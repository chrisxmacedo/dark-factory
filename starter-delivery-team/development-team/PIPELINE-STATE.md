# Pipeline State — {PROJECT_NAME}

The Team Lead updates this file after every Jira transition, every agent
signal received, every branch operation, and every `envctl rebuild`.
It is the crash-recovery source of truth.

**Read by the Programme Lead** (`../PIPELINE.md`) — polls the "Signals
received" and "Incoming handoff" sections to coordinate the delivery
team. Keep those current so cross-pipeline events are not missed.

**Do not commit this file** — ephemeral pipeline state.

## Incoming handoff (from Programme Lead)

The Programme Lead writes here when it creates a new Deliverable. The
Team Lead clears the entry once the Deliverable has moved past In
Refinement.

| DEV key | Title | Journey source | Brief path | Repos | Delivered |
|---------|-------|----------------|-------------|-------|-----------|
|         |       |                |             |       |           |

## Active ticket

- **Key:** {DEV_KEY}-{N}
- **Title:**
- **Type:** Deliverable | Task
- **Status:**
- **Branch:** feature/{DEV_KEY}-{N}/{slug}
- **Stage started:** {ISO timestamp}
- **MODEL journey epic:** {MODEL_KEY}-{N} (for Deliverables)

## Signals received (for the active ticket)

- [ ] REFINEMENT COMPLETE — {timestamp}
- [ ] SOLUTION DESIGN — {timestamp}
- [ ] TASKS CREATED ({count} tasks) — {timestamp}
- [ ] RISK ASSESSMENT: {clean | flagged} — {timestamp}
- [ ] DEVELOPMENT COMPLETE — {timestamp}
- [ ] LOCAL TEST PASSED — {timestamp}
- [ ] MERGED TO CI — {timestamp}
- [ ] INTEGRATION TEST PASSED — {timestamp}
- [ ] E2E IMPACT PASSED — {timestamp}
- [ ] RC CUT — {timestamp}
- [ ] REGRESSION PASSED — {timestamp}
- [ ] HUMAN PROMOTE APPROVED — {timestamp}
- [ ] RELEASED TO PROD — {timestamp}
- [ ] DELIVERABLE DONE — {timestamp}

## Signals to Programme Lead (outgoing)

- [ ] DELIVERABLE DONE reported — {timestamp}
- [ ] SPEC DEFECT RAISED — {DEV key} — {timestamp} — {one-line reason}
- [ ] FIX EXHAUSTED — {DEV key} — {timestamp} — {one-line reason}

## Branch state

| Repo | Branch | Clean? | Last action |
|------|--------|--------|-------------|
|      |        |        |             |

## Last action

{One sentence describing the last thing the Team Lead did or spawned.}

## Docker environments

| Env  | Running? | Last rebuilt | Healthy? |
|------|----------|--------------|----------|
| CI   |          |              |          |
| RC   |          |              |          |
| Prod |          |              |          |

## Open defects (build-side)

| DEV key | Stage found | Diagnostics cycles | Status | Spec-defect? |
|---------|-------------|---------------------|--------|---------------|
|         |             |                     |        |               |
