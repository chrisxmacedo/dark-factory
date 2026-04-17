# JSON schemas

Schemas for the capability pipeline artefacts. Starter set — extend as
new artefact types are added.

The validator scripts (`validate-journey.py`, etc.) check file presence
and ID format. These schemas are the structural contract the **downstream
development pipeline** relies on when consuming artefacts.

| Schema | Applies to |
|--------|------------|
| `capability.schema.json` | `foundation/capabilities/*.json` |
| `persona.schema.json` | `foundation/personas/*.json` |
| `governance.schema.json` | `foundation/governance/*.json` |
| `technical-service.schema.json` | `foundation/technical-services/*.json` |
| `journey-detail.schema.json` | `models/{slug}/journey-detail.json` |
| `event.schema.json` | Items in `models/{slug}/events/event-catalogue.json` and `central-model/event-catalogue.json` |

## Adding a schema

1. Create `{artefact-type}.schema.json` here.
2. Reference it from `artefact-standards.md`.
3. Add a check to `validate-journey.py` (or a new validator) that loads
   the schema and validates every matching artefact.

## What schemas do NOT do

- They do not specify how the downstream dev team implements the
  artefact's runtime behaviour.
- They do not enforce cross-artefact consistency (IDs resolving across
  files). That is the job of the validator scripts.
