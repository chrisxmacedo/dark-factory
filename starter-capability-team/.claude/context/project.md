# Project identity

Project name: {PROJECT_NAME}
Organisation: {ORG_NAME}

## Jira projects

| Project | Key | Phase | Board |
|---------|-----|-------|-------|
| Foundation | {FOUND_KEY} | A + B | Kanban |
| Analytical Modelling | {MODEL_KEY} | C | Scrum |
| UI Specification | {UXSPEC_KEY} | D | Kanban |
| Development | {DEV_KEY} | Build | Pipeline |

## Artefact repository

All design artefacts live in a single Git repository:

```
artefacts/
  foundation/           # Phase A + B outputs
    capabilities/
    governance/
    personas/
    technical-services.json
    journey-inventory.json
    shared-sub-capabilities.json
  architecture/         # Phase B outputs
    visual-architecture.json
    channel-model.json
  models/               # Phase C outputs (per journey)
    {journey-name}/
      journey-detail.json
      participant-interaction.json
      nfr.json
      data-model.json
      service-boundaries.json
      api-contracts/
      events/
  central-model/        # Aggregated from all journeys
    entities/
    service-map.json
    event-catalogue.json
  ui-specs/             # Phase D outputs (per portal)
    {portal-name}/
      information-architecture.json
      screens/
      task-flows/
      forms/
      design-system.json
  schemas/              # JSON schemas for validation
```

## Current phase

{CURRENT_PHASE} — update this as the project progresses.
