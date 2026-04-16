# Capability modelling best practices

Read by: Discovery Team, Journey Modelling Team

## Architectural philosophy

See `context/architecture-specification.md` for the full specification.
The key points that inform capability modelling:

- A **capability** is a business domain grouping containing one or more
  independently deployable technical services. It is NOT a single service.
- A **service** is a component inside a capability — an API, worker,
  processor, or scheduled job. Services within a capability may share
  databases and communicate by whatever means suits the domain (direct
  method calls, shared DB, internal REST/gRPC, internal queues).
- **Cross-capability communication is exclusively asynchronous events.**
  No capability calls another capability's API. No shared databases
  across capabilities. The Event Bus is the sole integration mechanism.
- **Channel UIs** sit outside the system boundary and call capability
  REST APIs synchronously. This is not cross-capability communication.
- **Capabilities are sized to fit an AI agent's context window.** This
  is the primary decomposition constraint.
- **Journey state is implicit in capability data.** No central
  orchestrator. The data IS the state.
- **C4 L2 shows capabilities; L3 shows services within a capability.**
  Design-time artefacts do not appear on C4 diagrams.

## Capability decomposition

- Start from what the organisation **does**, not what systems it needs
- Each capability is a business domain grouping containing one or more
  services that together fulfil that domain's responsibilities
- Capabilities own their data — one or more databases or schemas,
  invisible to other capabilities
- Capabilities are stable over decades — they change only when the mandate changes
- Technology choices are derived from capability requirements, never the reverse
- **Research before drafting**: the agent must research the market landscape
  for each capability domain before producing artefacts. A capability list
  derived only from the org chart produces a shallow architecture. The
  research captures: competitive landscape (who does what, what's being
  unbundled/re-bundled), regulatory horizon (what's coming in 2-3 years),
  build-vs-buy assessment (what platforms exist, what must be in-house),
  and sub-capability boundary evidence (market structure informs the
  promotion test)
- Each capability artefact includes a `market_context` section capturing
  the research findings that informed its design

## Sub-capability promotion test

Every sub-capability must be evaluated against four criteria:
1. Distinct external participants?
2. Separate regulatory framework?
3. Distinct lifecycle (end-to-end phases that don't map onto the parent)?
4. Independent scalability requirements?

If 3+ criteria met → promote to a separate service within the
capability. Document the decision in the artefact.

Promotion determines the service structure within a capability:
- **Retained** sub-capabilities are implemented as internal modules
  within an existing service — shared database, direct method calls
- **Promoted** sub-capabilities become their own service (own repo,
  own deployment unit) but remain inside the capability boundary. They
  may share databases with other services in the same capability or
  have their own — this is an internal decision.

Promotion does NOT mean leaving the capability. A promoted
sub-capability is still part of its parent capability. It becomes a
separate service, not a separate capability. Cross-capability
communication rules do not apply within the capability boundary.

The market research from Step 1 provides evidence for promotion:
- Specialist providers exist → evidence for distinct participants
  and independent scalability
- Separate regulation governs it → evidence for separate regulatory
  framework
- The market treats it as a distinct product → evidence for distinct
  lifecycle

## Shared sub-capabilities

When a sub-capability appears in more than one capability:
- Record in `foundation/shared-sub-capabilities.json`
- Document the architectural resolution: share contracts, not implementations
- Each capability owns its own representation of shared concepts (e.g.
  Billing has BillingCustomer, not a shared Customer model)
- Reference data is published by whichever capability is authoritative
  and consumed as read-only by others via domain events
- This decision has downstream implications for service boundaries

## Journey modelling

- Journeys are the unit of work in Phase C — one journey = one cycle through steps 7-13
- **Journeys are design-time specifications, not runtime orchestration** — they define steps, data requirements, and valid transitions, but nothing reads them at runtime
- The channel UI uses journey specs to build the interaction flow; AI agents use them to understand how capabilities compose
- Data status within capabilities implicitly represents journey progress — a KYC record with status "pending" means the onboarding journey is in progress. No separate state machine needed.
- Actual coordination happens through capabilities reacting to each other's published events
- Every journey must have: happy path, at least one alternative path, at least one exception path
- Phases within a journey are the natural breakpoints — each phase can have different actors, different governance rules, different NFRs
- A journey crosses service boundaries — that's what makes it a journey, not a feature
- **Cross-capability journeys**: A journey may span multiple capabilities. This is expected — a settlement instruction journey might touch monetary policy, payment operations, and reporting capabilities. The sequence diagram makes these cross-capability data flows explicit
- When a journey spans capabilities, the sequence diagram is the primary artefact that reveals integration points — which services in which capability domains need to communicate, what data crosses the boundary, and in what order

## Data model principles

- Entities are derived from the journey, not invented
- Every entity must be reachable from at least one journey phase
- Every field must have a type, validation rule, and source (which step/journey introduced it)
- Orphan entities (no journey reference) are a bug
- The central model is the aggregation of all journey-level models — it grows incrementally

## Service boundary principles

- The capability boundary is the hard boundary — no shared databases
  across capabilities, no synchronous calls between capabilities
- Within a capability, services communicate by whatever means suits the
  domain (direct method calls, shared database, internal REST/gRPC,
  internal queues) — this is an internal technical decision
- Cross-capability communication is exclusively asynchronous domain
  events via the Event Bus. No capability calls another capability's API.
- High revision counts on a capability boundary signal it should be redrawn
- The Architect makes boundary decisions — the agent provides options analysis
- Each capability has: its own data (one or more databases/schemas),
  its own services, its own event contracts, its own REST API surface

## Data transformation principles

- The data model describes data **at rest**. Transformations describe
  how data changes as it **flows** between capabilities and to channels.
- **Inbound event mapping**: when a consumed_event is declared in
  service-boundaries.json, include a `maps_to` section specifying which
  entity fields the event payload maps to in the consuming capability.
- **Outbound event derivation**: in the event catalogue, each event
  should include a `derived_from` section listing which entity fields
  produce which payload fields, including masking and exclusion rules.
- **API response projection**: in API contracts, response schemas
  should note which entity fields are projected, especially where
  field visibility varies by persona/entitlement.
- **Computed fields**: in the data model, fields that are derived from
  other fields should include a `computed_from` section listing the
  source fields and the derivation logic.

## API contract principles

- API contracts are **per-capability, not per-service** — each capability
  exposes one published REST API surface to channels
- Internal routing from the capability API to its services is an L3
  (component) concern, not documented in the API contract
- The first journey that touches a capability creates its API contract;
  subsequent journeys extend it
- API contracts must include example request/response bodies, error
  responses, auth requirements, and response projection notes
- Channels never address a service directly — only the capability API

## Sequence principles

- A sequence is the end-to-end flow of data and control between
  participants, channels, and capabilities during a journey
- **Personas never call services or capabilities directly** — they
  interact through a channel (web portal, mobile app, internal tooling).
  Show `Persona → Channel → Capability API`, never `Persona → Service`
- Expressed as a Mermaid sequence diagram (`.mmd`) derived from
  structured JSON (`.json`) — the JSON is the source of truth
- Both files must be committed together and kept in sync
- Sequence diagrams show **capability boundaries**, not service
  boundaries. Show `Channel → CAP-001 API`, not `Channel → SVC-001`
- For cross-capability journeys, the sequence diagram shows events
  flowing via the Event Bus between capabilities
- Every journey phase produces at least one sequence diagram
- Sequence diagrams are the primary input for cross-cutting service design and API contract definition
- The Architect on the Journey Modelling Team produces both the JSON and the Mermaid representation at step 12

## C4 architecture principles

- The C4 workspace (`architecture/c4-workspace.dsl`) is a single Structurizr DSL file that is the source of truth for all architecture diagrams
- It is a **living artefact** — not baselined, continuously updated across all phases
- **C4 shows only what runs in production.** Design-time artefacts (API specs, journey specs, regulatory constraints) do not appear on C4 diagrams.
- **System Context (L1)**: the system boundary, actual system users (personas), and external systems. AI agents do not appear — development concern, not system user.
- **Container (L2)**: two boundary groupings within the system:
  - **Capabilities boundary** — each capability appears as a container. Arrows between capabilities are labelled with the async events they exchange. No synchronous arrows between capabilities.
  - **Platform boundary** — sits below capabilities. Event Bus, Schema Registry, Observability, Audit Pipeline, Auth, Cache. Dependency arrows flow downward from capabilities to platform.
  - The Contract Layer does not appear on L2.
- **Component (L3)**: zooms into a single capability. Shows internal services, inbound ports (event consumers), outbound ports (event publishers), API controllers, data stores, platform adapters. External dependencies shown are the platform containers the capability connects to at runtime.
- Every element traces to a JSON artefact: personas to `personas/*.json`, capabilities to `service-map.json`, components to `service-boundaries.json`
- The Review Team validates C4-to-JSON consistency at every review

## API contract principles

- OpenAPI specification for every service-to-service interaction
- Both internal APIs (between services) and external APIs (for participants)
- Contracts include: authentication model, rate limits, error responses
- Sequence diagrams show the call flow for each journey phase

## Service dependency principles

- Every service is assigned a build tier (T0-T4) based on upstream dependencies
- T0 Foundation (no deps) → T1 Core Infrastructure → T2 Business Services → T3 Composite → T4 Overlay
- Each dependency is classified as **hard** (sync, immediate failure) or **soft** (async/degradable)
- The build order is regulatory-driven: compliance prerequisites (KYC, sanctions, fraud) must be live before payment or onboarding services
- `service.yaml` is the authoritative manifest per service: id, tier, depends_on (with protocol and criticality), topics_produced, topics_consumed, data_classification, secrets with rotation_days
- The dependency graph + criticality drives the blast radius visualiser and zero-trust policy enforcement

## Observability principles

- OTel Collector is the sole telemetry ingestion point — services never connect to stores directly
- PII scrubbing happens once, centrally, in the collector pipeline
- Four stores with incompatible requirements: Log (90d, engineering), Trace (30d, engineering), Metrics (13mo, engineering), Audit (7yr WORM, auditor-only)
- Per-service instrumentation checklist (6 items) is a mandatory gate before a service is marked Done
- Logging schema extensions are mandatory per service category (API/edge, core domain, payment, identity/auth, async/event, admin/config, batch)
- `service.yaml` data_classification drives SIEM alert severity — CVE on a pii/financial service triggers elevated alert

## Security principles

- Zero-trust model: service.yaml declares allowed calls, service mesh enforces, diff between policy and observed calls is a security signal
- mTLS between all services via service mesh with workload identity
- Data classification (public → regulated) determines encryption, audit logging, and additional controls
- Audit log pipeline is physically separate from operational telemetry — incompatible retention/access requirements
- Audit store must use immutable/WORM storage — admin cannot delete within retention period

## Event catalogue principles

- Events are facts about what happened, not commands about what should happen
- Event names use past tense: `SettlementCompleted`, not `CompleteSettlement`
- Every event has: source service, payload schema, consumers, ordering guarantees
- Events enable the transparency model — public events are a projection of internal events
