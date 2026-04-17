# Project identity

Project name: {PROJECT_NAME}
Organisation: {ORG_NAME}

## Jira projects

| Project | Key | Phase | Board |
|---------|-----|-------|-------|
| Foundation | {FOUND_KEY} | A + B | Kanban |
| Analytical Modelling | {MODEL_KEY} | C | Scrum |
| Development | {DEV_KEY} | Build | Pipeline |

## Artefact repository

All design artefacts live in a single Git repository:

```
artefacts/
  foundation/           # Phase A + B outputs
    capabilities/
    governance/
    personas/
    technical-services/
    journey-inventory.json
    shared-sub-capabilities.json
  architecture/         # Phase B outputs
    visual-architecture.json
    channel-model.json
    c4-workspace.dsl
    service-dependencies.json
    service-catalogue.json
    observability-model.json
    security-model.json
    environment-spec.json
  models/               # Phase C outputs (per journey)
    {journey-name}/
      _manifest.json
      _refinement-brief.md
      journey-detail.json
      participant-interaction.json
      nfr.json
      data-model.json
      service-boundaries.json
      api-contracts/
      sequence-diagrams/
      events/
      evidence/         # validator outputs committed alongside artefacts
  central-model/        # Aggregated from all journeys
    entities/
    service-map.json
    event-catalogue.json
  schemas/              # JSON schemas for validation
```

## Current phase

{CURRENT_PHASE} — update this as the project progresses.
