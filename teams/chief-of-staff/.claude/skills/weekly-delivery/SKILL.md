---
name: weekly-delivery
description: Write the Friday delivery status from the JSON the scripts already produced. Use for the weekly CTO report, DORA figures, and cycle time.
---

# Weekly delivery

Run, if the files are missing:

```bash
python3 scripts/pull_delivery.py --days 7
python3 scripts/dora.py
python3 scripts/cycle_time.py
```

Read `outputs/raw/delivery.json`, `outputs/raw/dora.json`, and `outputs/raw/cycle-time.json`. Copy figures. Do not recompute them and do not fill a null with zero.

Write `outputs/weekly/YYYY-MM-DD-delivery-status.md`:

- Risks, dependencies, and decisions needed, in that order.
- The DORA block with the definition strings from the JSON, including when `using_proxy` is true.
- Cycle time, plus the count of issues excluded for a missing start.

A decision needed is a sentence, not a decision, unless `config/positions.md` already covers it.
