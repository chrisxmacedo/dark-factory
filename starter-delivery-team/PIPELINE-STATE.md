# Pipeline State — {PROJECT_NAME}

Top-level state owned by the **Programme Lead**. Update after every
Gate signal received, every Deliverable created, every defect routed
across the boundary.

**Do not commit** — this is ephemeral handoff state.

## Capability pipeline

- **Phase:** {A | B | C | post-Gate 1}
- **Gate 1:** {not passed | passed on {YYYY-MM-DD}}
- **Active journey (if Phase C):** {journey-id} {slug} — status {scaffolded | modelling | review | stable}
- See `capability-team/PIPELINE-STATE.md` for detail.

## Handoff queue (journeys awaiting DEV Deliverable)

| Journey ID | Slug | Gate 2 date | Handoff status         | DEV key |
|------------|------|--------------|-------------------------|---------|
|            |      |              | {pending | in-progress} | {DEV-N} |

## Development pipeline

- **Sprint 0 status:** {not started | in progress | done}
- **Active Deliverable:** {DEV-N} — {title} — {status}
- **Deliverables in backlog (built from Stable journeys):** {count}
- See `development-team/PIPELINE-STATE.md` for detail.

## Cross-pipeline defects

| DEV key | Root cause location | Status | Notes |
|---------|---------------------|--------|-------|
|         | {capability | build | infra} | {open | routed | resolved} |       |

## Escalations (FIX EXHAUSTED) — open

| Sub-pipeline | Journey / Deliverable | Reason | Awaiting human direction? |
|--------------|------------------------|--------|----------------------------|
|              |                        |        |                            |

## Last action

{One sentence describing what the Programme Lead did last.}

## Recent Gate transitions (most recent first)

| Timestamp | Event | Journey / Deliverable |
|-----------|-------|------------------------|
|           |       |                        |
