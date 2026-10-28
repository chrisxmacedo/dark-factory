#!/usr/bin/env python3
"""Validate a RAID log. The agent writes the narrative; this checks the shape.

A RAID log is JSON with risks, assumptions, issues, and dependencies.
Each item has id, text, owner_role, and status. Owner is a role, not a
person's name, so the template stays free of employee data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SECTIONS = ("risks", "assumptions", "issues", "dependencies")
ITEM_KEYS = ("id", "text", "owner_role", "status")


def validate(document: dict) -> list[str]:
    errors = []
    if not isinstance(document, dict):
        return ["RAID log must be a JSON object"]
    for section in SECTIONS:
        items = document.get(section)
        if not isinstance(items, list):
            errors.append(f"{section} must be a list")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{section}[{index}] must be an object")
                continue
            for key in ITEM_KEYS:
                if not str(item.get(key) or "").strip():
                    errors.append(f"{section}[{index}] missing {key}")
    return errors


def template(initiative_id: str) -> dict:
    return {
        "initiative": initiative_id,
        "risks": [],
        "assumptions": [],
        "issues": [],
        "dependencies": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or create a RAID log")
    parser.add_argument("--check", type=Path)
    parser.add_argument("--init", help="Initiative id. Writes outputs/initiatives/<id>/raid.json if missing")
    parser.add_argument("--list", action="store_true", help="Check every RAID log under outputs/initiatives")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.init:
        destination = root / "outputs" / "initiatives" / args.init / "raid.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_text(json.dumps(template(args.init), indent=2) + "\n", encoding="utf-8")
            print(f"wrote {destination}")
        else:
            print(f"kept {destination}")
        return
    targets = []
    if args.check:
        targets.append(args.check)
    if args.list or not targets:
        base = root / "outputs" / "initiatives"
        if base.is_dir():
            targets.extend(sorted(base.glob("*/raid.json")))
    failed = False
    if not targets:
        print("no RAID logs")
        return
    for path in targets:
        errors = validate(json.loads(path.read_text(encoding="utf-8")))
        if errors:
            failed = True
            print(f"{path}:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{path}: ok")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
