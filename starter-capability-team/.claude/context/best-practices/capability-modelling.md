# Capability modelling best practices

Read by: Discovery Team, Journey Modelling Team

## Architectural philosophy

This pipeline produces a **capability-driven architecture** where each
capability is the deployment boundary — a self-contained domain with its
own data, logic, contracts, events, and test suite. This is a modular
monolith, not microservices. Each capability is sized to fit within an
AI agent's context window for development.

**Three layers:**
- **Runtime — Capability Layer**: domain modules owning data, exposing
  REST APIs, publishing/consuming events. Data status within capabilities
  implicitly represents journey progress.
- **Runtime — Platform Layer**: shared infrastructure (Event Bus, Schema
  Registry, Observability, Audit, Auth, Cache). Share the mechanism,
  isolate the state.
- **Design-time — Contract Layer**: API specs, event schemas, journey
  specs. Live in the repo and CI pipeline, consumed by channel UIs and
  AI development agents. Not runtime containers, not on C4 diagrams.
  The Schema Registry is the sole runtime exception.

**Key principles:**
- Share contracts, not implementations — each capability owns its own
  representation of shared concepts
- Capabilities communicate through domain events, not shared databases
- Journeys are design-time specifications, not runtime orchestration
- Verification independence (can I test this in isolation?) is the
  decomposition criterion, not deployment independence
- C4 diagrams show runtime only — capabilities + platform layer

## Capability decomposition

- Start from what the organisation **does**, not what systems it needs
- Each capability is a distinct area of institutional responsibility
- Each capability is also the **deployment boundary** — own database schema, own application, own test suite
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

If 3+ criteria met → promote to standalone capability. Document the
decision in the artefact.

Promotion has a direct deployment consequence:
- **Retained** sub-capabilities are part of the parent capability's
  deployable unit (same database schema, same application)
- **Promoted** sub-capabilities become independently deployable
  capabilities (own schema, own application, own test suite)

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

- Boundaries follow business capability lines, not technical convenience
- A capability owns its data — no shared databases between capabilities
- Cross-capability communication is explicit: synchronous via REST API, asynchronous via domain events on the event backbone
- High revision counts on a boundary signal it should be redrawn
- The Architect makes boundary decisions — the agent provides options analysis
- Each deployable capability has: own database schema, own application, own test suite, own service.yaml manifest

## Sequence principles

- A sequence is the end-to-end flow of data and control between participants and services during a journey
- Expressed as a Mermaid sequence diagram (`.mmd`) derived from structured JSON (`.json`) — the JSON is the source of truth, the Mermaid is the renderable representation
- Both files must be committed together and kept in sync
- For cross-capability journeys, the sequence diagram is the most architecturally significant artefact — it shows exactly how data moves from one capability's services to another's
- Every journey phase produces at least one sequence diagram
- Sequence diagrams are the primary input for cross-cutting service design and API contract definition
- The Architect on the Journey Modelling Team produces both the JSON and the Mermaid representation at step 12

## C4 architecture principles

- The C4 workspace (`architecture/c4-workspace.dsl`) is a single Structurizr DSL file that is the source of truth for all architecture diagrams
- It is a **living artefact** — not baselined, continuously updated across all phases
- **C4 shows runtime only** — capabilities (deployment units) sitting on the platform layer. No contract layer on the diagrams. API specs, journey specs, and regulatory constraints are design-time artefacts that live in the repo, not runtime containers.
- **System Context (L1)**: produced by Discovery Team at step 5. Shows the system boundary, system users (personas), and external systems. Does NOT show developers or AI agents — those are development concerns, not runtime.
- **Container (L2)**: capabilities as deployment units on top of the platform layer, with dependency arrows flowing downward. One container per deployable capability (retained sub-caps are internal, promoted sub-caps are separate containers). Platform containers: Event Bus, Schema Registry, Observability, Audit Pipeline, Auth, Cache.
- **Component (L3)**: produced by Journey Modelling Team after each journey. One component diagram per capability, showing internal structure derived from service boundaries and data model entities. Components connect to platform containers (Event Bus, Schema Registry, Audit Pipeline, Observability).
- Every element in the C4 workspace must trace to a JSON artefact: personas to `personas/*.json`, containers to `service-map.json`, components to `service-boundaries.json`, relationships to `api-contracts/*.openapi.json`
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
