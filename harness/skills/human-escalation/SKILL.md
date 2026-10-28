---
name: human-escalation
description: Decide only inside the chief-of-staff caps and the positions the CTO already wrote down. Use before confirming spend, a position, a people matter, an architecture point, or a change to engineering commitments.
---

# Human escalation

Read `config/ara.env` and `config/positions.md` before you decide. If either file is missing, write a draft and stop.

Decide only when both are true:

- The choice is one of the authority bullets in `CLAUDE.md`.
- The same choice is already written in `config/positions.md`, or it is spend that `outputs/raw/budget-flags.json` marks `within_cap` and it is not headcount.

Draft, and do not decide, when any of these are true:

- The script says `needs_human`, `no_actuals`, or the caps are unset.
- The amount is above a cap, or a consultant term is longer than `SPEND_CAP_CONSULTANT_MONTHS`. Caps are inclusive.
- It is a new position, a hiring or performance matter, or an architecture or product-priority call.
- It would change an engineering team's backlog, priority, status, sprint, or commitments.
- It would change product code or a pull request.

Write drafts under `drafts/for-cto/` or `drafts/escalations/`. A draft states the question, the facts you actually have, and the decision you are not making. Do not send it and do not describe it as approved.
