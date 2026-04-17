# Event catalogue and event design best practices

Read by: Journey Modelling Team (step 13)

## Events are facts, not commands

- Past tense names: `SettlementCompleted`, `AccountOpened`,
  `LoanDecided`.
- Never imperative: no `CompleteSettlement`, `OpenAccount`,
  `DecideLoan`.
- An event describes what **happened**. Commands (requests to do
  something) are internal to a capability and are not events.

## Required fields per event

- `event_id` — global sequential ID (EVT-NNN, from the journey
  manifest)
- `name` — PascalCase past tense
- `source_service` — the single publishing service
- `source_entity` — the entity whose state change triggered the event
- `trigger` — the specific state transition that emits it
- `journey_phase` — the phase(s) in which it fires
- `payload_schema` — full JSON schema
- `derived_from` — which entity fields produce which payload fields
  (see `data-modelling.md` — "Outbound event derivation")
- `consumers` — list of consuming services (across capabilities)
- `ordering_guarantees` — e.g. per-aggregate ordered, global FIFO,
  unordered
- `topic` — routing topic
- `data_classification` — public | internal | confidential | regulated
- `worm_audit_pipeline` — boolean
- `retention` — duration
- `cloudevents_type` — CloudEvents `type` attribute

## Cross-capability vs intra-capability events

- **Cross-capability events** are the integration contract — they are
  consumed by other capabilities and cross the Event Bus.
- **Intra-capability events** may exist (internal pub/sub) but are not
  part of the cross-capability contract. Catalogue them only if they
  have external observers.

## Versioning

- Payload schemas are additive — add fields, never rename or remove
  within a major version.
- A breaking change creates a new event (e.g. `AccountOpenedV2`) —
  the old event continues to flow for consumers that haven't migrated.
- Version info is part of the CloudEvents `type` attribute.

## Projections and the transparency model

- Public events are a projection of internal events — exclude PII,
  internal identifiers, and draft states.
- The projection rule is documented in the event's `derived_from`
  section.

## Consumer hygiene

- A consumer must be declared with its mapping (`maps_to` — see
  `data-modelling.md`).
- Consumers never assume ordering across aggregates unless the
  `ordering_guarantees` say so.
- Consumers are idempotent — the same event may arrive more than
  once.

## Anti-patterns

- Command-shaped events (`OpenAccount`, `DecideLoan`) — they couple
  publishers to consumers.
- Events that carry everything — payloads should contain what a
  consumer needs, not the whole entity.
- Anonymous consumers — every consumer must be declared so the
  dependency graph is complete.
- Events published by multiple services — each event has exactly one
  source.
