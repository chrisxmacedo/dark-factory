#!/usr/bin/env python3
"""
Environment Dashboard — lightweight server for managing Docker environments.
Serves the dashboard HTML and exposes API endpoints that shell out to envctl.

Usage:
    ./dashboard.py              # Start on port 4400
    ./dashboard.py --port 4500  # Custom port

API:
    GET  /api/status            — status of all environments
    POST /api/up/{env}          — start environment (ci|rc|prod)
    POST /api/down/{env}        — stop environment (ci|rc|prod)
    POST /api/rebuild/{env}     — rebuild environment (ci|rc|prod)

Replace {PLACEHOLDERS} with your project-specific values before use.
"""

import json
import os
import re
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import urlparse

INFRA_DIR = Path(__file__).parent.resolve()
ENVCTL = INFRA_DIR / "envctl"
PORT = 4400

# ── Project-specific config — replace these ─────────────────────────────────

PROJECT_SLUG = "{PROJECT_SLUG}"
WEB_PORT_CI = "{WEB_PORT}"
JIRA_URL = "https://{JIRA_SITE}"

ENVIRONMENTS = {
    "ci": {
        "label": "CI",
        "branch": "ci",
        "web_port": WEB_PORT_CI,
        "health": f"http://localhost:{WEB_PORT_CI}/healthz",
        "description": "Latest merged feature code",
    },
    "rc": {
        "label": "RC",
        "branch": "release-rc-*",
        "web_port": WEB_PORT_CI + 100,
        "health": f"http://localhost:{WEB_PORT_CI + 100}/healthz",
        "description": "Current release candidate with fixture data",
    },
    "prod": {
        "label": "Prod-parity",
        "branch": "main",
        "web_port": WEB_PORT_CI + 200,
        "health": f"http://localhost:{WEB_PORT_CI + 200}/healthz",
        "grafana": "http://localhost:4000",
        "description": "Production-like with OTel/Grafana stack",
    },
}


def run_envctl(command: str, env: str) -> dict:
    try:
        result = subprocess.run(
            [str(ENVCTL), command, env],
            capture_output=True, text=True, timeout=300, cwd=str(INFRA_DIR),
        )
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}


def get_env_status(env: str) -> dict:
    info = ENVIRONMENTS[env].copy()
    info["id"] = env
    project_name = f"{PROJECT_SLUG}-{env}"
    try:
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "ps", "--format", "json"],
            capture_output=True, text=True, timeout=10, cwd=str(INFRA_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            containers = []
            raw = result.stdout.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    containers = parsed
                else:
                    containers = [parsed]
            except json.JSONDecodeError:
                for line in raw.split("\n"):
                    try: containers.append(json.loads(line))
                    except json.JSONDecodeError: pass
            running = [c for c in containers if c.get("State") == "running"]
            exited_ok = [c for c in containers if c.get("State") == "exited" and c.get("ExitCode", 1) == 0]
            active = len(running) + len(exited_ok)
            info["running"] = len(running) > 0
            info["containers"] = len(running)
            info["total_containers"] = len(containers)
            info["all_healthy"] = active == len(containers) and len(running) > 0
            # Per-service status for the frontend
            svc_status = {}
            for c in containers:
                svc_name = c.get("Service", "")
                svc_status[svc_name] = {
                    "state": c.get("State", "unknown"),
                    "health": c.get("Health", ""),
                    "exit_code": c.get("ExitCode", -1),
                }
            info["services"] = svc_status
        else:
            info.update(running=False, containers=0, total_containers=0)
    except Exception:
        info.update(running=False, containers=0, total_containers=0)
    return info


TEST_STATUS_DIR = Path("/tmp/envctl-tests")


def get_test_status(env: str) -> dict | None:
    status_file = TEST_STATUS_DIR / f"{env}.json"
    if not status_file.exists():
        return None
    try:
        with open(status_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_all_status() -> list:
    envs = []
    for env in ENVIRONMENTS:
        info = get_env_status(env)
        info["test_status"] = get_test_status(env)
        info["jira_url"] = JIRA_URL
        envs.append(info)
    return envs


def get_active_commits() -> dict:
    """Get the git commit hash each RUNNING environment was built from.
    Only reports commits for environments that have running containers.
    Reads git.commit label from the envctl-built images ({service}:{env})."""
    project_root = INFRA_DIR.parent
    result = {}

    # First, check which environments are actually running
    running_envs = set()
    for env in ENVIRONMENTS:
        project_name = f"{PROJECT_SLUG}-{env}"
        try:
            ps = subprocess.run(
                ["docker", "compose", "-p", project_name, "ps", "--status", "running", "-q"],
                capture_output=True, text=True, timeout=5, cwd=str(INFRA_DIR),
            )
            if ps.returncode == 0 and ps.stdout.strip():
                running_envs.add(env)
        except Exception:
            continue

    if not running_envs:
        return {}

    # Only check images for running environments
    service_repos = sorted(
        [e for e in project_root.iterdir() if e.is_dir() and (e / ".git").exists()],
        key=lambda p: p.name,
    )

    for repo in service_repos:
        name = repo.name
        for env in running_envs:
            image_tag = f"{name}:{env}"
            try:
                inspect = subprocess.run(
                    ["docker", "inspect", "--format",
                     '{{index .Config.Labels "git.commit"}}', image_tag],
                    capture_output=True, text=True, timeout=3,
                )
                commit = inspect.stdout.strip()
                if commit and commit != "<no value>":
                    if name not in result:
                        result[name] = {}
                    result[name][env] = commit[:7]
            except Exception:
                continue
    return result


def get_commit_detail(repo_name: str, commit_hash: str) -> dict | None:
    """Get detailed info for a single commit: files changed, lines added/removed."""
    project_root = INFRA_DIR.parent
    repo = project_root / repo_name
    if not repo.is_dir() or not (repo / ".git").exists():
        return None

    result = subprocess.run(
        ["git", "show", commit_hash, "--stat", "--format=%H|%h|%s|%aI|%an|%ae"],
        capture_output=True, text=True, timeout=5, cwd=str(repo),
    )
    if result.returncode != 0:
        return None

    lines = result.stdout.strip().split("\n")
    if not lines:
        return None

    # First line is the format string
    header = lines[0].split("|", 5)
    if len(header) < 6:
        return None

    full_hash, short_hash, subject, date, author, email = header

    # Parse stat lines (file changes)
    files = []
    total_insertions = 0
    total_deletions = 0
    for stat_line in lines[1:]:
        stat_line = stat_line.strip()
        if not stat_line or stat_line.startswith("Merge:"):
            continue
        # Summary line: "3 files changed, 10 insertions(+), 2 deletions(-)"
        if "file" in stat_line and "changed" in stat_line:
            import re
            ins = re.search(r"(\d+) insertion", stat_line)
            dels = re.search(r"(\d+) deletion", stat_line)
            if ins:
                total_insertions = int(ins.group(1))
            if dels:
                total_deletions = int(dels.group(1))
            continue
        # File line: " src/main.py | 15 +++---"
        if "|" in stat_line:
            parts = stat_line.split("|")
            fname = parts[0].strip()
            if fname:
                files.append(fname)

    return {
        "hash": short_hash,
        "full_hash": full_hash,
        "subject": subject,
        "date": date,
        "author": author.strip(),
        "email": email.strip(),
        "files": files,
        "files_changed": len(files),
        "insertions": total_insertions,
        "deletions": total_deletions,
    }


_tracks_cache = {"data": None, "time": 0}


def get_commit_tracks() -> dict:
    """Get per-repo commit graphs by walking the tree from main and ci,
    using git notes to identify feature branch boundaries.
    Results are cached for 15 seconds to avoid repeated git operations."""
    import time as _time
    now = _time.time()
    if _tracks_cache["data"] and (now - _tracks_cache["time"]) < 15:
        return _tracks_cache["data"]

    project_root = INFRA_DIR.parent
    repos = {}
    latest_repo = None
    latest_date = ""

    service_repos = sorted(
        [e for e in project_root.iterdir() if e.is_dir() and (e / ".git").exists()],
        key=lambda p: p.name,
    )

    for repo in service_repos:
        try:
            repo_data = _build_repo_graph(repo)
            if repo_data and repo_data["commits"]:
                repo_latest = repo_data["commits"][-1]["date"]
                if repo_latest > latest_date:
                    latest_date = repo_latest
                    latest_repo = repo.name
                repos[repo.name] = repo_data
        except Exception:
            continue

    result = {"repos": repos, "latest_repo": latest_repo}
    _tracks_cache["data"] = result
    _tracks_cache["time"] = _time.time()
    return result


def _first_parent_log(repo: Path, branch: str, limit: int = 30) -> list[dict]:
    """Get the first-parent log of a branch with parent hashes."""
    result = subprocess.run(
        ["git", "log", branch, "--first-parent", "--date=iso-strict",
         "--format=%H|%h|%s|%aI|%P|%an", f"-{limit}"],
        capture_output=True, text=True, timeout=5, cwd=str(repo),
    )
    if result.returncode != 0:
        return []
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 5)
        if len(parts) < 6:
            continue
        full_hash, short_hash, subject, date, parents_str, author = parts
        parents = parents_str.strip().split() if parents_str.strip() else []
        commits.append({
            "full_hash": full_hash,
            "hash": short_hash,
            "subject": subject[:60],
            "date": date,
            "author": author.strip(),
            "parents": parents,
            "is_merge": len(parents) >= 2,
        })
    return commits


def _walk_branch(repo: Path, tip_hash: str, stop_hashes: set, limit: int = 15) -> list[dict]:
    """Walk a branch from tip backwards, stopping at any commit in stop_hashes.
    Returns the commits that are unique to this branch."""
    result = subprocess.run(
        ["git", "log", tip_hash, "--date=iso-strict",
         "--format=%H|%h|%s|%aI|%an", f"-{limit}"],
        capture_output=True, text=True, timeout=5, cwd=str(repo),
    )
    if result.returncode != 0:
        return []
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        full_hash, short_hash, subject, date, author = parts
        if full_hash in stop_hashes:
            break  # reached the mainline — stop
        commits.append({
            "full_hash": full_hash,
            "hash": short_hash,
            "subject": subject[:60],
            "date": date,
            "author": author.strip(),
            "is_merge": False,
        })
    return commits


def _get_notes(repo: Path) -> dict[str, str]:
    """Get all git notes as {full_hash: note_text}."""
    result = subprocess.run(
        ["git", "notes", "list"],
        capture_output=True, text=True, timeout=3, cwd=str(repo),
    )
    if result.returncode != 0:
        return {}
    notes = {}
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) == 2:
            note_blob, commit_hash = parts
            note_result = subprocess.run(
                ["git", "notes", "show", commit_hash],
                capture_output=True, text=True, timeout=2, cwd=str(repo),
            )
            if note_result.returncode == 0:
                notes[commit_hash] = note_result.stdout.strip()
    return notes


def _build_repo_graph(repo: Path) -> dict | None:
    """Build commit graph by walking the tree from notes.

    The two backbones (ci and main first-parent logs) provide the commits.
    Notes provide ALL cross-track relationships:
      - branch-off: ci from main          → main↗ci
      - branch-off: feature/X from ci     → ci↗feature
      - merge: feature/X into ci          → feature↘ci (+ walk feature commits)
      - branch-off: release-rc-N from ci  → ci↘rc (no RC commits unless walked)
      - merge: release-rc-N into main     → rc↘main (link from ci to main via rc)
      - merge: main back-merge into ci    → main↗ci
    """
    all_commits = []
    links = []
    rc_branchoffs = {}  # rc_name → {"ci_hash": ..., "rc_commits": [...]}

    # Step 1: CI backbone — this is the primary timeline
    ci_log = _first_parent_log(repo, "ci", limit=60)
    ci_hashes = {c["full_hash"] for c in ci_log}
    ci_by_hash = {c["full_hash"]: c for c in ci_log}
    for c in ci_log:
        c["track"] = "ci"
        c["branch"] = "ci"
        all_commits.append(c)

    # Step 2: Main backbone — only commits NOT already on ci
    main_log = _first_parent_log(repo, "main", limit=60)
    main_hashes = {c["full_hash"] for c in main_log}
    main_by_hash = {c["full_hash"]: c for c in main_log}
    for c in main_log:
        if c["full_hash"] not in ci_hashes:
            c["track"] = "main"
            c["branch"] = "main"
            all_commits.append(c)

    # The set of all backbone hashes — feature/rc walks stop here
    backbone = main_hashes | ci_hashes

    # Helper to find a commit in all_commits by short hash
    def find_commit(short_hash, track=None):
        for c in all_commits:
            if c.get("hash") == short_hash:
                if track is None or c.get("track") == track:
                    return c
        return None

    # Step 3: Process ALL notes in two passes.
    # Pass 1: branch-offs (creates RC virtual nodes and stores branchoff info)
    # Pass 2: merges (uses branchoff info to create links)
    notes = _get_notes(repo)

    # Collect all note lines with their commit hashes
    all_note_lines = []
    for commit_hash, note_text in notes.items():
        for line in note_text.split("\n"):
            line = line.strip()
            if line:
                all_note_lines.append((commit_hash, line))

    # Sort: branch-offs first, then merges
    def note_sort_key(item):
        return 0 if item[1].startswith("branch-off:") else 1
    all_note_lines.sort(key=note_sort_key)

    for commit_hash, line in all_note_lines:
        short = commit_hash[:7]
        parts = line.split()
        name = parts[1] if len(parts) > 1 else ""

        # ── branch-off: ci from main ──────────────────────────────
        if line.startswith("branch-off: ci from main"):
            pass  # Visual: ci starts here

        # ── branch-off: feature/X from ci ─────────────────────────
        elif line.startswith("branch-off:") and "from ci" in line and "release-rc" not in line and "ci from main" not in line:
            # Links built after feature commits are collected from merge notes
            pass

        # ── merge: feature/X into ci ──────────────────────────────
        elif line.startswith("merge:") and "into ci" in line and "release-rc" not in line and "back-merge" not in line.lower():
            ci_commit = ci_by_hash.get(commit_hash)
            if not ci_commit or not ci_commit.get("is_merge"):
                continue
            parents = ci_commit.get("parents", [])
            if len(parents) < 2:
                continue

            feature_tip = parents[1]
            feature_commits = _walk_branch(repo, feature_tip, backbone, limit=15)
            for fc in feature_commits:
                fc["track"] = "feature"
                fc["branch"] = name
                all_commits.append(fc)

            if feature_commits:
                links.append({
                    "from_hash": feature_commits[0]["hash"],
                    "from_track": "feature",
                    "to_hash": short,
                    "to_track": "ci",
                })

        # ── branch-off: release-rc-N from ci ──────────────────────
        elif line.startswith("branch-off:") and "release-rc" in line and "from ci" in line:
            rc_name = name

            rc_commits = _walk_branch(repo, rc_name, backbone, limit=10)
            for rc in rc_commits:
                rc["track"] = "rc"
                rc["branch"] = rc_name
                all_commits.append(rc)

            if not rc_commits:
                ci_commit = find_commit(short, "ci")
                if ci_commit:
                    virtual_hash = f"rc-{rc_name.replace('release-rc-', '')}"
                    virtual = {
                        "hash": virtual_hash,
                        "subject": f"Cut {rc_name}",
                        "date": ci_commit["date"],
                        "track": "rc",
                        "branch": rc_name,
                        "is_merge": False,
                    }
                    all_commits.append(virtual)
                    rc_commits = [virtual]

            if rc_commits:
                links.append({
                    "from_hash": short,
                    "from_track": "ci",
                    "to_hash": rc_commits[-1]["hash"],
                    "to_track": "rc",
                })

            rc_branchoffs[rc_name] = {
                "ci_hash": short,
                "rc_commits": rc_commits,
            }

        # ── merge: release-rc-N into main ─────────────────────────
        elif line.startswith("merge:") and "release-rc" in line and "into main" in line:
            rc_name = name
            main_commit = find_commit(short, "main")
            if not main_commit:
                continue

            branchoff = rc_branchoffs.get(rc_name)
            if branchoff and branchoff["rc_commits"]:
                links.append({
                    "from_hash": branchoff["rc_commits"][0]["hash"],
                    "from_track": "rc",
                    "to_hash": short,
                    "to_track": "main",
                })
            elif branchoff:
                links.append({
                    "from_hash": branchoff["ci_hash"],
                    "from_track": "ci",
                    "to_hash": short,
                    "to_track": "main",
                })

        # ── merge: main back-merge into ci ────────────────────────
        elif line.startswith("merge:") and "back-merge" in line.lower() and "into ci" in line.lower():
            ci_commit = ci_by_hash.get(commit_hash)
            if not ci_commit or not ci_commit.get("is_merge"):
                continue
            parents = ci_commit.get("parents", [])
            if len(parents) < 2:
                continue

            main_parent = parents[1][:7]
            if find_commit(main_parent, "main"):
                links.append({
                    "from_hash": main_parent,
                    "from_track": "main",
                    "to_hash": short,
                    "to_track": "ci",
                })

    # Second pass: build branch-off links for features
    # (feature commits were added during merge processing above)
    for commit_hash, note_text in notes.items():
        short = commit_hash[:7]
        for line in note_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("branch-off:") and "from ci" in line and "release-rc" not in line and "ci from main" not in line:
                parts = line.split()
                branch_name = parts[1] if len(parts) > 1 else ""

                feat_for_branch = [c for c in all_commits
                                   if c.get("track") == "feature" and c.get("branch") == branch_name]
                if feat_for_branch and find_commit(short, "ci"):
                    oldest_feat = sorted(feat_for_branch, key=lambda c: c["date"])[0]  # earliest by date
                    links.append({
                        "from_hash": short,
                        "from_track": "ci",
                        "to_hash": oldest_feat["hash"],
                        "to_track": "feature",
                    })

    # Sort chronologically (oldest first)
    all_commits = sorted(all_commits, key=lambda c: c["date"])

    # Clean up internal fields
    for c in all_commits:
        c.pop("full_hash", None)
        c.pop("parents", None)

    return {"commits": all_commits, "links": links}


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PROJECT_NAME} — Environment Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --surface2: #1c2128;
    --border: #30363d; --text: #e6edf3; --text-dim: #7d8590;
    --green: #3fb950; --green-bg: #0d2818; --green-border: #1a4024;
    --red: #f85149; --red-bg: #2d1214; --red-border: #4a1e1f;
    --yellow: #d29922; --yellow-bg: #2e1e00; --yellow-border: #4b3a12;
    --blue: #58a6ff; --blue-bg: #0c2d6b; --blue-border: #1a4b8f;
    --purple: #bc8cff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.5; }
  .header { padding: 24px 32px; border-bottom: 1px solid var(--border);
            display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 20px; font-weight: 600; }
  .header h1 span { color: var(--blue); }
  .header-meta { font-size: 12px; color: var(--text-dim); font-family: 'SF Mono', monospace; }
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
          padding: 24px 32px; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: 12px; overflow: hidden; }
  .card-header { padding: 16px 20px; display: flex; align-items: center;
                 justify-content: space-between; border-bottom: 1px solid var(--border); }
  .card-title { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .card-body { padding: 16px 20px; }
  .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .status-dot.running { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .status-dot.stopped { background: var(--red); }
  .status-dot.starting { background: var(--yellow); animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
  .badge { font-size: 11px; font-family: 'SF Mono', monospace; padding: 2px 8px;
           border-radius: 4px; letter-spacing: 0.03em; }
  .badge-green { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
  .badge-red { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
  .badge-yellow { background: var(--yellow-bg); color: var(--yellow); border: 1px solid var(--yellow-border); }
  .badge-blue { background: var(--blue-bg); color: var(--blue); border: 1px solid var(--blue-border); }
  .info-row { display: flex; justify-content: space-between; padding: 8px 0;
              border-bottom: 1px solid var(--border); font-size: 13px; }
  .info-row:last-child { border-bottom: none; }
  .info-label { color: var(--text-dim); }
  .info-value { font-family: 'SF Mono', monospace; font-size: 12px; }
  .info-value a { color: var(--blue); text-decoration: none; }
  .info-value a:hover { text-decoration: underline; }
  .services { padding: 16px 20px; border-top: 1px solid var(--border); }
  .services-title { font-size: 12px; color: var(--text-dim); text-transform: uppercase;
                    letter-spacing: 0.06em; margin-bottom: 10px; font-family: 'SF Mono', monospace; }
  .svc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
  .svc { display: flex; align-items: center; gap: 6px; font-size: 12px;
         font-family: 'SF Mono', monospace; padding: 4px 8px; border-radius: 4px;
         background: var(--surface2); }
  .svc-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .svc-dot.healthy { background: var(--green); }
  .svc-dot.unhealthy { background: var(--red); }
  .svc-dot.starting { background: var(--yellow); animation: pulse 1.5s infinite; }
  .svc-dot.stopping { background: var(--yellow); animation: pulse 1.5s infinite; }
  .svc-dot.exited-ok { background: var(--text-dim); }
  .svc-dot.not-running { background: var(--text-dim); }
  .test-status { padding: 12px 20px; border-top: 1px solid var(--border); }
  .test-ticket { display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
                 font-size: 12px; }
  .test-ticket a { color: var(--blue); text-decoration: none; font-family: 'SF Mono', monospace;
                   font-weight: 600; }
  .test-ticket a:hover { text-decoration: underline; }
  .test-ticket .ticket-summary { color: var(--text-dim); }
  .test-bar { display: flex; align-items: center; gap: 10px; font-size: 12px;
              font-family: 'SF Mono', monospace; padding: 8px 12px;
              border-radius: 6px; background: var(--surface2); }
  .test-bar .spinner { width: 12px; height: 12px; border: 2px solid var(--border);
                       border-top-color: var(--blue); border-radius: 50%;
                       animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .test-bar.passed { border-left: 3px solid var(--green); }
  .test-bar.failed { border-left: 3px solid var(--red); }
  .test-bar.running, .test-bar.booting, .test-bar.installing { border-left: 3px solid var(--yellow); }
  .test-bar.teardown { border-left: 3px solid var(--blue); }
  .test-time { color: var(--text-dim); margin-left: auto; }
  .actions { padding: 12px 20px; border-top: 1px solid var(--border);
             display: flex; gap: 8px; }
  .btn { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
         background: var(--surface2); color: var(--text); cursor: pointer;
         font-size: 12px; font-family: 'SF Mono', monospace; transition: all 0.15s; }
  .btn:hover { border-color: var(--blue); color: var(--blue); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-danger:hover { border-color: var(--red); color: var(--red); }
  .btn-success { border-color: var(--green-border); color: var(--green); }
  .btn-success:hover { background: var(--green-bg); }
  .toast { position: fixed; bottom: 20px; right: 20px; padding: 12px 20px;
           background: var(--surface); border: 1px solid var(--border);
           border-radius: 8px; font-size: 13px; display: none; z-index: 100;
           box-shadow: 0 4px 12px rgba(0,0,0,0.4); }
  .section-title { padding: 24px 32px 8px; font-size: 14px; color: var(--text-dim);
                   text-transform: uppercase; letter-spacing: 0.06em;
                   font-family: 'SF Mono', monospace; }
  .tracks-section { padding: 20px 32px; }
  .tracks-header { display: flex; align-items: center; justify-content: space-between;
                   margin-bottom: 12px; }
  .tracks-title { font-size: 12px; color: var(--text-dim); text-transform: uppercase;
                  letter-spacing: 0.06em; font-family: 'SF Mono', monospace; }
  .carousel-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
  .carousel-tab { font-size: 11px; font-family: 'SF Mono', monospace; padding: 4px 10px;
                  border-radius: 4px; background: var(--surface2); color: var(--text-dim);
                  border: 1px solid var(--border); cursor: pointer; transition: all 0.15s; }
  .carousel-tab:hover { border-color: var(--blue); color: var(--text); }
  .carousel-tab.active { background: var(--blue-bg); color: var(--blue);
                         border-color: var(--blue-border); }
  .carousel-tab.latest { box-shadow: 0 0 6px var(--green); border-color: var(--green-border); }
  .tracks-container { background: var(--surface); border: 1px solid var(--border);
                      border-radius: 12px; padding: 20px; display: flex; gap: 16px;
                      overflow: hidden; }
  .tracks-labels { display: flex; flex-direction: column; justify-content: space-around;
                   flex-shrink: 0; height: 160px; }
  .track-label { font-size: 11px; font-family: 'SF Mono', monospace; color: var(--text-dim);
                 text-align: right; width: 60px; line-height: 1; }
  .tracks-canvas-wrap { flex: 1; overflow-x: auto; overflow-y: hidden; min-width: 0; }
  .tracks-canvas-wrap canvas { display: block; }
  .tracks-empty { font-size: 12px; color: var(--text-dim); font-family: 'SF Mono', monospace;
                  text-align: center; padding: 40px; }
</style>
</head>
<body>

<div class="header">
  <h1>{PROJECT_NAME} &mdash; Environments</h1>
  <div style="display:flex;align-items:center;gap:12px">
    <div class="header-meta" id="last-updated">Loading...</div>
    <button class="btn" id="test-toggle" onclick="toggleTestData()" style="font-size:10px;padding:3px 8px">Test Data</button>
  </div>
</div>

<div class="tracks-section">
  <div class="tracks-header">
    <div class="tracks-title">Pipeline Activity</div>
    <div class="carousel-tabs" id="carousel-tabs"></div>
  </div>
  <div class="tracks-container" id="tracks-container">
    <div class="tracks-labels">
      <div class="track-label">feature</div>
      <div class="track-label">ci</div>
      <div class="track-label">rc</div>
      <div class="track-label">main</div>
    </div>
    <div class="tracks-canvas-wrap">
      <canvas id="tracks-canvas" height="160"></canvas>
    </div>
  </div>
</div>

<div class="grid" id="env-grid"></div>

<div id="toast" class="toast"></div>
<div id="commit-tooltip" style="display:none;position:fixed;z-index:200;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--text);max-width:400px;box-shadow:0 4px 16px rgba(0,0,0,0.5);pointer-events:none;line-height:1.5"></div>

<script>
const SERVICES = [
  // Replace with your project's services and ports
  // {name: '{service-1}', port: {PORT_1}},
  // {name: '{service-2}', port: {PORT_2}},
];

function statusClass(env) {
  if (env.all_healthy) return 'running';
  if (env.containers > 0) return 'starting';
  return 'stopped';
}

function renderTestStatus(env) {
  const t = env.test_status;
  if (!t) return '';
  const s = statusClass(env);
  const testActive = ['booting','installing','running','teardown'].includes(t.status);
  if (s === 'stopped' && !testActive) return '';
  const isActive = ['booting','installing','running','teardown'].includes(t.status);
  const icon = t.status === 'passed' ? '&#10003;' :
               t.status === 'failed' ? '&#10007;' :
               '';
  const spinner = isActive ? '<div class="spinner"></div>' : '';
  const ago = t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : '';

  let ticketHtml = '';
  if (t.ticket) {
    const jiraUrl = env.jira_url || '';
    const ticketUrl = jiraUrl ? `${jiraUrl}/browse/${t.ticket}` : '#';
    ticketHtml = `<div class="test-ticket">
      <a href="${ticketUrl}" target="_blank">${t.ticket}</a>
      <span class="ticket-summary">${t.summary || ''}</span>
    </div>`;
  }

  let testsHtml = '';
  if (t.tests && t.tests.length > 0) {
    const testRows = t.tests.map(test => {
      const dot = test.result === 'passed' ? 'up' :
                  test.result === 'failed' ? 'down' :
                  'skip';
      const icon2 = test.result === 'passed' ? '&#10003;' :
                    test.result === 'failed' ? '&#10007;' :
                    '&#8212;';
      const color = test.result === 'passed' ? 'var(--green)' :
                    test.result === 'failed' ? 'var(--red)' :
                    'var(--text-dim)';
      return `<div class="svc" style="font-size:11px"><span style="color:${color}">${icon2}</span> ${test.name}</div>`;
    }).join('');
    testsHtml = `<div class="svc-grid" style="margin-top:8px">${testRows}</div>`;
  }

  return `
    <div class="test-status">
      ${ticketHtml}
      <div class="test-bar ${t.status}">
        ${spinner}
        <span>${icon} <strong>${t.suite}</strong> &mdash; ${t.detail}</span>
        <span class="test-time">${ago}</span>
      </div>
      ${testsHtml}
    </div>`;
}

// Service status: not-running, starting, healthy, unhealthy, stopping
function svcStatus(env, svcName) {
  if (!env.services) return 'not-running';
  const s = env.services[svcName];
  if (!s) return 'not-running';
  if (s.state === 'running') {
    if (s.health === 'healthy') return 'healthy';
    if (s.health === 'starting') return 'starting';
    if (s.health === 'unhealthy') return 'unhealthy';
    // Running with no health check configured — treat as healthy
    return 'healthy';
  }
  if (s.state === 'created' || s.state === 'restarting') return 'starting';
  if (s.state === 'removing' || s.state === 'paused') return 'stopping';
  if (s.state === 'exited' && s.exit_code === 0) return 'exited-ok';
  if (s.state === 'exited') return 'not-running';
  return 'not-running';
}

function statusLabel(env) {
  const s = statusClass(env);
  if (s === 'running') return '<span class="badge badge-green">RUNNING</span>';
  if (s === 'starting') return '<span class="badge badge-yellow">STARTING</span>';
  return '<span class="badge badge-red">STOPPED</span>';
}

function renderCard(env) {
  const s = statusClass(env);
  const containers = env.total_containers > 0
    ? `${env.containers}/${env.total_containers} containers`
    : 'No containers';
  const healthUrl = env.health || '';
  const grafana = env.grafana ? `<div class="info-row"><span class="info-label">Grafana</span><span class="info-value"><a href="${env.grafana}" target="_blank">${env.grafana}</a></span></div>` : '';

  return `
    <div class="card" id="card-${env.id}">
      <div class="card-header">
        <div class="card-title">
          <span class="status-dot ${s}"></span>
          ${env.label}
        </div>
        ${statusLabel(env)}
      </div>
      <div class="card-body">
        <div class="info-row">
          <span class="info-label">Branch</span>
          <span class="info-value">${env.branch}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Containers</span>
          <span class="info-value">${containers}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Health</span>
          <span class="info-value"><a href="${healthUrl}" target="_blank">${healthUrl}</a></span>
        </div>
        ${grafana}
        <div class="info-row">
          <span class="info-label">Description</span>
          <span class="info-value" style="font-family:inherit;max-width:60%">${env.description}</span>
        </div>
      </div>
      <div class="services">
        <div class="services-title">Services</div>
        <div class="svc-grid">
          ${SERVICES.map(svc => {
            const st = svcStatus(env, svc.name);
            return `<div class="svc"><span class="svc-dot ${st}"></span>${svc.name}:${svc.port}</div>`;
          }).join('')}
        </div>
      </div>
      ${renderTestStatus(env)}
      <div class="actions">
        <button class="btn btn-success" onclick="envAction('up','${env.id}')" ${s==='running'?'disabled':''}>Start</button>
        <button class="btn btn-danger" onclick="envAction('down','${env.id}')" ${s==='stopped'?'disabled':''}>Stop</button>
        <button class="btn" onclick="envAction('rebuild','${env.id}')">Rebuild</button>
      </div>
    </div>
  `;
}

async function refresh() {
  try {
    const res = await fetch('/api/status');
    const envs = await res.json();
    document.getElementById('env-grid').innerHTML = envs.map(renderCard).join('');
    document.getElementById('last-updated').textContent =
      'Updated ' + new Date().toLocaleTimeString();
  } catch (e) {
    document.getElementById('last-updated').textContent = 'Error: ' + e.message;
  }
}

async function envAction(action, env) {
  const toast = document.getElementById('toast');
  toast.textContent = `${action} ${env}...`;
  toast.style.display = 'block';

  // Immediately update the card to show transitional state
  const card = document.getElementById('card-' + env);
  if (card) {
    const dot = card.querySelector('.status-dot');
    const badge = card.querySelector('.badge');
    if (action === 'down' && dot && badge) {
      dot.className = 'status-dot starting';  // yellow pulse
      badge.className = 'badge badge-yellow';
      badge.textContent = 'STOPPING';
    } else if (action === 'up' && dot && badge) {
      dot.className = 'status-dot starting';
      badge.className = 'badge badge-yellow';
      badge.textContent = 'STARTING';
    } else if (action === 'rebuild' && dot && badge) {
      dot.className = 'status-dot starting';
      badge.className = 'badge badge-yellow';
      badge.textContent = 'REBUILDING';
    }
    // Disable all action buttons during the operation
    card.querySelectorAll('.btn').forEach(b => b.disabled = true);
  }

  try {
    const res = await fetch(`/api/${action}/${env}`, {method: 'POST'});
    const data = await res.json();
    toast.textContent = data.success ? `${action} ${env}: done` : `${action} ${env}: ${data.stderr}`;
    setTimeout(() => { toast.style.display = 'none'; }, 4000);
    refresh();
  } catch (e) {
    toast.textContent = `Error: ${e.message}`;
    setTimeout(() => { toast.style.display = 'none'; }, 4000);
    refresh();
  }
}

// ── Pipeline Tracks (carousel + graph) ──────────────────────────────────

const TRACK_COLORS = { feature: '#58a6ff', ci: '#3fb950', rc: '#d29922', main: '#bc8cff' };
const TRACK_ORDER = ['feature', 'ci', 'rc', 'main'];
const TRACK_Y = {};
const TRACK_SPACING = 40;
const TRACK_TOP = 20;
TRACK_ORDER.forEach((t, i) => { TRACK_Y[t] = TRACK_TOP + i * TRACK_SPACING; });

// ── Test data: two tickets through the full pipeline ─────────────────
// FAKE-1: feature (3 commits) → merge ci → cut rc-1 → merge main → back-merge ci
// FAKE-2: feature (2 commits) → merge ci → cut rc-2 → merge main → back-merge ci
const TEST_DATA = {
  repos: {
    "test-service": {
      commits: [
        // Main backbone (oldest first)
        {hash:"m0", subject:"chore: initial commit",              date:"2026-04-01T10:00:00Z", track:"main", branch:"main", is_merge:false},
        // CI backbone
        {hash:"c0", subject:"chore: initialize ci branch",        date:"2026-04-01T10:01:00Z", track:"ci", branch:"ci", is_merge:false},
        // Feature FAKE-1 (3 commits)
        {hash:"f1a",subject:"FAKE-1: add widget module",          date:"2026-04-02T10:00:00Z", track:"feature", branch:"feature/FAKE-1/add-widget", is_merge:false},
        {hash:"f1b",subject:"FAKE-1: add widget tests",           date:"2026-04-02T11:00:00Z", track:"feature", branch:"feature/FAKE-1/add-widget", is_merge:false},
        {hash:"f1c",subject:"FAKE-1: fix widget edge case",       date:"2026-04-02T12:00:00Z", track:"feature", branch:"feature/FAKE-1/add-widget", is_merge:false},
        // Merge feature into ci
        {hash:"c1", subject:"Merge feature/FAKE-1/add-widget into ci — FAKE-1", date:"2026-04-02T13:00:00Z", track:"ci", branch:"ci", is_merge:true},
        // RC-1 cut from ci (2 commits — regression fix)
        {hash:"r1a",subject:"FAKE-1: fix regression in widget init", date:"2026-04-02T14:00:00Z", track:"rc", branch:"release-rc-1", is_merge:false},
        {hash:"r1b",subject:"FAKE-1: update widget snapshot test",  date:"2026-04-02T14:30:00Z", track:"rc", branch:"release-rc-1", is_merge:false},
        // Merge RC-1 into main
        {hash:"m1", subject:"Merge release-rc-1 into main — FAKE-1", date:"2026-04-02T15:00:00Z", track:"main", branch:"main", is_merge:true},
        // Back-merge main into ci
        {hash:"c2", subject:"Back-merge main (v1.0.0) into ci — FAKE-1", date:"2026-04-02T15:01:00Z", track:"ci", branch:"ci", is_merge:true},
        // Feature FAKE-2 (2 commits)
        {hash:"f2a",subject:"FAKE-2: add gadget module",          date:"2026-04-03T10:00:00Z", track:"feature", branch:"feature/FAKE-2/add-gadget", is_merge:false},
        {hash:"f2b",subject:"FAKE-2: add gadget API endpoint",    date:"2026-04-03T11:00:00Z", track:"feature", branch:"feature/FAKE-2/add-gadget", is_merge:false},
        // Merge feature into ci
        {hash:"c3", subject:"Merge feature/FAKE-2/add-gadget into ci — FAKE-2", date:"2026-04-03T12:00:00Z", track:"ci", branch:"ci", is_merge:true},
        // RC-2 cut from ci (2 commits — config fix)
        {hash:"r2a",subject:"FAKE-2: fix gadget config for prod",   date:"2026-04-03T13:00:00Z", track:"rc", branch:"release-rc-2", is_merge:false},
        {hash:"r2b",subject:"FAKE-2: add gadget health check",      date:"2026-04-03T13:30:00Z", track:"rc", branch:"release-rc-2", is_merge:false},
        // Merge RC-2 into main
        {hash:"m2", subject:"Merge release-rc-2 into main — FAKE-2", date:"2026-04-03T14:00:00Z", track:"main", branch:"main", is_merge:true},
        // Back-merge main into ci
        {hash:"c4", subject:"Back-merge main (v2.0.0) into ci — FAKE-2", date:"2026-04-03T14:01:00Z", track:"ci", branch:"ci", is_merge:true},
      ],
      links: [
        // ci branched from main
        {from_hash:"m0", from_track:"main", to_hash:"c0", to_track:"ci"},
        // FAKE-1: ci → feature (branch-off), feature → ci (merge)
        {from_hash:"c0", from_track:"ci", to_hash:"f1a", to_track:"feature"},
        {from_hash:"f1c", from_track:"feature", to_hash:"c1", to_track:"ci"},
        // FAKE-2: ci → feature (branch-off), feature → ci (merge)
        {from_hash:"c2", from_track:"ci", to_hash:"f2a", to_track:"feature"},
        {from_hash:"f2b", from_track:"feature", to_hash:"c3", to_track:"ci"},
        // RC-1: ci → rc (branch-off from c1), rc → main (merge into m1)
        {from_hash:"c1", from_track:"ci", to_hash:"r1a", to_track:"rc"},
        {from_hash:"r1b", from_track:"rc", to_hash:"m1", to_track:"main"},
        // RC-2: ci → rc (branch-off from c3), rc → main (merge into m2)
        {from_hash:"c3", from_track:"ci", to_hash:"r2a", to_track:"rc"},
        {from_hash:"r2b", from_track:"rc", to_hash:"m2", to_track:"main"},
        // Back-merges: main → ci
        {from_hash:"m1", from_track:"main", to_hash:"c2", to_track:"ci"},
        {from_hash:"m2", from_track:"main", to_hash:"c4", to_track:"ci"},
      ],
    },
  },
  latest_repo: "test-service",
};

let USE_TEST_DATA = false;  // Toggle: true = fake data, false = live API

let currentRepo = null;
let tracksData = null;
let previousLatest = null;
let activeCommits = {};  // {service: {env: short_hash}}
let pulsePhase = 0;

// Fetch active environment commits periodically
async function refreshActiveCommits() {
  try {
    const res = await fetch('/api/active-commits');
    activeCommits = await res.json();
  } catch (e) {}
}
refreshActiveCommits();
setInterval(refreshActiveCommits, 30000);

// Pulse animation — redraws the graph every frame for smooth pulsing
function animatePulse() {
  pulsePhase = (pulsePhase + 0.03) % (Math.PI * 2);
  if (tracksData && currentRepo && Object.keys(activeCommits).length > 0) {
    drawRepoGraph();
  }
  requestAnimationFrame(animatePulse);
}
animatePulse();

async function refreshTracks() {
  try {
    if (USE_TEST_DATA) {
      tracksData = TEST_DATA;
      console.log('Using TEST_DATA');
    } else {
      console.log('Fetching /api/tracks...');
      const res = await fetch('/api/tracks');
      tracksData = await res.json();
      console.log('Got tracks data:', Object.keys(tracksData.repos).length, 'repos, latest:', tracksData.latest_repo);
    }

    // Auto-switch carousel when a new commit arrives in a different repo
    if (tracksData.latest_repo && tracksData.latest_repo !== previousLatest) {
      currentRepo = tracksData.latest_repo;
      previousLatest = tracksData.latest_repo;
    }
    if (!currentRepo && tracksData.latest_repo) {
      currentRepo = tracksData.latest_repo;
    }

    renderCarousel();
    drawRepoGraph();
  } catch (e) { console.error('refreshTracks error:', e); }
}

function renderCarousel() {
  const container = document.getElementById('carousel-tabs');
  if (!container || !tracksData) return;

  const repos = Object.keys(tracksData.repos).sort();
  container.innerHTML = repos.map(repo => {
    const isActive = repo === currentRepo;
    const isLatest = repo === tracksData.latest_repo;
    const classes = ['carousel-tab'];
    if (isActive) classes.push('active');
    if (isLatest) classes.push('latest');
    return `<div class="${classes.join(' ')}" onclick="selectRepo('${repo}')">${repo}</div>`;
  }).join('');
}

function selectRepo(repo) {
  currentRepo = repo;
  renderCarousel();
  drawRepoGraph();
}

function drawRepoGraph() {
  const canvas = document.getElementById('tracks-canvas');
  if (!canvas || !tracksData || !currentRepo) return;
  const repoData = tracksData.repos[currentRepo];
  if (!repoData) return;

  const ctx = canvas.getContext('2d');
  const commits = repoData.commits || [];
  const links = repoData.links || [];

  // ── One column per commit ────────────────────────────────────────────
  // All commits are sorted chronologically. Each gets its own x column.
  // At most one dot per column. The dot sits on its track's y position.
  // Feature commits naturally interleave between the ci commits they
  // were developed between.

  const colSpacing = 36;
  const padLeft = 24;
  const padRight = 40;

  const positions = {};
  commits.forEach((c, i) => {
    positions[c.hash] = {
      x: padLeft + i * colSpacing,
      y: TRACK_Y[c.track],
      track: c.track,
    };
  });

  const width = padLeft + commits.length * colSpacing + padRight;

  // Debug: log commit sequence and links
  console.log('=== ' + currentRepo + ' ===');
  console.log('Commits (' + commits.length + '):');
  commits.forEach((c, i) => {
    console.log('  [' + i + '] ' + c.track.padEnd(8) + ' ' + c.hash + ' ' + (c.branch || '') + ' — ' + c.subject);
  });
  console.log('Links (' + links.length + '):');
  links.forEach(l => {
    const fromPos = positions[l.from_hash];
    const toPos = positions[l.to_hash];
    console.log('  ' + l.from_track + '(' + l.from_hash + ')' + (fromPos ? ' @x=' + fromPos.x : ' MISSING') + ' -> ' + l.to_track + '(' + l.to_hash + ')' + (toPos ? ' @x=' + toPos.x : ' MISSING'));
  });

  canvas.width = Math.max(width, canvas.parentElement.clientWidth);
  canvas.height = 160;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // ── Draw ────────────────────────────────────────────────────────────

  // Track rail lines (faint dashed)
  TRACK_ORDER.forEach(track => {
    const y = TRACK_Y[track];
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(48, 54, 61, 0.5)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 8]);
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
    ctx.setLineDash([]);
  });

  // CI and Main: continuous lines through all commits on that track
  // Feature: connect commits on the SAME branch only
  const branchGroups = {};
  commits.forEach(c => {
    // ci and main are continuous (group by track)
    // feature groups by branch name
    const key = (c.track === 'ci' || c.track === 'main') ? c.track : (c.branch || c.hash);
    if (!branchGroups[key]) branchGroups[key] = { track: c.track, commits: [] };
    branchGroups[key].commits.push(c);
  });

  Object.values(branchGroups).forEach(bg => {
    const tc = bg.commits;
    if (tc.length < 2) return;
    const color = TRACK_COLORS[bg.track];
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.4;
    for (let i = 0; i < tc.length - 1; i++) {
      const p1 = positions[tc[i].hash];
      const p2 = positions[tc[i + 1].hash];
      if (p1 && p2) {
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1.0;
  });

  // Cross-track links — smooth curves
  links.forEach(link => {
    const from = positions[link.from_hash];
    const to = positions[link.to_hash];
    if (!from || !to) return;

    ctx.beginPath();
    ctx.strokeStyle = TRACK_COLORS[link.to_track];
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.7;

    // S-curve: horizontal departure/arrival, clearing the commit circle.
    // Offset start/end by one circle diameter (12px) so the curve is
    // visibly horizontal before it reaches the commit dot.
    const r = 12;
    const dir = to.x > from.x ? 1 : -1;
    const fx = from.x + r * dir;
    const tx = to.x - r * dir;
    const midX = (fx + tx) / 2;
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(fx, from.y);
    ctx.bezierCurveTo(midX, from.y, midX, to.y, tx, to.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
    ctx.globalAlpha = 1.0;
  });

  // Commit circles
  commits.forEach(commit => {
    const pos = positions[commit.hash];
    if (!pos) return;
    const color = TRACK_COLORS[pos.track];

    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 9, 0, Math.PI * 2);
    ctx.fillStyle = color + '18';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Pulse ring for commits that are active in a running environment
    const repoActive = activeCommits[currentRepo] || {};
    const isActive = Object.values(repoActive).includes(commit.hash);
    if (isActive) {
      const pulseRadius = 10 + Math.sin(pulsePhase) * 3;
      const pulseAlpha = 0.4 + Math.sin(pulsePhase) * 0.3;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pulseRadius, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.globalAlpha = pulseAlpha;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }

    if (commit.is_merge) {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 7, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.5;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }
  });

  // Rich tooltip — appears instantly on hover, fetches detail from API
  const tip = document.getElementById('commit-tooltip');
  let tipFetchController = null;
  let tipVisible = false;
  let lastTipHash = '';

  canvas.onmousemove = function(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    let found = null;

    for (const commit of commits) {
      const pos = positions[commit.hash];
      if (!pos) continue;
      if (Math.sqrt((mx - pos.x) ** 2 + (my - pos.y) ** 2) < 10) {
        found = commit;
        break;
      }
    }

    if (!found) {
      if (tipVisible) {
        tip.style.display = 'none';
        tipVisible = false;
        lastTipHash = '';
        if (tipFetchController) { tipFetchController.abort(); tipFetchController = null; }
      }
      canvas.style.cursor = 'default';
      return;
    }
    canvas.style.cursor = 'pointer';

    // Position tooltip near cursor
    tip.style.left = (e.clientX + 12) + 'px';
    tip.style.top = (e.clientY - 10) + 'px';

    if (found.hash === lastTipHash) return; // already showing
    lastTipHash = found.hash;

    // Show immediately with basic info
    const color = TRACK_COLORS[found.track] || '#888';
    const date = new Date(found.date).toLocaleString();
    tip.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
        <span style="color:${color};font-weight:700">${found.hash}</span>
        <span style="color:var(--text-dim);font-size:10px">${found.track}${found.branch && found.branch !== found.track ? ' / ' + found.branch : ''}</span>
      </div>
      <div style="margin-bottom:4px">${found.subject}</div>
      <div style="color:var(--text-dim);font-size:11px">${found.author || ''} · ${date}</div>
      <div style="color:var(--text-dim);font-size:11px;margin-top:4px">Loading details...</div>
    `;
    tip.style.display = 'block';
    tipVisible = true;

    // Fetch detail asynchronously
    if (tipFetchController) tipFetchController.abort();
    tipFetchController = new AbortController();
    fetch('/api/commit/' + currentRepo + '/' + found.hash, { signal: tipFetchController.signal })
      .then(r => r.json())
      .then(d => {
        if (!tipVisible || lastTipHash !== found.hash) return;
        const filesHtml = d.files && d.files.length > 0
          ? d.files.slice(0, 8).map(f => `<div style="color:var(--text-dim);font-size:10px;font-family:'SF Mono',monospace">  ${f}</div>`).join('')
            + (d.files.length > 8 ? `<div style="color:var(--text-dim);font-size:10px">  ... and ${d.files.length - 8} more</div>` : '')
          : '<div style="color:var(--text-dim);font-size:10px">  (no files)</div>';

        const statsColor = d.insertions > 0 ? 'var(--green)' : 'var(--text-dim)';
        const delColor = d.deletions > 0 ? 'var(--red)' : 'var(--text-dim)';

        tip.innerHTML = `
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
            <span style="color:${color};font-weight:700">${d.hash || found.hash}</span>
            <span style="color:var(--text-dim);font-size:10px">${found.track}${found.branch && found.branch !== found.track ? ' / ' + found.branch : ''}</span>
          </div>
          <div style="margin-bottom:4px">${d.subject || found.subject}</div>
          <div style="color:var(--text-dim);font-size:11px">${d.author || ''} &lt;${d.email || ''}&gt; · ${date}</div>
          <div style="margin-top:6px;font-size:11px">
            <span style="color:${statsColor}">+${d.insertions || 0}</span>
            <span style="color:var(--text-dim)"> / </span>
            <span style="color:${delColor}">-${d.deletions || 0}</span>
            <span style="color:var(--text-dim)"> · ${d.files_changed || 0} file${(d.files_changed || 0) !== 1 ? 's' : ''}</span>
          </div>
          <div style="margin-top:4px">${filesHtml}</div>
        `;
      })
      .catch(() => {});
  };

  canvas.onmouseleave = function() {
    tip.style.display = 'none';
    tipVisible = false;
    lastTipHash = '';
  };

  // Preserve scroll position across refreshes.
  // Only auto-scroll to right on first render.
  const wrap = canvas.parentElement;
  if (!wrap.dataset.hasRendered) {
    wrap.scrollLeft = canvas.width - wrap.clientWidth;
    wrap.dataset.hasRendered = 'true';
  }
}

function toggleTestData() {
  USE_TEST_DATA = !USE_TEST_DATA;
  const btn = document.getElementById('test-toggle');
  btn.textContent = USE_TEST_DATA ? 'Live Data' : 'Test Data';
  btn.style.borderColor = USE_TEST_DATA ? 'var(--yellow)' : 'var(--border)';
  btn.style.color = USE_TEST_DATA ? 'var(--yellow)' : 'var(--text)';
  currentRepo = null;
  previousLatest = null;
  refreshTracks();
}

refresh();
refreshTracks();
setInterval(refresh, 10000);
setInterval(refreshTracks, 10000);
</script>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/dashboard"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif path == "/api/status":
            self.send_json(get_all_status())
        elif path == "/api/tracks":
            self.send_json(get_commit_tracks())
        elif path == "/api/active-commits":
            self.send_json(get_active_commits())
        elif path.startswith("/api/commit/"):
            # /api/commit/{repo}/{hash}
            parts = path.split("/")
            if len(parts) >= 5:
                repo_name = parts[3]
                commit_hash = parts[4]
                detail = get_commit_detail(repo_name, commit_hash)
                if detail:
                    self.send_json(detail)
                else:
                    self.send_json({"error": "not found"}, 404)
            else:
                self.send_json({"error": "usage: /api/commit/{repo}/{hash}"}, 400)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        match = re.match(r"^/api/(up|down|rebuild)/(\w+)$", path)
        if match:
            action, env = match.groups()
            if env not in ENVIRONMENTS and env != "all":
                self.send_json({"success": False, "stderr": f"Unknown: {env}"}, 400)
                return
            self.send_json(run_envctl(action, env))
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        sys.stderr.write(f"[dashboard] {args[0]}\n")


if __name__ == "__main__":
    port = PORT
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True
    server = ThreadedHTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"Dashboard: http://localhost:{port}")
    server.serve_forever()
