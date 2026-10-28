---
name: chase-deadlines
description: Chase open CTO-forum actions that are due soon or late. Use after chase-deadlines.py has written outputs/raw/chase.json.
---

# Chase deadlines

```bash
python3 scripts/chase_deadlines.py
```

If `needs_chase` is false, stop. Do not write a note that says there was nothing to do unless a human asked.

If it is true, write `drafts/chase/YYYY-MM-DD.md`. You may `gh issue comment` when `github_issue` is set. You may edit the deadline inside `outputs/actions/actions.json` and say what the new date is.

When `days_late` is set, also write `drafts/escalations/<id>.md` for the owner's director. Leave sending it to the human. Do not change a tracker's priority or status.
