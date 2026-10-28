# Human escalation

The chief of staff decides only inside the caps in `config/ara.env` and the positions in `config/positions.md`. Everything else is a draft for a human.

The writing rules live in the `human-escalation` skill. The boundary is also enforced, not only described: `scripts/guard_authority.py` runs as a Claude Code `PreToolUse` hook and refuses writes outside `outputs/` and `drafts/`, repository changes, pull-request merges and reviews, and tracker calls that update, transition, or reprioritise work.

Spend above a cap is flagged by `scripts/budget_flags.py` as `needs_human`. The hook cannot see a business decision, so the budget skill forbids approving those rows. Headcount is always `needs_human`.

A draft is not sent and not treated as accepted.
