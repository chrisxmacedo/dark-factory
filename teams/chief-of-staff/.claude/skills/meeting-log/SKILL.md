---
name: meeting-log
description: Turn a CTO-forum note into a decision and action log within 24 hours. Use when inbox/meetings has a note with no matching output.
---

# Meeting log

```bash
python3 scripts/pending_meetings.py
```

For each pending note, write `outputs/meetings/<stem>.md` and merge its actions into `outputs/actions/actions.json`.

An action has `id`, `text`, `owner_role`, `deadline`, `forum`, `status`, and optional `github_issue`. Status starts as `open`. Do not store a person's name; store the role.

Only mark a line as a decision this office has taken when `config/positions.md` already allows it. Other outcomes are recorded as "for the CTO".
