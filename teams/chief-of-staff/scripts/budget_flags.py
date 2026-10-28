#!/usr/bin/env python3
"""Compare a finance drop with the configured spend caps.

Input is a CSV the finance partner drops in inbox/finance/actuals.csv.
The script flags rows. It does not approve spend. A headcount row is always
needs_human, because people decisions are outside this role even when the
amount is inside a cap. Caps are inclusive: an amount equal to the cap is
within it ("up to" the cap).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
for ancestor in Path(__file__).resolve().parents:
    harness = ancestor / "harness" / "scripts"
    if harness.is_dir():
        sys.path.insert(0, str(harness))
        break

from office_env import load_config  # noqa: E402
from paths import office_root  # noqa: E402


def money(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise SystemExit(f"Amount is not a number: {value!r}") from exc


def cap(config: dict[str, str], key: str) -> Decimal:
    raw = config.get(key, "").strip()
    if not raw:
        raise SystemExit(
            f"{key} is not set. Copy config/ara.env.example to config/ara.env "
            "and set the caps your organisation actually approved. "
            "The example numbers are not an approval."
        )
    return money(raw)


def evaluate(rows: list[dict[str, str]], config: dict[str, str], as_of: date) -> dict:
    item_cap = cap(config, "SPEND_CAP_ITEM")
    annual_cap = cap(config, "SPEND_CAP_ANNUAL")
    consultant_cap = cap(config, "SPEND_CAP_CONSULTANT")
    term_cap = int(config.get("SPEND_CAP_CONSULTANT_MONTHS") or "3")
    currency = config.get("SPEND_CURRENCY") or "GBP"
    flagged = []
    annual = Decimal("0")
    for row in rows:
        category = (row.get("category") or "other").strip().lower()
        amount = money(row.get("amount") or "0")
        committed = (row.get("committed_on") or "").strip()
        term_raw = (row.get("term_months") or "").strip()
        term = int(term_raw) if term_raw else None
        reasons = []
        if category == "headcount":
            reasons.append("people_decision")
        elif category == "consultant":
            if amount > consultant_cap:
                reasons.append("consultant_over_cap")
            if term is not None and term > term_cap:
                reasons.append("consultant_term_over_cap")
        elif amount > item_cap:
            reasons.append("item_over_cap")
        if committed:
            committed_date = date.fromisoformat(committed[:10])
            if committed_date.year == as_of.year:
                annual += amount
        else:
            annual += amount
            reasons.append("missing_committed_on")
        flagged.append(
            {
                "category": category,
                "item": (row.get("item") or "").strip(),
                "amount": str(amount),
                "currency": currency,
                "committed_on": committed,
                "term_months": term,
                "reasons": reasons,
                "decision": "needs_human" if reasons else "within_cap",
            }
        )
    annual_reasons = ["annual_over_cap"] if annual > annual_cap else []
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "as_of": as_of.isoformat(),
        "currency": currency,
        "caps": {
            "item": str(item_cap),
            "annual": str(annual_cap),
            "consultant": str(consultant_cap),
            "consultant_months": term_cap,
            "inclusive": True,
        },
        "annual_total": str(annual),
        "annual_decision": "needs_human" if annual_reasons else "within_cap",
        "annual_reasons": annual_reasons,
        "rows": flagged,
        "needs_human": any(row["decision"] == "needs_human" for row in flagged) or bool(annual_reasons),
        "definition": (
            "within_cap means the row is inside the configured caps and is not headcount. "
            "needs_human means this role must draft the item for the CTO and must not approve it. "
            "Headcount is always needs_human."
        ),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Flag tech spend against configured caps")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--as-of", dest="as_of")
    args = parser.parse_args()
    root = office_root()
    source = args.input or (root / "inbox" / "finance" / "actuals.csv")
    destination = args.output or (root / "outputs" / "raw" / "budget-flags.json")
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        payload = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "no_actuals",
            "needs_human": True,
            "definition": "Finance has not dropped actuals. Do not invent figures.",
        }
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {destination} (no actuals)")
        return
    result = evaluate(read_csv(source), load_config(root), as_of)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
