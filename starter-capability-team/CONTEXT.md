# starter-capability-team

Capability-driven system design pipeline. Produces machine-readable JSON
artefacts consumed by a development pipeline (starter-development-team).

## Structure

```
.claude/
  agents/
    discovery-team.md          — Phase A + B (steps 1-6, do once)
    journey-modelling-team.md  — Phase C (steps 7-13, per journey)
    ui-specification-team.md   — Phase D (steps 14-18, per portal)
    review-team.md             — Cross-cutting quality gate
  context/
    project.md             — Project identity, Jira config, artefact repo
    phases.md              — Phase model, gates, orchestration
    artefact-standards.md  — JSON format, naming, lifecycle, vocabulary
    best-practices/
      capability-modelling.md  — Phase A-C best practices
      ui-specification.md      — Phase D best practices
artefacts/                 — All design outputs
  foundation/              — Phase A + B (JSON)
  architecture/            — Phase B (JSON + Structurizr DSL + observability + security)
  models/                  — Phase C per journey (JSON + Mermaid)
  central-model/           — Aggregated from all journeys (JSON)
  ui-specs/                — Phase D per portal (JSON)
  design-system/           — Cross-portal patterns (JSON)
  schemas/                 — JSON schemas for validation
PIPELINE.md                — Programme Lead orchestration
```

## Placeholders to replace

| Placeholder | Replace with |
|-------------|-------------|
| `{PROJECT_NAME}` | Full project name |
| `{ORG_NAME}` | Organisation name |
| `{FOUND_KEY}` | Jira Foundation project key |
| `{MODEL_KEY}` | Jira Modelling project key |
| `{UXSPEC_KEY}` | Jira UI Spec project key |
| `{DEV_KEY}` | Jira Development project key |
| `{PROJECT_KEY}` | Default project key for jiractl |
| `{CURRENT_PHASE}` | Starting phase (usually "Phase A — Discovery") |

## Relationship to development pipeline

This pipeline produces specifications. The development pipeline builds
the software. The handoff point is:

  Stable journey model (Phase C) + Approved screen specs (Phase D)
  = One buildable Deliverable in the DEV project

Design and development overlap. The first journey can be in production
while the fifteenth journey is still being modelled.
