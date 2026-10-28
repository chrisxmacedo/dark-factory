A cross-team initiative the CTO assigned is due a brief, a plan, or a closure note. Read inbox/initiatives/*/meta.json and pick the ones whose milestone is today, whose close date is today, or whose stage is kickoff and which have no brief yet.

For each one, write under outputs/initiatives/<id>/:

- brief.md at kickoff
- plan.md when the milestone is a planning date
- closure.md when close_by is today

Keep a RAID log at outputs/initiatives/<id>/raid.json with risks, assumptions, issues, and dependencies. Each item needs id, text, owner_role, and status. Run `python3 scripts/raid_log.py --check` on that file before you finish. You may run `python3 scripts/raid_log.py --init <id>` to create an empty log.

You do not change engineering backlogs. Dependencies on a team are recorded and chased, not reprioritised.
