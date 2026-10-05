# capability-meta-model

A sector-neutral JSON Schema meta-model for describing capabilities, their services, the journeys that exercise them, and the contracts between them. Intended as the substrate from which sector-specific packs (banking, energy, health, etc.) are built.

This folder is the template. A pack takes these schemas, supplies concrete content that validates against them, and publishes a reference implementation for its sector.

## The shape of a capability

A capability is a mandate-backed business function. It is the primary unit of architectural decomposition in this model. Every capability file carries a six-part bundle:

1. **Mandate** — the statutes, regulations, policies, charters, or strategic decisions that explain why the organisation holds this capability.
2. **Competitive landscape** — where the organisation sits relative to others offering the same capability: table stakes, differentiators, disruptors, unbundling, rebundling, switching drivers.
3. **Regulatory horizon** — what is currently in force, what is coming, and what enforcement signals matter.
4. **Build-vs-buy** — which elements must be built in-house and which should be bought from vendors.
5. **Sub-capabilities** — the bounded areas of responsibility that compose the capability, each with a promotion test.
6. **Design decisions** — architectural choices with rationale, alternatives considered, and why those alternatives were rejected.

Revenue model is intentionally not part of the bundle. The capability file describes what the capability is; commercial analysis is a separate concern.

## The promotion test

Every sub-capability carries a four-criterion test:

1. **Distinct participants** — does it involve actors absent from the parent's other sub-capabilities?
2. **Separate regulatory framework** — is it governed by a materially distinct body of rules?
3. **Distinct lifecycle** — does it have phases of operation that do not appear elsewhere?
4. **Independent scalability** — do its demand drivers vary independently of the parent capability?

Each criterion is a boolean. `criteria_met` is the count of trues. The prima facie rule is: if three or more are true, promote the sub-capability to a standalone capability. If fewer, retain.

Overrides are permitted. A sub-capability that scores 3 of 4 can still be retained, and one that scores 2 can still be promoted — but the parent capability's `design_decisions` must record a decision explaining the override. No silent deviation.

## Architectural rules the meta-model enforces

- **Channels talk to capabilities via REST.** Every capability publishes an OpenAPI spec. Customer-facing systems, partner systems, and other external consumers reach the capability through this contract.
- **Capabilities talk to each other via events, never REST.** Every capability publishes an AsyncAPI spec listing the events it emits on the shared bus. Other capabilities subscribe; they do not call the capability's REST API.
- **Every service has both contracts.** Each service inside a capability publishes its own OpenAPI spec (for intra-capability calls) and AsyncAPI spec (for events it publishes and consumes on the bus).
- **No shared sub-capabilities.** Every sub-capability belongs to exactly one parent capability. If two capabilities appear to need the same sub-capability, either promote it to a capability or accept that they are solving different problems that happen to sound alike. There is no "shared" resolution.
- **No shared databases, no shared entities, no shared codebases across capabilities.** If capability A needs data owned by capability B, A subscribes to B's events. Share contracts, not implementations.
- **Data stores are capability-scoped and first-class.** Every data store (DS-XXX) belongs to exactly one capability. A store may be shared between services within that capability, never across capabilities. Every entity is persisted in exactly one store. A store's data classification must equal or exceed the classification of every entity it holds.
- **Entities are capability-scoped, not journey-scoped.** The data model lives with the capability that owns it. Journeys reference entities by ID but do not define them.
- **Service boundaries are capability-scoped.** The service boundary map lives with the capability. Journeys reference services by ID but do not redefine their boundaries.
- **Events are capability-scoped.** The event catalogue lives with the capability whose services publish the events. Consumers from other capabilities reference events by ID.
- **Non-functional requirements are journey-scoped** for end-to-end behaviour (latency budget for the whole flow, regulatory SLAs). Per-service SLAs live on the `technical-service` spec for that service — they compose into the journey-level targets.
- **Sequence diagrams are journey-phase-scoped.** A journey may initiate many sequences; each is attached to a phase. There are no capability-level or service-level sequence diagrams in this meta-model.

## The eighteen schemas

Core schemas in `schemas/`:

- `capability.schema.json` — a capability file.
- `sub-capability.schema.json` — referenced from capability; defines the promotion test.
- `journey-inventory.schema.json` — the flat list of all journeys.
- `journey-detail.schema.json` — the detailed specification of a single journey, owned by the journey folder.
- `data-model.schema.json` — the entities owned by a capability (capability-scoped).
- `data-store.schema.json` — a persistence boundary inside a capability (capability-scoped). First-class artifact; every entity is stored in exactly one.
- `service-boundaries.schema.json` — the services composing a capability (capability-scoped).
- `service-dependencies.schema.json` — the system-wide service dependency map and build order.
- `persona.schema.json` — a type of actor.
- `technical-service.schema.json` — the canonical per-service definition, including per-service SLA and the data stores the service uses.
- `event.schema.json` — a single event on the bus.
- `event-catalogue.schema.json` — the events published by a capability (capability-scoped).
- `governance.schema.json` — the governance rules applicable to a capability (structure here, rule content in the pack).
- `nfr.schema.json` — end-to-end NFRs for a journey (journey-scoped).
- `observability-model.schema.json` — organisation-wide observability posture (system-level).
- `security-model.schema.json` — organisation-wide security posture (system-level).
- `api-manifest.schema.json` — indexes OpenAPI + AsyncAPI specs at capability or service scope.
- `sequence-manifest.schema.json` — indexes Mermaid sequence diagrams at journey-phase scope.

## Identifier conventions

Prefixes and formats are conventions, not hard requirements of the schemas. A pack may choose different prefixes; the regex patterns in the schemas will need matching pack-specific overrides.

| Prefix | Meaning | Format |
|---|---|---|
| `CAP-XXX` | Capability | 3 digits |
| `SUB-XXX` | Sub-capability | 3 digits |
| `JRN-XXX` | Journey | 3 digits |
| `PH-XXX` | Phase (within a journey) | 3 digits |
| `PER-XXX` | Persona | 3 digits |
| `CHN-XXX` | Channel | 3 digits |
| `SVC-XXX` | Service | 3 digits |
| `ENT-XXX` | Entity | 3 digits |
| `DS-XXX` | Data store | 3 digits |
| `EVT-XXX` | Event | 3 digits |
| `GOV-XXX` or `GOV-XXX-RYY` | Governance rule | 3 digits, optional sub-rule |
| `DD-XXX` | Design decision | 3 digits |
| `SEQ-XXX` | Sequence diagram | 3 digits |

## What the validator should enforce

A pack consuming this meta-model should validate (beyond pure JSON Schema):

- Every capability has at least one `mandate_source` entry.
- Every sub-capability's `criteria_met` equals the count of true booleans in the `promotion_test`.
- Every sub-capability whose `promoted` contradicts `criteria_met >= 3` has a matching entry in its parent capability's `design_decisions` explaining the override.
- Every `design_decision` has a non-empty `rationale`.
- Every journey `capabilities_touched` and `sub_capabilities_involved` ID resolves to an existing capability or sub-capability.
- Every `sub_capabilities_involved` ID belongs to one of the capabilities in the same journey's `capabilities_touched`.
- `cross_capability` is true iff `sub_capabilities_involved` spans more than one top-level capability.
- Every `depends_on_journeys` ID resolves to another journey in the inventory.
- Every journey-detail's `journey_id` matches the folder it lives in.
- Every phase ID referenced in `paths.happy_path.phases` resolves to a phase in the same journey-detail.
- Every `owned_entities` ID in a capability's `service-boundaries` is owned by exactly one service across the entire organisation.
- Every entity (`ENT-XXX`) appears in exactly one data store's `stored_entities` across the organisation.
- Every data store's `capability_id` matches the capability of every service in its `owning_services`, and of every entity it stores.
- Every data store's `data_classification` is greater than or equal to the classification of every entity it holds (`regulated` > `confidential` > `internal` > `public`).
- Every `data_stores` ID on a technical-service resolves to a data store whose `owning_services` contains that service.
- Every `published_events` ID in a service's boundaries resolves to an event in the capability's `event-catalogue`.
- Every capability has an `api-manifest` indexing at least one OpenAPI and one AsyncAPI spec.
- Every service has an `api-manifest` indexing at least one OpenAPI and one AsyncAPI spec.
- Every sequence in a `sequence-manifest` references a phase that exists in the same journey's `journey-detail`.
- No sub-capability appears in more than one capability (the no-shared-sub-capabilities rule).
- No entity is referenced as `owning_service` by a service in a capability other than its own.

## What pack authors add

A sector pack built on this meta-model contributes:

- Concrete capability files for the sector's capabilities.
- Concrete personas, channels, services.
- Concrete governance rules (UK statutes, sector regulators, etc.) matching the governance schema structure.
- Concrete journey definitions and their artifact folders.
- Sector-specific ID prefix overrides if required.
- Any pack-level extensions (additional fields, tighter enums).

Packs do not modify the schemas in this folder. If a schema change is needed, it is a change to the meta-model and affects every pack.
