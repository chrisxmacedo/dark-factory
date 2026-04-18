# Process improvements

Generalised learnings from running the capability pipeline. These inform
the scaffold scripts, validation scripts, team instructions, and review
gates.

## Pre-creation enforcement (scaffold)

1. **Global sequential IDs** — phase IDs (PH-NNN), entity IDs (ENT-NNN),
   and event IDs (EVT-NNN) must be globally sequential across all
   journeys. Journey-specific prefixes (PY-, BPH-, FR-PH-, ENT-B,
   EVT-P) cause inconsistency and break cross-references. The scaffold
   script scans all existing artefacts to assign the next available IDs.

2. **Template files** — the scaffold pre-creates template JSON files with
   the correct structure. The modelling agent overwrites them with full
   content but keeps the structure. This prevents structural drift
   between journeys.

3. **Manifest file** — each journey directory contains a `_manifest.json`
   with the ID ranges and format rules. The modelling agent MUST read
   this before producing any artefact.

4. **Format rules in manifest** — `owned_entities` must be plain ID
   strings (`"ENT-012"`), never annotated (`"ENT-012 (Name)"`). Same
   for `published_events` and `service_ids`. This enables deterministic
   validation.

## Post-creation validation

5. **Central model sync verification** — after updating the central
   event catalogue or service map, the agent must read the file back to
   confirm the update was applied. Silent write failures have been
   observed where the event catalogue was not updated despite the agent
   reporting success.

6. **Cross-capability communication validation** — sequence diagrams
   (both JSON and Mermaid) must be validated for synchronous calls
   between services in different capabilities. The only valid
   cross-capability communication is async events via the Event Bus.
   The `validate-sequences.py` script enforces this deterministically.

7. **Entity ownership validation** — every entity in the data model must
   have exactly one owning service declared in `service-boundaries.json`.
   Unowned entities are a bug.

8. **Sequence diagram pairing** — every `.json` sequence diagram must
   have a corresponding `.mmd` Mermaid file, and vice versa. Unpaired
   files indicate incomplete work.

## Architectural classifications

9. **Channel services are not capabilities** — services that act as a
   frontend/BFF layer (e.g. Digital Channels, Online Banking, Mobile
   App) sit outside the system boundary. They are allowed to call any
   capability's REST API synchronously. They must be classified as
   `channel` in service-dependencies.json, not mapped to a capability.

10. **Notification is a platform service** — notification delivery is
    shared infrastructure, not a business capability. If it were a
    capability, every other capability would need async events just to
    send a notification, which adds unnecessary complexity. Classify as
    `foundation` in service-dependencies.json.

11. **Platform services are invisible to cross-capability checks** —
    calls to/from platform services (IAM, Event Bus, Audit, Observability,
    Notifications, etc.) are not cross-capability violations. They are
    shared infrastructure.

## Communication model (four valid paths only)

There are exactly four ways a service can be reached:

1. **Channel → Capability API** — synchronous REST. The channel (web
   portal, mobile app, internal tooling, branch terminal) calls the
   capability's published REST API. The capability routes internally
   to whatever service handles the request. The channel never addresses
   a service directly — it only sees the capability's API surface.

2. **Event Bus → Capability** — async event consumed by a capability's
   event consumer. The capability routes internally to the right
   service. This is the sole mechanism for cross-capability communication.

3. **Service → Service (within same capability)** — direct method call,
   shared DB, internal REST/gRPC, internal queue. Internal implementation
   detail, invisible outside the capability boundary.

4. **Service → Platform service** — any service can call platform
   infrastructure (IAM, Audit, Observability, Cache, Schema Registry,
   Notifications). These are shared mechanisms.

No other communication paths exist. Services are never directly
addressable from outside their capability.

Consequences for artefacts:
- **API contracts are per-capability, not per-service.** A capability
  exposes one API surface. Internal service routing is an L3 concern.
- **Sequence diagrams show Channel → Capability API**, never
  Channel → Service or Persona → Service. The persona uses a channel;
  the channel calls the capability.
- **Personas never appear calling services directly** in sequence
  diagrams. A credit analyst uses an internal portal (channel) which
  calls the capability's API.

## Error handling

12. **Agents must report failures immediately** — if a file write fails,
    a central model update conflicts, or a tool call errors, the agent
    stops and reports to the Capability Lead. No silent continuation with
    incomplete artefacts. No partial central model updates.

13. **Validation runs after every journey** — the Capability Lead runs
    `validate-journey.py` and `validate-sequences.py` after each journey
    model is completed. Failures block Gate 2.

13b. **Central model entity files are the most commonly missed update.**
    The agent consistently updates service-map.json and event-catalogue.json
    but forgets to create individual entity files in central-model/entities/.
    Resolved by `sync-central-model.py` — it creates missing entity files
    automatically from the journey's data-model.json. The Journey Modelling
    Team runs this before signalling JOURNEY MODEL COMPLETE.

13c. **Annotated IDs persist despite manifest rules.** The agent
    sometimes writes `"ENT-036 (LetterOfCredit)"` in published_events
    or owned_entities despite the manifest saying plain IDs only.
    Resolved by `cleanup-ids.py` — run by the Journey Modelling Team
    before `sync-central-model.py`.

## Data transformation specifications

18. **The pipeline has a data transformation gap.** The data model
    describes data at rest. Sequence diagrams show call order. Event
    catalogues show payload schemas. But none of them capture how data
    is transformed as it flows. Four transformation types are missing:

    a. **Inbound event mapping** — when a capability consumes an event,
       how does it map the event payload to its own internal entities?
       E.g. Compliance consumes AccountOpened → maps to KycMonitoringRecord.
       Add a `maps_to` section to consumed_events in service-boundaries.

    b. **Outbound event derivation** — when a capability publishes an
       event, which entity fields produce which payload fields? What is
       included, excluded, masked, computed? Add a `derived_from` section
       to each event in the event catalogue.

    c. **API response projection** — how does the stored entity map to
       the API response? Especially field-level projections per persona/
       entitlement. The OpenAPI spec shows the shape but not the mapping.
       Add transformation notes to API contract response schemas.

    d. **Cross-entity derivation** — computed fields that span multiple
       entities within a capability. E.g. affordability_result derived
       from gross_income + committed_expenditure + stress_test_rate.
       Add a `computed_from` section to derived fields in the data model.

    This is an L3 (component) concern — internal to the capability. The
    transformations belong in extensions to existing artefacts (event
    catalogue, service boundaries, API contracts, data model) rather
    than a separate artefact type.

## Sequence diagram and API contract rules

14. **Personas never call services or capabilities directly** — in
    sequence diagrams, personas interact through a channel. Show
    `Persona → Channel → Capability API`, never `Persona → Service`.
    A credit analyst using an internal tool is using a channel.

15. **Sequence diagrams show capability boundaries** — show
    `Channel → CAP-002 API`, not `Channel → SVC-005`. The internal
    routing from capability API to service is an L3 concern.

16. **API contracts are per-capability, not per-service** — each
    capability exposes one API surface. The first journey that touches
    a capability creates its contract; subsequent journeys extend it.
    Internal service routing is not documented in the API contract.

17. **Every capability touched by a journey needs an API contract** —
    if a capability appears in the journey's service boundaries, it
    must have a corresponding API contract documenting its published
    REST surface for channels.

## Learnings from full pipeline run (30 journeys)

19. **Early journeys set the quality bar.** The first 5 journeys
    (modelled before scripts and standards existed) required full
    remediation afterwards — ID format renames, cross-capability
    violation fixes, central model sync. Later journeys (modelled
    with scaffold + manifest + validate loop) passed first time or
    with minor fixes. Invest in tooling before the first journey.

20. **Central model entity sync is the #1 failure mode.** Across 30
    journeys, the agent forgot to create central-model/entities/ files
    in ~30% of runs. The sync-central-model.py script eliminates this
    entirely. Never rely on the agent for deterministic file operations.

21. **Annotated IDs persist despite explicit instructions.** The agent
    writes `"ENT-012 (MortgageApplication)"` in ~20% of runs despite
    manifest rules saying plain IDs only. cleanup-ids.py runs after
    every journey. Accept this as a known agent behaviour and script
    around it.

22. **Sequence diagram JSON and Mermaid diverge.** The agent sometimes
    produces only the Mermaid (.mmd) without the JSON, or vice versa.
    The validator catches this. In some cases the JSON steps array was
    empty (stub file). Require both files and validate both have content.

23. **Programme Lead cannot persist across many journeys.** The
    orchestrating agent hits context or rate limits after 2-3 journeys.
    Design for re-spawn: the Programme Lead reads pipeline state from
    the artefact directory (which journeys have models) rather than
    maintaining in-memory state.

24. **API contracts should be per-capability, not per-service.** Early
    journeys produced one OpenAPI per service (retail-banking-core,
    customer-onboarding, kyc-aml). Later journeys correctly produced
    one per capability (retail-banking, commercial-banking). The first
    approach leaks implementation detail; the second matches the
    architecture (channels call capabilities, not services).

25. **Cross-capability async violations are always in JSON sequence
    files, rarely in Mermaid.** The Mermaid files tend to show the
    correct event flow because the visual notation makes violations
    obvious. The JSON files use raw service IDs where the capability
    boundary isn't visible. The validator catches both but the JSON
    files need more attention.

## Pipeline ordering constraints

18b. **Scaffolds must be sequential.** The scaffold script assigns
    globally sequential IDs by scanning existing artefacts. If two
    journeys are scaffolded before either writes artefacts, they get
    overlapping ID ranges. Always scaffold → model → validate one
    journey at a time, or scaffold with reserved ID blocks if parallel
    modelling is needed.

## Script inventory

| Script | Purpose | Run by | When |
|--------|---------|--------|------|
| `scaffold-journey.py` | Creates directory, manifest, templates with next available IDs | Capability Lead | Before spawning Journey Modelling Team |
| `cleanup-ids.py` | Strips annotated IDs from service-boundaries (ENT-012 (Name) → ENT-012) | Journey Modelling Team | After steps 7-13, before signalling complete |
| `sync-central-model.py` | Copies entities to central-model/entities/, appends events to catalogue, merges service map | Journey Modelling Team | After cleanup, before signalling complete |
| `validate-journey.py` | Checks files, ID formats, entity ownership, central model sync | Review Team (Stage 1) | First action when reviewing a journey |
| `validate-sequences.py` | Checks sequence diagrams for cross-capability sync violations | Review Team (Stage 1) | After validate-journey passes |
| `validate-central-model-impact.py` | Lists prior journeys whose artefacts reference entities/events touched by the current journey | Capability Lead | After `sync-central-model.py`, before Gate 2. Informational, not blocking. |
| `validate-data-integrity.py` | Deep structural integrity check — traces data flow from entity fields through event payloads through consumed mappings through API contracts. Surfaces field references that don't resolve. | Review Team (Stage 1) | After validate-sequences passes. The most thorough check — catches 80% of issues that would block a developer. |
| `generate-event-schemas.py` | Generates Avro schema files (.avsc) from event catalogue payload definitions. One file per event, organised by topic. Includes CloudEvents envelope. | Capability Lead | After all journeys complete (or periodically). Deterministic — no reasoning needed. |
