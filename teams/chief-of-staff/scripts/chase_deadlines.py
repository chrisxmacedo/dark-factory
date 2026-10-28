#!/usr/bin/env python3
"""List open actions that are due soon or late.

Reads outputs/actions/actions.json. Does not assign owners, close actions,
or change a tracker's priority. The agent writes the chase note; this script
only classifies dates.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
for ancestor in Path(__file__).resolve().parents:
    harness = ancestor / "harness" / "scripts"
    if harness.is_dir():
        sys.path.insert(0, str(harness))
        break

from office_env import load_config  # noqa: E402
from paths import office_root  # noqa: E402


def classify(actions: list[dict], today: date, within_days: int) -> dict:
    overdue = []
    due_soon = []
    for action in actions:
        if str(action.get("status") or "open").lower() != "open":
            continue
        deadline_raw = action.get("deadline") or ""
        if not deadline_raw:
            continue
        deadline = date.fromisoformat(deadline_raw[:10])
        record = {
            "id": action.get("id"),
            "text": action.get("text") or "",
            "owner_role": action.get("owner_role") or "",
            "deadline": deadline.isoformat(),
            "forum": action.get("forum") or "",
            "github_issue": action.get("github_issue") or "",
        }
        if deadline < today:
            record["days_late"] = (today - deadline).days
            overdue.append(record)
        elif deadline <= today + timedelta(days=within_days):
            due_soon.append(record)
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "as_of": today.isoformat(),
        "within_days": within_days,
        "overdue": overdue,
        "due_soon": due_soon,
        "needs_chase": bool(overdue or due_soon),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify open action deadlines")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--as-of")
    parser.add_argument("--within-days", type=int)
    args = parser.parse_args()
    root = office_root()
    config = load_config(root)
    within = args.within_days
    if within is None:
        within = int(config.get("CHASE_WITHIN_DAYS") or "2")
    source = args.input or (root / "outputs" / "actions" / "actions.json")
    destination = args.output or (root / "outputs" / "raw" / "chase.json")
    today = date.fromisoformat(args.as_of) if args.as_of else date.today()
    if not source.is_file():
        result = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "as_of": today.isoformat(),
            "overdue": [],
            "due_soon": [],
            "needs_chase": False,
            "status": "no_actions",
        }
    else:
        payload = json.loads(source.read_text(encoding="utf-8"))
        result = classify(payload.get("actions") or [], today, within)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")
    if not result.get("needs_chase"):
        # Exit 0 either way. Callers that want to skip an agent read needs_chase.
        return


if __name__ == "__main__":
    main()
