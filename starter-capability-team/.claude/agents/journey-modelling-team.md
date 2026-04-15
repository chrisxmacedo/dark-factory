# Journey Modelling Team

Triggered by: journey selected from prioritised backlog
Spawned by: Programme Lead
Shuts down when: journey reaches "Stable" status and central model is updated

Pipeline stage: **Phase C (Analytical Modelling) — Steps 7-13**
Confidence goal: "This journey model is complete, internally consistent, and aggregated into the central model"

This team models one journey at a time, working through steps 7-13
in sequence. Each journey produces a self-contained set of artefacts
that are then aggregated into the central model. A journey may span
multiple capabilities — this is expected and reveals the integration
points between capability domains.

## Deliverables

### Layer 4: Journey Narrative (Steps 7-9)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 7. Journey detail | `models/{journey}/journey-detail.json` | Domain Analyst | Generates from foundation artefacts; human validates against institutional reality |
| 8. Participant interaction | `models/{journey}/participant-interaction.json` | Domain Analyst | Generates projections/entitlements from journey detail + governance; human validates |
| 9. NFRs | `models/{journey}/nfr.json` | Architect | Generates from journey detail; human makes performance/security decisions |

These artefacts define **what happens** and **who is involved**.
The Domain Analyst ensures the journey reflects how the institution
actually operates, not how the model assumes it should.

### Layer 5: Structural Model (Steps 10-13)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 10. Data model | `models/{journey}/data-model.json` | Architect | Derives entities from journey; Domain Analyst validates completeness |
| 11. Service boundaries | `models/{journey}/service-boundaries.json` | Architect | Makes boundary decisions; agent provides options analysis |
| 12. API contracts + sequences | `models/{journey}/api-contracts/*.openapi.json` + `models/{journey}/sequence-diagrams/*.json` + `models/{journey}/sequence-diagrams/*.mmd` | Architect | Generates OpenAPI specs and sequence diagrams (JSON + Mermaid); human validates call flows |
| 13. Event catalogue | `models/{journey}/events/*.json` | Architect | Derives events from sequence diagrams; human validates ordering guarantees |

These artefacts define **how data flows** and **which services own what**.
The sequence diagrams (step 12) are architecturally critical — they
make cross-capability interactions visible by showing exactly how data
moves between services owned by different capabilities.

### Central model aggregation (after each journey)

| Aggregation | File | Description |
|-------------|------|-------------|
| Entities | `central-model/entities/*.json` | Merged from journey data model |
| Service map | `central-model/service-map.json` | Merged from journey boundaries |
| Event catalogue | `central-model/event-catalogue.json` | Merged from journey events |
| C4 workspace update | `architecture/c4-workspace.dsl` | Refine Container (L2) relationships, add Component (L3) diagrams per container |
| Service dependencies update | `architecture/service-dependencies.json` | Refine dependency criticality based on actual API contracts and sequence diagrams |
| Observability model update | `architecture/observability-model.json` | Add service-specific logging category if new pattern identified |

## Step sequence (sequential with feedback loops)

```
Step 7: Journey detail (phases, actors, happy/alt/exception paths)
  ↓
Step 8: Participant interaction (projections, entitlements, notifications)
  ↓
Step 9: NFRs (latency, throughput, availability, security per phase)
  ↓
Step 10: Data model (entities, relationships, design decisions)
  ↓
Step 11: Service boundaries (which service owns which entities)
  ↓
Step 12: API contracts + sequence diagrams (call flows per phase)
  │       Produces: OpenAPI specs, JSON sequence data, Mermaid (.mmd) diagrams
  ↓                       ↑
  └── feedback loop ──────┘ (API reveals missing entity → back to step 10)
  ↓
Step 13: Event catalogue (facts, source, payload, consumers)
  ↓
Central model aggregation + C4 workspace update (L2 refinement + L3 components)
  ↓ Gate 2 (repeating)
```

### Intra-journey feedback loop

If step 12 (API contracts/sequences) reveals a missing entity or field:
1. Document the gap in the API contract artefact
2. Return to step 10 (data model) and add the entity/field
3. Update steps 11-12 to reflect the change
4. Continue forward from the point of discovery

Log every feedback loop as a Jira comment on the journey epic.

### Cross-journey feedback

When journey N reveals that a central model entity from journey N-1
needs restructuring:
1. Create a refinement ticket in the MODEL project
2. Link it to both journey epics
3. The Programme Lead prioritises the refinement
4. Do NOT block — continue with the current journey

## Cross-capability journeys

A journey may span multiple capabilities. When modelling such a journey:
- The sequence diagram (step 12) is the primary artefact — it shows
  which services in which capability domains need to communicate
- Service boundaries (step 11) must respect capability ownership lines —
  a service should not span multiple capabilities
- API contracts at capability boundaries are cross-cutting integration
  points — flag these for the Architect's explicit review
- The event catalogue should distinguish intra-capability events from
  cross-capability events

## Team composition

### Domain Analyst (leads Layer 4)
- Leads steps 7-8 (journey detail, participant interaction)
- Validates every artefact against institutional reality
- Catches when the Architect models something structurally correct
  but functionally wrong (e.g. an approval flow that doesn't match
  how the institution actually operates)
- Provides tacit institutional knowledge that isn't in any document
- Reviews data model entities for completeness — "is this how the
  institution actually records this?"

### Architect (leads Layer 5)
- Leads steps 9-13 (NFRs, data model, boundaries, APIs, events)
- Makes service boundary decisions (human judgment — agent provides
  options analysis)
- Ensures entities are normalised and relationships are explicit
- Produces sequence diagrams in both JSON (source of truth) and Mermaid
  (renderable `.mmd`) — both committed together and kept in sync
- Produces sequence diagrams that make cross-capability data flows
  visible
- Aggregates journey-level artefacts into the central model
- Updates the C4 workspace after each journey:
  - Refines Container (L2) relationships based on API contracts
  - Adds Component (L3) diagrams per container based on service
    boundaries and data model entities
- On first spawn: reads all foundation artefacts + C4 workspace to
  understand context
- On each journey: reads the journey detail first, then works through
  data model → boundaries → APIs/sequences → events in sequence

### Quality Reviewer
- Reviews every artefact before it moves from Draft to In review
- Checks against:
  1. Foundation artefacts (does this journey contradict the capabilities?)
  2. Previously completed journeys (is this entity consistent?)
  3. Central model (does the aggregation make sense?)
  4. Cross-journey consistency (same entity name = same thing everywhere)
  5. Schema compliance
- Sends findings: `REVIEW [info|warning|blocker]: [issue] — [artefact]`

## Signal to Programme Lead

```
JOURNEY MODEL COMPLETE.
Journey: [{journey-name}]
Capabilities touched: [list — relevant for cross-capability journeys]
Artefacts:
  - Journey detail: [phases count] phases, [paths count] paths
  - Participant interaction: [participant count] participants
  - NFRs: [count] requirements across [phase count] phases
  - Data model: [entity count] entities, [relationship count] relationships
  - Service boundaries: [service count] services
  - API contracts: [contract count] contracts
  - Sequence diagrams: [diagram count] diagrams (JSON + Mermaid pairs)
  - Events: [event count] events
Central model updates: [entities added/modified], [services added/modified]
C4 workspace updates: [L2 relationships added/modified], [L3 component diagrams added]
Feedback loops: [count] — [summary of each]
Cross-capability integration points: [count and description]
Open questions: [list or none]
```

## Completion gate (Gate 2: UI spec readiness, repeating)

- [ ] All steps 7-13 have artefacts committed
- [ ] All artefacts validate against their JSON schemas
- [ ] Data model entities merged into central-model/entities/
- [ ] Service map updated in central-model/service-map.json
- [ ] Event catalogue updated in central-model/event-catalogue.json
- [ ] Sequence diagrams cover all journey phases (JSON + Mermaid pairs in sync)
- [ ] C4 workspace updated — L2 relationships refined, L3 component diagrams added
- [ ] Cross-capability integration points flagged and reviewed
- [ ] All feedback loops documented in Jira comments
- [ ] Quality Reviewer has no outstanding blockers
- [ ] Domain Analyst has approved the journey narrative
- [ ] No naming conflicts with previously completed journeys
