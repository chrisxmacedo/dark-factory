#!/usr/bin/env python3
"""Find meeting notes that still need a decision log.

A note is a markdown file in inbox/meetings/ with an `ended_at:` line.
It is pending when that time is within the last 24 hours (or the file is
newer than 24 hours and has no ended_at) and outputs/meetings/<stem>.md
does not exist yet. The script does not write the log.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


ENDED = re.compile(r"^ended_at:\s*(\S+)", re.MULTILINE)


def parse_dt(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def pending(inbox: Path, logs: Path, now: datetime, hours: int = 24) -> list[dict]:
    if not inbox.is_dir():
        return []
    found = []
    cutoff = now - timedelta(hours=hours)
    for path in sorted(inbox.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        match = ENDED.search(text)
        ended = parse_dt(match.group(1)) if match else None
        if ended is None:
            ended = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if ended < cutoff or ended > now + timedelta(hours=1):
            continue
        log = logs / f"{path.stem}.md"
        if log.is_file():
            continue
        found.append(
            {
                "note": str(path),
                "stem": path.stem,
                "ended_at": ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "log": str(log),
            }
        )
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="List meeting notes missing a decision log")
    parser.add_argument("--inbox", type=Path)
    parser.add_argument("--logs", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--now")
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    inbox = args.inbox or (root / "inbox" / "meetings")
    logs = args.logs or (root / "outputs" / "meetings")
    now = parse_dt(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    items = pending(inbox, logs, now, args.hours)
    payload = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pending": items,
        "needs_log": bool(items),
    }
    destination = args.output or (root / "outputs" / "raw" / "pending-meetings.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
