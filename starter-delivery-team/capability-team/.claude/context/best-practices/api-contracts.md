# API contract best practices

Read by: Journey Modelling Team (step 12)

## Per capability, not per service

- **API contracts are per-capability, not per-service.** Each capability
  exposes one published REST API surface to channels.
- Internal routing from the capability API to its services is an L3
  (component) concern, not documented in the API contract.
- The first journey that touches a capability creates its API contract;
  subsequent journeys extend it.

## Every capability touched needs a contract

If a capability appears in the journey's service boundaries, it MUST
have a corresponding API contract documenting its published REST surface
for channels. Platform services (IAM, Event Bus, Audit) are exempt.

## Required content per endpoint

- Path, method, summary
- Authentication model (required scopes, auth flow)
- Rate limits (per persona type / channel)
- Request body schema with example
- Response body schema with example
- Error responses with schemas (4xx + 5xx)
- **Projection notes** — which entity fields appear, and any per-persona
  field visibility differences (see `data-modelling.md` — "API response
  projection")

## Cross-reference hygiene

- Response schemas reference central-model entities by path. From
  `artefacts/models/{slug}/api-contracts/{capability}.openapi.json`,
  that is three levels up:
  `$ref: "../../../central-model/entities/Customer.json"`
- All `$ref` paths must resolve. `validate-journey.py` catches broken
  refs.
- Field names in API schemas match the entity field names exactly —
  rename at the boundary if the external name must differ, and document
  the mapping in the projection notes.

## What API contracts are NOT

- Not a runtime enforcement mechanism (the application framework
  validates at runtime).
- Not a description of internal service-to-service calls.
- Not a mechanism for cross-capability communication. Cross-capability
  integration is exclusively events.

## Anti-patterns

- Per-service API contracts leaking internal structure outside the
  capability.
- Endpoints without example bodies — forces consumers to guess shapes.
- Silent field projection (returning more or fewer fields than
  documented per persona).
- Using the API contract to describe internal orchestration — that's
  a sequence diagram concern.
