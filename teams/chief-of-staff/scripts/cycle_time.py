#!/usr/bin/env python3
"""Cycle time from a normalised delivery payload.

Cycle time is completed_at minus started_at, in hours, for issues completed
inside the window. Issues with no start time are counted as excluded, not as
zero. The median of an even count is the mean of the two central values.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 2)
    return round((ordered[mid - 1] + ordered[mid]) / 2, 2)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return round(ordered[index], 2)


def compute(document: dict) -> dict:
    window = document.get("window") or {}
    start = parse_dt(window.get("start"))
    end = parse_dt(window.get("end"))
    samples = []
    excluded = []
    for issue in document.get("issues") or []:
        completed = parse_dt(issue.get("completed_at"))
        if completed is None:
            continue
        if start and end and not (start <= completed <= end):
            continue
        started = parse_dt(issue.get("started_at"))
        if started is None or completed < started:
            excluded.append(issue.get("key") or "")
            continue
        hours = round((completed - started).total_seconds() / 3600, 2)
        samples.append(
            {
                "key": issue.get("key") or "",
                "source": issue.get("source") or "",
                "hours": hours,
                "started_at_source": issue.get("started_at_source") or "",
            }
        )
    hours = [sample["hours"] for sample in samples]
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": window,
        "cycle_time_hours_median": median(hours),
        "cycle_time_hours_p75": percentile(hours, 0.75),
        "samples": len(samples),
        "excluded_missing_start": [key for key in excluded if key],
        "by_issue": samples,
        "definition": (
            "Hours from started_at to completed_at for issues completed in the window. "
            "Issues with no usable start are listed in excluded_missing_start and are not treated as zero. "
            "Where started_at_source is statuscategorychangedate, the start is a proxy from Jira, not a confirmed in-progress transition."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute cycle time from a delivery payload")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = args.input or (root / "outputs" / "raw" / "delivery.json")
    if not source.is_file():
        raise SystemExit(f"No delivery payload at {source}. Run pull_delivery.py first.")
    result = compute(json.loads(source.read_text(encoding="utf-8")))
    destination = args.output or (root / "outputs" / "raw" / "cycle-time.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
