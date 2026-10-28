---
name: budget-tracker
description: Write the monthly tech budget tracker on working day 5 from budget-flags.json. Never approve a needs_human row.
---

# Budget tracker

```bash
python3 scripts/budget_flags.py
```

Write `outputs/budget/YYYY-MM.md`.

- `no_actuals`: say the finance drop has not arrived. Stop.
- `within_cap`: report the row as inside the configured caps.
- `needs_human`: flag it, draft `drafts/for-cto/`, and do not approve it.

Headcount is always `needs_human`. Caps are whatever `config/ara.env` says. Do not fall back to the example file.
