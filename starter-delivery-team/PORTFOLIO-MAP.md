# Portfolio Map — {PROJECT_NAME}

Portfolio-level view owned by the **Programme Lead**. One row per
journey from inventory → stable → building → live.

Regenerate after every Gate 2 pass and every DEV Deliverable transition.
This is a read-across of the sub-pipeline state files plus Jira status.

**Do not commit** — ephemeral working document.

## Journeys

| Priority | Journey ID | Slug | Design status | DEV key | Build status | Released as | Notes |
|----------|------------|------|----------------|---------|----------------|---------------|-------|
|          |            |      | {inventory \| scaffolded \| modelling \| review \| stable} | {DEV-N \| —} | {—  \| backlog \| refinement \| dev \| local test \| integ \| e2e \| regression \| release \| done} | {version tag or —} |       |

## Portfolio health indicators

- **Design-to-build lead time** (Gate 2 → DEV Backlog creation):
  median ~ {N} hours
- **Build cycle time** (Backlog → Done):
  median ~ {N} days
- **Open cross-pipeline defects:** {N}
- **Open capability-team refinements:** {N} (see `capability-team/PIPELINE-STATE.md`)
- **Journeys in flight simultaneously:** {N}

## Current bottlenecks

- {Free text — e.g. "Team Lead paused on HIN-42; diagnostics cycle 2
  in progress. If FIX EXHAUSTED, will escalate."}

## Upcoming (next 3 journeys by priority)

| Priority | Journey ID | Slug | Expected capabilities | Earliest handoff |
|----------|------------|------|------------------------|-------------------|
|          |            |      |                        |                   |
