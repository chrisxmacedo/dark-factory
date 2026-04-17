# starter-capability-team

Capability-driven system design pipeline. Produces a headless system
specification as machine-readable JSON artefacts consumed by a
development pipeline (starter-development-team).

## Structure

```
.claude/
  agents/
    discovery-team.md          — Phase A + B (steps 1-6, do once)
    journey-modelling-team.md  — Phase C (steps 7-13, per journey)
    review-team.md             — Cross-cutting quality gate
  context/
    project.md                  — Project identity, Jira config
    phases.md                   — Phase model, gates, orchestration
    artefact-standards.md       — JSON format, naming, lifecycle, vocabulary
    architecture-specification.md — Capability-driven architecture (authoritative)
    best-practices/
      capability-modelling.md  — Phase A-C best practices
    process-improvements.md    — Generalised learnings, script inventory
scripts/
  scaffold-journey.py          — Pre-creation: directories, manifest, templates
  validate-journey.py          — Post-creation: files, IDs, ownership, central model
  validate-sequences.py        — Post-creation: cross-capability violation checks
artefacts/                     — All design outputs (template structure)
  foundation/                  — Phase A + B (JSON)
    capabilities/              — One file per capability
    governance/                — One file per capability
    personas/                  — External + internal persona files
    technical-services/        — Domain, cross-cutting, foundation service files
  architecture/                — Phase B (JSON + Structurizr DSL)
  models/                      — Phase C per journey (JSON + Mermaid)
  central-model/               — Aggregated from all journeys (JSON)
    entities/                  — One file per entity
  schemas/                     — JSON schemas for validation
PIPELINE.md                    — Programme Lead orchestration
CONTEXT.md                     — This file
```

## Placeholders to replace

| Placeholder | Replace with |
|-------------|-------------|
| `{PROJECT_NAME}` | Full project name |
| `{ORG_NAME}` | Organisation name |
| `{FOUND_KEY}` | Jira Foundation project key |
| `{MODEL_KEY}` | Jira Modelling project key |
| `{DEV_KEY}` | Jira Development project key |
| `{PROJECT_KEY}` | Default project key |
| `{CURRENT_PHASE}` | Starting phase (usually "Phase A — Discovery") |

## Relationship to development pipeline

This pipeline produces a headless system specification — capabilities,
their APIs, their events, and the journey contracts that describe how
they compose. Channel UIs (web, mobile, branch) sit outside the system
boundary and are a separate development concern.

The handoff point is:

  Stable journey model (Phase C, Gate 2 passed)
  = One buildable Deliverable in the DEV project

Design and development overlap. The first journey can be in production
while the fifteenth journey is still being modelled.

## Pipeline flow

The Programme Lead orchestrates:

```
Phase A+B: Spawn Discovery Team → Gate 1
Phase C:   For each journey:
             1. scaffold-journey.py (pre-creation)
             2. Spawn Journey Modelling Team
             3. Spawn Review Team (per artefact)
             4. validate-journey.py (post-creation)
             5. validate-sequences.py (post-creation)
             6. If fails → back to team
             7. Gate 2 → Handoff to DEV
```

See PIPELINE.md for full orchestration instructions.
