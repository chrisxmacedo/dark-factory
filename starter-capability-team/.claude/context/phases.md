# Phase model and orchestration

Read by: Programme Lead only

## Phase flow

```
Phase A (Discovery)      → sequential, do once
Phase B (Framing)        → sequential, do once
  ── Gate 1 ──
Phase C (Modelling)      → iterative, per journey
  ── Gate 2 (repeating) ──
Phase D (UI Spec)        → iterative, per portal (parallel with C)
  ── Handoff to DEV ──
```

## Phase A — Discovery (steps 1-4)

Sequential. Each step depends on the previous. Outputs baselined.

| Step | Artefact | Inputs | Owner |
|------|----------|--------|-------|
| 1. Capabilities | `foundation/capabilities/*.json` | Mandate, legislation, charter | Domain Analyst |
| 2. Technical services | `foundation/technical-services.json` | Capabilities | Architect |
| 3. Governance | `foundation/governance/*.json` | Legislation, policy, capabilities | Domain Analyst |
| 4. Personas | `foundation/personas/*.json` | Capabilities, governance | Domain Analyst |

## Phase B — Framing (steps 5-6)

Sequential. Produces the system map and journey backlog.

| Step | Artefact | Inputs | Owner |
|------|----------|--------|-------|
| 5. Visual architecture + C4 | `architecture/visual-architecture.json` + `channel-model.json` + `architecture/c4-workspace.dsl` | Capabilities, services, personas | Architect |
| 5. Service dependencies | `architecture/service-dependencies.json` + `architecture/service-catalogue.json` | Technical services, capabilities | Architect |
| 5. Observability model | `architecture/observability-model.json` | Technical services, governance | Architect |
| 5. Security model | `architecture/security-model.json` | Technical services, governance, personas | Architect |
| 5. Environment specification | `architecture/environment-spec.json` | Service catalogue, dependencies, security model | Architect |
| 6. Journey inventory | `foundation/journey-inventory.json` | Sub-capabilities x personas | Domain Analyst |

## Gate 1: Modelling readiness

Passed once. Conditions:
- All foundation artefacts baselined (including C4, service dependencies, observability model, security model)
- Journey inventory prioritised
- First journey selected

## Phase C — Analytical Modelling (steps 7-13, per journey)

Iterative. Pick highest-priority journey, model steps 7-13, aggregate
into central model, repeat.

**Cross-capability journeys**: A journey may span multiple capabilities.
This is expected and desirable — it reveals the integration points
between capability domains. The sequence diagram (step 12) for a
cross-capability journey shows exactly which services need to
communicate, making it the primary input for cross-cutting service
design. The journey inventory (step 6) naturally produces
cross-capability journeys from the sub-capability × persona matrix.

| Step | Artefact | Inputs | Owner |
|------|----------|--------|-------|
| 7. Journey detail | `models/{journey}/journey-detail.json` | Foundation artefacts | Domain Analyst |
| 8. Participant interaction | `models/{journey}/participant-interaction.json` | Journey detail, governance, channels | Domain Analyst |
| 9. NFRs | `models/{journey}/nfr.json` | Journey detail | Architect |
| 10. Data model | `models/{journey}/data-model.json` | Journey detail, interaction model, NFRs | Architect |
| 11. Service boundaries | `models/{journey}/service-boundaries.json` | Data model, NFRs, technical services | Architect |
| 12. API contracts + sequences | `models/{journey}/api-contracts/*.openapi.json` + `models/{journey}/sequence-diagrams/*.json` + `*.mmd` | Boundaries, data model, interaction model | Architect |
| 13. Event catalogue | `models/{journey}/events/*.json` | Boundaries, sequence diagrams | Architect |

After each journey, update:
- Central model (entities, service map, event catalogue)
- C4 workspace (refine L2 container relationships, add L3 component diagrams)

Feedback loops:
- Intra-journey: step 12 → step 10 (API reveals missing entity)
- Cross-journey: journey N → central model → journey N+1 (shared entity needs restructuring)

## Gate 2: UI spec readiness (repeating)

Passed repeatedly. Conditions:
- At least one journey's artefacts are "Stable"
- Central model updated
- No blocking refinements outstanding

## Phase D — UI Specification (steps 14-18, per portal)

Iterative. Runs parallel with Phase C once Gate 2 is passed.

| Step | Artefact | Inputs | Owner |
|------|----------|--------|-------|
| 14. Portal definition | `ui-specs/{portal}/information-architecture.json` | Stable journey models | Designer |
| 15. Screen specs | `ui-specs/{portal}/screens/{screen}.json` | IA, data model, interaction model, APIs | Designer |
| 16. Task flows | `ui-specs/{portal}/task-flows/{journey}-flow.json` | Screen specs, sequence diagrams | Designer |
| 17. Form specs | `ui-specs/{portal}/forms/{form}.json` | Data model, screen specs, governance | Designer |
| 18. Design system | `ui-specs/{portal}/design-system.json` | Screen specs, NFRs | Designer |

Feedback loop:
- UI-to-model: screen spec reveals missing field → MODEL refinement ticket

## Handoff to DEV

### Sprint 0: Foundation (after Gate 1, before first journey)

The first handoff is not a journey — it is the foundation that all
journeys require. Created once from the architecture artefacts:

| Ticket type | Source | Description |
|-------------|--------|-------------|
| Environment setup (CI) | `service-dependencies.json` + `service-catalogue.json` + `security-model.json` | docker-compose, CI pipeline, ephemeral databases, test secrets, OTel collector (minimal), external system stubs |
| Environment setup (RC) | Same sources | Persistent databases, full OTel stack, rotated secrets |
| Environment setup (prod-parity) | Same sources | Full OTel + audit pipeline, Vault-backed secrets, network zones |
| T0 platform service (per service) | `service-dependencies.json` tier 0 | IAM, API Gateway, Event Bus, OTel Collector, Secrets Management, Service Mesh |
| T1 observability stores | `observability-model.json` | Log Store, Trace Store, Metrics Store, Audit Log Store (WORM) |

Environment differences:

| Component | CI | RC | Prod-parity |
|-----------|----|----|-------------|
| Domain capabilities | Real | Real | Real |
| Platform (IAM, Event Bus) | Real | Real | Real |
| External systems | Stubs | Stubs | Stubs or sandbox |
| Databases | Ephemeral | Persistent | Persistent + seed data |
| OTel pipeline | Collector only | Full stack | Full stack |
| Secrets | Test values | Rotated | Rotated, Vault-backed |

### Journey Deliverables (repeating, per journey)

When stable journey model + approved screen specs exist:
- Create Deliverable in DEV project
- Include: journey detail, data model, API contracts, sequence diagrams
  (JSON + Mermaid), screen specs, task flows, relevant C4 component diagrams,
  service.yaml manifests for affected services, observability and security
  requirements from the architecture models
- This is one buildable unit of work

### Ticket decomposition strategy

**Vertical slices by journey, on a foundation base.**

Sprint 0 builds the platform. Then each journey is a vertical slice
through the capability stack — not "build all services then journeys."

Each journey Deliverable is decomposed into tickets by artefact type:

| Ticket type | Source artefact | Scope |
|-------------|----------------|-------|
| Capability scaffold | `service-boundaries.json` | One per new capability this journey introduces — own DB schema, own app, own test suite, service.yaml |
| Entity implementation | `data-model.json` | One per entity — fields, types, validation, relationships |
| API endpoint | `api-contracts/*.openapi.json` | One per endpoint — must include example request/response bodies |
| Event producer/consumer | `events/*.json` | One per event — source, payload schema, consumers |
| Screen | `screens/{screen}.json` | One per screen — all 6 states mandatory |
| Task flow E2E test | `task-flows/*.json` | One per journey path (happy, alt, exception) |
| Instrumentation | `observability-model.json` | One per new capability — per-category logging schema, health endpoints, service.yaml |
| Security classification | `security-model.json` | One per new capability — data classification, network zone, mTLS config |

Services grow incrementally: JRN-001 builds the Customer entity with
10 fields. JRN-005 adds 5 more fields for Business Account. JRN-008
adds lending fields. The central model aggregation tracks this growth.

Journey dependencies: the journey inventory priority order respects
capability dependencies — you cannot model JRN-003 (Mortgage) until
JRN-001 (Account Opening) establishes the Customer and Account entities.

**Capabilities are the deployment boundary.** Each promoted sub-capability
and each retained parent capability is one deployable unit with its own
database schema, application, and test suite. The promotion test
determines the boundary.

## Timeline (typical)

| Phase | Duration | Team |
|-------|----------|------|
| A + B | 2-3 weeks | Domain Analyst + Architect |
| Sprint 0 (platform) | 1-2 weeks | DEV team (overlaps with Phase C start) |
| C (all journeys) | 8-12 weeks | Domain Analyst + Architect + Designer (from week 3) |
| D (all portals) | 6-8 weeks (overlaps C) | Designer + Architect |
| Total design | 12-16 weeks | DEV receives Sprint 0 at week 3, buildable journey units from week 5 onwards |
