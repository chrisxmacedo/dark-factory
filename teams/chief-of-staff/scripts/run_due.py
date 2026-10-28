#!/usr/bin/env python3
"""Decide which office jobs are due, run their scripts, then optionally Claude.

A job's prepare steps are plain scripts. Claude is invoked only after those
scripts exit 0, and only when the job's gate says there is something to do.
--dry-run prints the commands and does not run them. --list prints the gates
for one moment and does not run anything.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
for ancestor in Path(__file__).resolve().parents:
    harness = ancestor / "harness" / "scripts"
    if harness.is_dir():
        sys.path.insert(0, str(harness))
        break

from chase_deadlines import classify  # noqa: E402
from office_env import load_config  # noqa: E402
from paths import office_root  # noqa: E402
from pending_meetings import pending  # noqa: E402
from working_days import (  # noqa: E402
    board_due,
    load_holidays,
    parse_date,
    quarterly_due,
    working_day_number,
)


def load_jobs(root: Path) -> list[dict]:
    payload = json.loads((root / "schedules" / "jobs.json").read_text(encoding="utf-8"))
    return payload["jobs"]


def local_now(config: dict[str, str], at: str | None) -> datetime:
    zone = ZoneInfo(config.get("OFFICE_TZ") or "UTC")
    if at:
        parsed = datetime.fromisoformat(at)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=zone)
        return parsed.astimezone(zone)
    return datetime.now(zone)


def initiative_due(root: Path, day: date) -> tuple[bool, str]:
    inbox = root / "inbox" / "initiatives"
    if not inbox.is_dir():
        return False, "no initiatives"
    due = []
    for meta_path in sorted(inbox.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        initiative_id = meta.get("id") or meta_path.parent.name
        milestone = meta.get("next_milestone") or ""
        close_by = meta.get("close_by") or ""
        stage = meta.get("stage") or ""
        brief = root / "outputs" / "initiatives" / initiative_id / "brief.md"
        if milestone[:10] == day.isoformat() or (close_by and close_by[:10] == day.isoformat()):
            due.append(initiative_id)
        elif stage == "kickoff" and not brief.is_file():
            due.append(initiative_id)
    if not due:
        return False, "no initiative milestone today"
    return True, "due: " + ", ".join(due)


def gate(job: dict, root: Path, moment: datetime, config: dict[str, str], holidays: set[date]) -> tuple[bool, str]:
    kind = job.get("gate") or "always"
    day = moment.date()
    weekdays = job.get("weekdays")
    if weekdays and moment.strftime("%A").lower() not in weekdays:
        return False, f"not a scheduled weekday ({moment.strftime('%A')})"
    if kind == "always":
        return True, "scheduled"
    if kind == "working_day":
        number = working_day_number(day, holidays)
        expected = int(job.get("working_day") or 0)
        if number == expected:
            return True, f"working day {number}"
        return False, f"today is working day {number}, job wants {expected}"
    if kind == "days_before_quarter":
        lead = int(job.get("lead_days") or config.get("QUARTER_LEAD_DAYS") or 7)
        if quarterly_due(day, lead, holidays):
            return True, f"{lead} days before the next quarter"
        return False, "not the quarterly due date"
    if kind == "working_days_before_board":
        raw = config.get(job.get("dates_env") or "BOARD_DATES", "")
        boards = [parse_date(item) for item in raw.split(",") if item.strip()]
        if not boards:
            return False, "BOARD_DATES is empty"
        matched = board_due(day, boards, int(job.get("working_days") or 10), holidays)
        if matched:
            return True, f"10 working days before {matched.isoformat()}"
        return False, "no board pack due today"
    if kind == "pending_meetings":
        hours = int(job.get("hours") or 24)
        items = pending(root / "inbox" / "meetings", root / "outputs" / "meetings", moment.astimezone(timezone.utc), hours)
        if items:
            return True, f"{len(items)} meeting note(s) need a log"
        return False, "no meeting notes waiting"
    if kind == "open_chase":
        path = root / "outputs" / "actions" / "actions.json"
        if not path.is_file():
            return False, "no action log yet"
        actions = json.loads(path.read_text(encoding="utf-8")).get("actions") or []
        within = int(config.get("CHASE_WITHIN_DAYS") or "2")
        result = classify(actions, day, within)
        if result["needs_chase"]:
            return True, f"{len(result['overdue'])} overdue, {len(result['due_soon'])} due soon"
        return False, "nothing to chase"
    if kind == "initiative_milestone":
        return initiative_due(root, day)
    return False, f"unknown gate {kind}"


def prepare_commands(job: dict) -> list[list[str]]:
    commands = []
    for step in job.get("prepare") or []:
        commands.append(["python3", *step])
    return commands


def claude_command(root: Path, job: dict, config: dict[str, str]) -> list[str]:
    budget = str(job.get("budget_usd") or config.get("CLAUDE_MAX_BUDGET_USD") or "2.00")
    command = [
        str(root / "scripts" / "claude-headless.sh"),
        "--agent",
        job["agent"],
        "--prompt-file",
        job["prompt"],
        "--budget",
        budget,
    ]
    return command


def run_commands(commands: list[list[str]], root: Path, dry_run: bool) -> int:
    for command in commands:
        print("+", " ".join(command))
        if dry_run:
            continue
        completed = subprocess.run(command, cwd=root, check=False)
        if completed.returncode != 0:
            print(f"stopped before Claude: {' '.join(command)} exited {completed.returncode}", file=sys.stderr)
            return completed.returncode
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run office jobs whose deadline is today")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--job")
    parser.add_argument("--at", help="ISO datetime in OFFICE_TZ, or with an offset")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Run the named job even if its gate is closed")
    args = parser.parse_args()
    root = office_root()
    config = load_config(root)
    moment = local_now(config, args.at)
    holidays = load_holidays(root / "config" / "holidays.txt")
    jobs = load_jobs(root)
    if args.job:
        jobs = [job for job in jobs if job["id"] == args.job]
        if not jobs:
            raise SystemExit(f"No job named {args.job}")
    due_jobs = []
    for job in jobs:
        is_due, reason = gate(job, root, moment, config, holidays)
        print(f"{job['id']}: {'due' if is_due else 'skip'} — {reason}")
        if is_due or (args.force and args.job):
            due_jobs.append(job)
    if args.list:
        return
    if not args.job:
        raise SystemExit("Pass --job ID to run one job, or --list to inspect the calendar.")
    if not due_jobs:
        return
    job = due_jobs[0]
    code = run_commands(prepare_commands(job), root, args.dry_run)
    if code != 0:
        raise SystemExit(code)
    claude = claude_command(root, job, config)
    if args.dry_run:
        claude = [claude[0], "--dry-run", *claude[1:]]
    print("+", " ".join(claude))
    if args.dry_run:
        return
    env = os.environ.copy()
    env["OFFICE_ROOT"] = str(root)
    completed = subprocess.run(claude, cwd=root, check=False, env=env)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
