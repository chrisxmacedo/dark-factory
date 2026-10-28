#!/usr/bin/env python3
"""Pull delivery facts from GitHub, Jira, and Linear.

This is a script, not an agent. It writes a normalised JSON file and does not
interpret risks or decide anything. Credentials come from the environment
(or config/ara.env for non-secret settings). Tokens are never written to the
output or to logs.

At least one source must be configured. Sources that are not configured are
recorded as skipped. A configured source that fails is recorded as an error
and does not fail the whole pull unless every configured source failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
for ancestor in Path(__file__).resolve().parents:
    harness = ancestor / "harness" / "scripts"
    if harness.is_dir():
        sys.path.insert(0, str(harness))
        break

from office_env import load_config  # noqa: E402
from paths import office_root  # noqa: E402


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def within(moment: datetime | None, start: datetime, end: datetime) -> bool:
    return moment is not None and start <= moment <= end


def redact(text: str) -> str:
    import re

    return re.sub(r"(Bearer\s+)\S+", r"\1[redacted]", text)[:500]


class Transport:
    def __call__(self, url: str, headers: dict[str, str], method: str = "GET", body: bytes | None = None) -> dict:
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} for {urllib.parse.urlparse(url).path}: {redact(detail)}") from exc
        return json.loads(payload) if payload else {}


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "technical-chief-of-staff",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_github(config: dict[str, str], transport: Transport, start: datetime, end: datetime) -> dict:
    token = config.get("GITHUB_TOKEN", "")
    repos = [item.strip() for item in config.get("GITHUB_REPOS", "").split(",") if item.strip()]
    if not token or not repos:
        return {"status": "skipped", "reason": "Set GITHUB_TOKEN and GITHUB_REPOS (comma-separated owner/name)."}
    headers = github_headers(token)
    pulls = []
    deployments = []
    runs = []
    truncated = False
    for repo in repos:
        pull_payload = transport(
            f"https://api.github.com/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=50",
            headers,
        )
        if isinstance(pull_payload, list) and len(pull_payload) >= 50:
            truncated = True
        for pull in pull_payload if isinstance(pull_payload, list) else []:
            merged = parse_dt(pull.get("merged_at"))
            if not within(merged, start, end):
                continue
            first_commit = None
            source = None
            try:
                commits = transport(pull["commits_url"], headers)
                if isinstance(commits, list) and commits:
                    first_commit = parse_dt(
                        commits[0].get("commit", {}).get("author", {}).get("date")
                        or commits[0].get("commit", {}).get("committer", {}).get("date")
                    )
                    source = "first_commit"
            except RuntimeError:
                first_commit = None
            if first_commit is None:
                first_commit = parse_dt(pull.get("created_at"))
                source = "pull_request_created"
            pulls.append(
                {
                    "repo": repo,
                    "number": pull.get("number"),
                    "title": pull.get("title") or "",
                    "created_at": pull.get("created_at"),
                    "merged_at": pull.get("merged_at"),
                    "first_commit_at": iso(first_commit),
                    "first_commit_source": source,
                }
            )
        deployment_payload = transport(
            f"https://api.github.com/repos/{repo}/deployments?per_page=30",
            headers,
        )
        for deployment in deployment_payload if isinstance(deployment_payload, list) else []:
            created = parse_dt(deployment.get("created_at"))
            if not within(created, start, end):
                continue
            statuses = transport(deployment["statuses_url"], headers)
            state = None
            if isinstance(statuses, list) and statuses:
                state = statuses[0].get("state")
            deployments.append(
                {
                    "repo": repo,
                    "environment": deployment.get("environment") or "",
                    "created_at": deployment.get("created_at"),
                    "status": state or "unknown",
                    "sha": deployment.get("sha") or "",
                }
            )
        run_payload = transport(
            f"https://api.github.com/repos/{repo}/actions/runs?per_page=30",
            headers,
        )
        for run in run_payload.get("workflow_runs", []) if isinstance(run_payload, dict) else []:
            created = parse_dt(run.get("created_at"))
            if not within(created, start, end):
                continue
            runs.append(
                {
                    "repo": repo,
                    "name": run.get("name") or "",
                    "conclusion": run.get("conclusion") or "",
                    "created_at": run.get("created_at"),
                    "head_branch": run.get("head_branch") or "",
                    "html_url": run.get("html_url") or "",
                }
            )
    return {
        "status": "ok",
        "truncated": truncated,
        "pull_requests": pulls,
        "deployments": deployments,
        "workflow_runs": runs,
    }


def fetch_jira(config: dict[str, str], transport: Transport, start: datetime) -> dict:
    site = config.get("JIRA_SITE", "").replace("https://", "").replace("http://", "").strip("/")
    email = config.get("JIRA_EMAIL", "")
    token = config.get("JIRA_API_TOKEN", "")
    projects = [item.strip() for item in config.get("JIRA_PROJECTS", "").split(",") if item.strip()]
    if not (site and email and token and projects):
        return {
            "status": "skipped",
            "reason": "Set JIRA_SITE (hostname only), JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECTS.",
        }
    import base64

    basic = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {"Authorization": f"Basic {basic}", "Accept": "application/json", "Content-Type": "application/json"}
    project_list = ", ".join(projects)
    jql = f'project in ({project_list}) AND updated >= "{start.date().isoformat()}" ORDER BY updated DESC'
    body = json.dumps(
        {
            "jql": jql,
            "maxResults": 50,
            "fields": ["summary", "status", "priority", "created", "resolutiondate", "statuscategorychangedate", "issuetype"],
            "expand": "changelog",
        }
    ).encode()
    payload = transport(
        f"https://{site}/rest/api/3/search/jql",
        headers,
        method="POST",
        body=body,
    )
    issues = []
    for issue in payload.get("issues", []):
        issues.append(normalise_jira_issue(issue))
    return {
        "status": "ok",
        "truncated": payload.get("isLast") is False or len(issues) >= 50,
        "issues": issues,
    }


def normalise_jira_issue(issue: dict) -> dict:
    fields = issue.get("fields") or {}
    started, source = jira_started(issue)
    status = (fields.get("status") or {}).get("name") or ""
    return {
        "key": issue.get("key") or "",
        "source": "jira",
        "title": fields.get("summary") or "",
        "status": status,
        "priority": (fields.get("priority") or {}).get("name") or "",
        "issue_type": (fields.get("issuetype") or {}).get("name") or "",
        "created_at": fields.get("created"),
        "started_at": started,
        "started_at_source": source,
        "completed_at": fields.get("resolutiondate"),
        "blocked_by": [],
    }


def jira_started(issue: dict) -> tuple[str | None, str]:
    histories = (issue.get("changelog") or {}).get("histories") or []
    candidates = []
    for history in histories:
        for item in history.get("items") or []:
            if item.get("field") != "status":
                continue
            name = (item.get("toString") or "").lower()
            if any(token in name for token in ("progress", "development", "review", "done", "closed")):
                candidates.append(history.get("created"))
    if candidates:
        candidates.sort()
        return candidates[0], "changelog"
    changed = (issue.get("fields") or {}).get("statuscategorychangedate")
    if changed:
        return changed, "statuscategorychangedate"
    return None, "missing"


def fetch_linear(config: dict[str, str], transport: Transport, start: datetime) -> dict:
    token = config.get("LINEAR_API_KEY", "")
    if not token:
        return {"status": "skipped", "reason": "Set LINEAR_API_KEY to read Linear."}
    teams = [item.strip() for item in config.get("LINEAR_TEAM_IDS", "").split(",") if item.strip()]
    headers = {"Authorization": token if token.startswith("lin_") else f"Bearer {token}", "Content-Type": "application/json"}
    team_filter = ""
    if teams:
        quoted = ", ".join(f'"{team}"' for team in teams)
        team_filter = f", team: {{ id: {{ in: [{quoted}] }} }}"
    query = """
    query OfficeIssues($since: DateTimeOrDuration!) {
      issues(first: 50, filter: { updatedAt: { gte: $since } %s }) {
        nodes {
          identifier title createdAt startedAt completedAt updatedAt priorityLabel url
          state { name type }
        }
      }
    }
    """ % team_filter
    payload = transport(
        "https://api.linear.app/graphql",
        headers,
        method="POST",
        body=json.dumps({"query": query, "variables": {"since": iso(start)}}).encode(),
    )
    if payload.get("errors"):
        message = "; ".join(error.get("message", "Linear error") for error in payload["errors"])
        raise RuntimeError(message)
    issues = []
    for node in payload.get("data", {}).get("issues", {}).get("nodes", []):
        state = node.get("state") or {}
        issues.append(
            {
                "key": node.get("identifier") or "",
                "source": "linear",
                "title": node.get("title") or "",
                "status": state.get("name") or "",
                "priority": node.get("priorityLabel") or "",
                "issue_type": "",
                "created_at": node.get("createdAt"),
                "started_at": node.get("startedAt"),
                "started_at_source": "linear" if node.get("startedAt") else "missing",
                "completed_at": node.get("completedAt"),
                "url": node.get("url") or "",
                "blocked_by": [],
            }
        )
    return {"status": "ok", "truncated": len(issues) >= 50, "issues": issues}


def empty_document(start: datetime, end: datetime) -> dict:
    return {
        "generated_at": iso(utcnow()),
        "window": {"start": iso(start), "end": iso(end)},
        "sources": {},
        "pull_requests": [],
        "deployments": [],
        "workflow_runs": [],
        "incidents": [],
        "issues": [],
        "notes": [
            "Facts only. Risks, decisions, and narrative belong to the agent that reads this file.",
            "Counts are capped at 50 items per source. truncated=true means the window is incomplete.",
        ],
    }


def assemble(parts: dict[str, dict], start: datetime, end: datetime) -> dict:
    document = empty_document(start, end)
    for name, part in parts.items():
        document["sources"][name] = {"status": part.get("status"), "reason": part.get("reason", ""), "truncated": part.get("truncated", False)}
        document["pull_requests"].extend(part.get("pull_requests") or [])
        document["deployments"].extend(part.get("deployments") or [])
        document["workflow_runs"].extend(part.get("workflow_runs") or [])
        document["incidents"].extend(part.get("incidents") or [])
        document["issues"].extend(part.get("issues") or [])
    return document


def load_fixture(directory: Path, start: datetime, end: datetime) -> dict:
    """A fixture is either a normalised delivery.json or raw source files."""
    normalised = directory / "delivery.json"
    if normalised.is_file():
        document = json.loads(normalised.read_text(encoding="utf-8"))
        document["window"] = {"start": iso(start), "end": iso(end)}
        document["generated_at"] = iso(utcnow())
        return document
    parts = {}
    for name in ("github", "jira", "linear"):
        path = directory / f"{name}.json"
        if path.is_file():
            parts[name] = json.loads(path.read_text(encoding="utf-8"))
    if not parts:
        raise SystemExit(f"No fixture JSON in {directory}")
    return assemble(parts, start, end)


def pull_live(config: dict[str, str], transport: Transport, start: datetime, end: datetime) -> dict:
    parts: dict[str, dict] = {}
    errors = []
    for name, fetcher in (
        ("github", lambda: fetch_github(config, transport, start, end)),
        ("jira", lambda: fetch_jira(config, transport, start)),
        ("linear", lambda: fetch_linear(config, transport, start)),
    ):
        try:
            parts[name] = fetcher()
        except Exception as exc:  # noqa: BLE001 — one source must not hide the others
            message = redact(str(exc))
            parts[name] = {"status": "error", "reason": message}
            errors.append(name)
    configured = [name for name, part in parts.items() if part.get("status") != "skipped"]
    if not configured:
        raise SystemExit(
            "No delivery source is configured. Set GitHub (GITHUB_TOKEN, GITHUB_REPOS), "
            "Jira (JIRA_SITE, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECTS), or Linear (LINEAR_API_KEY)."
        )
    if configured and all(parts[name].get("status") == "error" for name in configured):
        document = assemble(parts, start, end)
        # Still write nothing here; the caller writes then exits.
        document["fatal"] = True
        return document
    return assemble(parts, start, end)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull GitHub, Jira, and Linear delivery facts")
    parser.add_argument("--since", help="ISO date or datetime. Default: 7 days ago")
    parser.add_argument("--until", help="ISO date or datetime. Default: now")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--fixture", type=Path, help="Read local JSON instead of the network")
    parser.add_argument("--output", type=Path, help="Default: outputs/raw/delivery.json")
    args = parser.parse_args()
    root = office_root()
    end = parse_dt(args.until) if args.until else utcnow()
    if end is None:
        end = utcnow()
    start = parse_dt(args.since) if args.since else end - timedelta(days=args.days)
    if start is None:
        start = end - timedelta(days=args.days)
    if args.fixture:
        document = load_fixture(args.fixture, start, end)
    else:
        document = pull_live(load_config(root), Transport(), start, end)
    destination = args.output or (root / "outputs" / "raw" / "delivery.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")
    if document.get("fatal"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
