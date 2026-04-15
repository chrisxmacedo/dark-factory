# Capability modelling best practices

Read by: Discovery Team, Journey Modelling Team

## Capability decomposition

- Start from what the organisation **does**, not what systems it needs
- Each capability is a distinct area of institutional responsibility
- Capabilities are stable over decades — they change only when the mandate changes
- Technology choices are derived from capability requirements, never the reverse

## Sub-capability promotion test

Every sub-capability must be evaluated against four criteria:
1. Distinct external participants?
2. Separate regulatory framework?
3. Distinct lifecycle (end-to-end phases that don't map onto the parent)?
4. Independent scalability requirements?

If 3+ criteria met → promote to standalone capability. Document the
decision in the artefact.

## Shared sub-capabilities

When a sub-capability appears in more than one capability:
- Record in `foundation/shared-sub-capabilities.json`
- Document the architectural resolution (shared service, library, or duplicated)
- This decision has downstream implications for service boundaries

## Journey modelling

- Journeys are the unit of work in Phase C — one journey = one cycle through steps 7-13
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
- A service owns its data — no shared databases
- Cross-service communication is explicit (API or event)
- High revision counts on a boundary signal it should be redrawn
- The Architect makes boundary decisions — the agent provides options analysis

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
- **System Context (L1)**: produced by Discovery Team at step 5. Shows the system boundary, all personas, and external system integrations. Containers follow capability domain lines — one container per technical service, not per feature
- **Container (L2)**: initial draft by Discovery Team at step 5 (one container per technical service). Refined by Journey Modelling Team after each journey (inter-container relationships from API contracts). Completed by UI Specification Team (portal containers added with frontend-to-backend relationships)
- **Component (L3)**: produced by Journey Modelling Team after each journey. One component diagram per container, showing internal structure derived from service boundaries and data model entities
- Every element in the C4 workspace must trace to a JSON artefact: personas to `personas/*.json`, containers to `service-map.json`, components to `service-boundaries.json`, relationships to `api-contracts/*.openapi.json`
- The Review Team validates C4-to-JSON consistency at every review

## API contract principles

- OpenAPI specification for every service-to-service interaction
- Both internal APIs (between services) and external APIs (for participants)
- Contracts include: authentication model, rate limits, error responses
- Sequence diagrams show the call flow for each journey phase

## Event catalogue principles

- Events are facts about what happened, not commands about what should happen
- Event names use past tense: `SettlementCompleted`, not `CompleteSettlement`
- Every event has: source service, payload schema, consumers, ordering guarantees
- Events enable the transparency model — public events are a projection of internal events
