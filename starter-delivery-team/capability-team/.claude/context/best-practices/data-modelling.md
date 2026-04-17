# Data modelling best practices

Read by: Journey Modelling Team (step 10 — data model; and transformations
across steps 11-13)

## Data at rest

- Entities are derived from the journey, not invented.
- Every entity must be reachable from at least one journey phase.
- Every field must have a type, validation rule, and source (which
  step/journey introduced it).
- Orphan entities (no journey reference) are a bug.
- The central model is the aggregation of all journey-level models —
  it grows incrementally.
- Entity names are PascalCase. Field names are snake_case.

## Ownership

- Every entity has exactly one owning service (declared in
  `service-boundaries.json`). An unowned entity is a bug caught by
  `validate-journey.py`.
- Services within a capability may share a database. Services across
  capabilities never share a database — if the same concept appears in
  two capabilities, each owns its own representation.

## Data in flight — transformations

The data model describes data at rest. Four transformation types
capture how data changes as it flows. Each type belongs in a specific
artefact — there is no separate "transformations" artefact.

### Inbound event mapping

When a capability consumes an event, it maps the event payload to its
own internal entities.

- **Where:** `service-boundaries.json` → `consumed_events[].maps_to`
- **Example:** Compliance consumes AccountOpened → maps to
  KycMonitoringRecord fields (customer_id → subject_id,
  opened_at → monitoring_start, etc.)

### Outbound event derivation

When a capability publishes an event, its payload is derived from entity
fields. The catalogue records which fields are included, excluded,
masked, or computed.

- **Where:** `events/*.json` → `events[].derived_from`
- **Example:** LoanDecided derived from LoanApplication fields:
  amount, decision, decided_at (exclude: applicant SSN, internal notes).

### API response projection

How a stored entity maps to an API response, especially field-level
projection per persona or entitlement.

- **Where:** API contract response schemas → projection notes per endpoint
- **Example:** Retail persona sees `account.balance, account.currency`.
  Advisor persona additionally sees `account.internal_risk_flag`.

### Cross-entity derivation

Computed fields that span multiple entities within a capability.

- **Where:** `data-model.json` → field-level `computed_from`
- **Example:** `affordability_result` computed from `gross_income +
  committed_expenditure + stress_test_rate`.

## Central model aggregation

After a journey's steps 7-13 complete, `sync-central-model.py` copies
entities to `central-model/entities/`, appends events to the catalogue,
and merges the service map.

- New entities: copy the journey's entity file as-is.
- Existing entities: merge new fields. Conflicts (field exists with
  different type or validation) block the sync — resolve via a design
  decision in the journey artefact, then re-run.
- Every merge decision is recorded in the journey's `design_decisions`.

## Anti-patterns

- Copying a field from one entity into another because "it's needed
  here too" — use events and projections instead.
- Introducing an entity in a journey without adding any fields to it
  (stub entity). If a journey does not populate an entity, it should
  not be declared in that journey.
- Normalising prematurely — in early journeys, simple structures are
  often right. Split later if needed.
- Modelling identifiers without an explicit type and format rule.
