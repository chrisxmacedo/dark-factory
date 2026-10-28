---
name: initiative
description: Write the brief, plan, or closure for a CTO-assigned cross-team initiative, with a RAID log.
---

# Initiative

Read `inbox/initiatives/*/meta.json`. Write under `outputs/initiatives/<id>/`. The RAID file must contain `risks`, `assumptions`, `issues`, and `dependencies`, and each item needs `id`, `text`, `owner_role`, and `status`.

```bash
python3 scripts/raid_log.py --init <id>
python3 scripts/raid_log.py --check outputs/initiatives/<id>/raid.json
```

Record dependencies. Do not reprioritise the other team. A closure note says what finished and what is still open. It does not declare an architecture outcome.
