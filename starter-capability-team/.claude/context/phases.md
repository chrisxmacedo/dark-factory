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
| 6. Journey inventory | `foundation/journey-inventory.json` | Sub-capabilities x personas | Domain Analyst |

## Gate 1: Modelling readiness

Passed once. Conditions:
- All foundation artefacts baselined (including C4 workspace with L1 + L2)
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

When stable journey model + approved screen specs exist:
- Create Deliverable in DEV project
- Include: journey detail, data model, API contracts, sequence diagrams
  (JSON + Mermaid), screen specs, task flows, relevant C4 component diagrams
- This is one buildable unit of work

## Timeline (typical)

| Phase | Duration | Team |
|-------|----------|------|
| A + B | 2-3 weeks | Domain Analyst + Architect |
| C (all journeys) | 8-12 weeks | Domain Analyst + Architect + Designer (from week 3) |
| D (all portals) | 6-8 weeks (overlaps C) | Designer + Architect |
| Total design | 12-16 weeks | DEV receives buildable units from week 5 onwards |
