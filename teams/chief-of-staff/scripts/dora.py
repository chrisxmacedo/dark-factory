#!/usr/bin/env python3
"""Compute DORA figures from outputs/raw/delivery.json.

Definitions are written next to the numbers. Missing signals stay null.
A merged pull request is used as a deployment proxy only when the payload
has no production deployments, and the output says so. Change-fail rate is
never invented from that proxy.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


PRODUCTION = {"production", "prod"}
FAILURE = {"failure", "failed", "error"}


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def hours_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None or end < start:
        return None
    return round((end - start).total_seconds() / 3600, 2)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 2)
    return round((ordered[mid - 1] + ordered[mid]) / 2, 2)


def compute(document: dict) -> dict:
    window = document.get("window") or {}
    start = parse_dt(window.get("start"))
    end = parse_dt(window.get("end"))
    window_days = None
    if start and end and end > start:
        window_days = round((end - start).total_seconds() / 86400, 2)

    deployments = [
        item
        for item in document.get("deployments") or []
        if str(item.get("environment", "")).lower() in PRODUCTION
    ]
    failures = [item for item in deployments if str(item.get("status", "")).lower() in FAILURE]
    pulls = [item for item in document.get("pull_requests") or [] if item.get("merged_at")]
    using_proxy = False
    notes = []
    if deployments:
        deploy_count = len(deployments)
        change_fail = round(len(failures) / deploy_count, 4)
        change_fail_reason = "production deployments whose latest status is failure or error, divided by production deployments in the window"
    elif pulls:
        using_proxy = True
        deploy_count = len(pulls)
        change_fail = None
        change_fail_reason = "not available: there are no production deployment records, so merged pull requests are not treated as failures or successes"
        notes.append("deployment_frequency uses merged pull requests because no production deployments were in the payload")
    else:
        deploy_count = 0
        change_fail = None
        change_fail_reason = "not available: no production deployments and no merged pull requests in the window"

    frequency = None
    if window_days and deploy_count:
        frequency = round(deploy_count / window_days, 4)

    lead_times = []
    lead_proxy = 0
    for pull in pulls:
        lead = hours_between(parse_dt(pull.get("first_commit_at")), parse_dt(pull.get("merged_at")))
        if lead is None:
            continue
        lead_times.append(lead)
        if pull.get("first_commit_source") == "pull_request_created":
            lead_proxy += 1

    repairs = []
    for incident in document.get("incidents") or []:
        repair = hours_between(parse_dt(incident.get("started_at")), parse_dt(incident.get("resolved_at")))
        if repair is not None:
            repairs.append(repair)

    if lead_proxy:
        notes.append(
            f"{lead_proxy} lead-time sample(s) use pull-request creation time because the first commit time was missing"
        )

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": window,
        "using_proxy": using_proxy,
        "deployment_frequency_per_day": frequency,
        "deployment_count": deploy_count,
        "lead_time_hours_median": median(lead_times),
        "lead_time_samples": len(lead_times),
        "change_fail_rate": change_fail,
        "mttr_hours_median": median(repairs),
        "mttr_samples": len(repairs),
        "notes": notes,
        "definitions": {
            "deployment_frequency_per_day": "production deployments in the window divided by window length in days. If there are none, merged pull requests are counted and using_proxy is true.",
            "lead_time_hours_median": "median hours from first commit (or pull-request creation if that is all the payload has) to merge, for pull requests merged in the window. Even counts use the mean of the two central values.",
            "change_fail_rate": change_fail_reason,
            "mttr_hours_median": "median hours from incident start to resolve. Null when the payload has no resolved incidents. This script does not infer incidents from failed builds.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute DORA figures from a delivery payload")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    # parents[0] is scripts, parents[1] is the office root in both layouts.
    source = args.input or (root / "outputs" / "raw" / "delivery.json")
    if not source.is_file():
        raise SystemExit(f"No delivery payload at {source}. Run pull_delivery.py first.")
    document = json.loads(source.read_text(encoding="utf-8"))
    result = compute(document)
    destination = args.output or (root / "outputs" / "raw" / "dora.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
