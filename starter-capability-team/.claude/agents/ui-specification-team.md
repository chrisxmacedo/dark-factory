# UI Specification Team

Triggered by: Gate 2 passed — at least one journey model is "Stable"
Spawned by: Programme Lead
Shuts down when: portal specs are "Approved" for all journeys that pass through it

Pipeline stage: **Phase D (UI Specification) — Steps 14-18**
Confidence goal: "These screen specs are buildable — every field references the data model, every action references an API, every screen handles all six states"

This team translates the analytical model (Phase C output) into
user-facing specifications. It works portal by portal, not journey
by journey. Phase D runs in parallel with Phase C once the first
batch of journey models reach "Stable" status.

This team reads across two teams' outputs:
- **Journey Modelling** — data model, API contracts, sequence diagrams, NFRs
- **Discovery** — governance rules (baselined, for form conditional logic
  and entitlement-driven field visibility), personas, channel model

## Deliverables

### Layer 6: Portal Specifications (Steps 14-18)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 14. Information architecture | `ui-specs/{portal}/information-architecture.json` | Interaction Designer | Generates screen inventory from stable journey models; human defines navigation and grouping |
| 15. Screen specifications | `ui-specs/{portal}/screens/{screen}.json` | Interaction Designer | Generates field mappings from data model; human makes layout and UX decisions |
| 16. Task flows | `ui-specs/{portal}/task-flows/{journey}-flow.json` | Interaction Designer | Generates from sequence diagrams; human refines click sequences |
| 17. Form specifications | `ui-specs/{portal}/forms/{form}.json` | Interaction Designer | Derives from data model + governance rules; human makes grouping and ordering decisions |
| 18. Design system | `ui-specs/{portal}/design-system.json` | Interaction Designer + Architect | Generates component patterns from screen specs; human defines visual language |

### Supporting artefacts

| Artefact | Description |
|----------|-------------|
| `design-system/component-patterns.json` | Reusable component patterns across portals |
| `design-system/error-states.json` | Error and failure mode UI treatment |

### C4 workspace update

After completing each portal, update `architecture/c4-workspace.dsl`:
- Add the portal as a **Container** (frontend application type)
- Add relationships from the portal container to backend service containers
  (derived from the API contracts the portal's screens reference)
- This completes the Container (L2) diagram with the user-facing layer

## Step sequence (portal-first, not screen-first)

```
Step 14: Information architecture (screen inventory, navigation)
  ↓
Step 15: Screen specifications (fields, states, actions per screen)
  ↓
Step 16: Task flows (user-level click sequences per journey)
  ↓
Step 17: Form specifications (input fields, validation, conditional logic)
  ↓
Step 18: Design system (reusable patterns for this portal)
```

Design one portal at a time. This ensures navigation, layout, and
patterns are consistent within a portal before moving to the next.

## Six-state requirement

Every screen must address all six states:
1. **Loading** — data is being fetched
2. **Empty** — no data exists yet (first-time user)
3. **Happy path** — normal data, expected behaviour
4. **Partial data** — some API calls succeeded, some failed
5. **Error** — service unavailable
6. **Forbidden** — user lacks entitlement for this screen

A screen spec that only describes the happy path is incomplete.

## Field-level traceability

Every field on a screen must reference:
- The data model entity and field it displays
- The projection rule (from participant interaction model)
- The action entitlement — can this participant edit this field?
- The validation rule (from data model) — applied client-side

Do NOT invent fields that don't exist in the data model.

## UI-to-model feedback loop

When a screen spec reveals a gap in the analytical model:
1. Document the gap: which entity, which field, why it's needed
2. Create a "Model feedback" ticket in the MODEL project
3. Link it to the UXSPEC screen spec
4. Mark the affected screen as "Pending model update"
5. Continue with other screens — do NOT block

The Programme Lead prioritises model feedback in the Phase C backlog.

## Team composition

### Interaction Designer (leads all steps)
- Leads steps 14-18 for each portal
- Reads governance rules from foundation artefacts for form conditional
  logic and entitlement-driven field visibility
- Translates system-level sequence diagrams into user-level task flows
- Ensures every screen addresses all six states
- References the data model for field-level detail — never invents
  fields that don't exist in the model
- Identifies UI-to-model feedback gaps and creates refinement tickets
- Makes UX decisions: field grouping, ordering, navigation, conditional
  display logic

### Architect (supports steps 15, 17, 18)
- Validates that screen fields reference real data model entities
- Validates that actions reference real API contracts
- Ensures error states align with actual service failure modes
- Reviews form validation rules against data model constraints
- Contributes to design system — ensures component patterns match
  the technical architecture
- Updates C4 workspace with portal containers and their relationships
  to backend services

### Quality Reviewer
- Reviews every artefact before it moves from Draft to In review
- Checks:
  1. All screens address all six states
  2. All fields reference data model entities (no invented fields)
  3. All actions reference API contracts
  4. Task flows cover every journey that passes through this portal
  5. Form validation matches data model constraints
  6. Design system patterns are consistent within the portal
  7. Schema compliance
- Sends findings: `REVIEW [info|warning|blocker]: [issue] — [artefact]`

## Signal to Programme Lead

```
PORTAL SPEC COMPLETE.
Portal: [{portal-name}]
Participant types served: [list]
Journeys covered: [list]
Artefacts:
  - Information architecture: [screen count] screens, [nav depth] navigation levels
  - Screen specifications: [count] screens, all six states: [yes|no]
  - Task flows: [count] flows covering [journey count] journeys
  - Forms: [count] forms
  - Design system: [component count] component patterns
C4 workspace: portal container added with [count] backend service relationships
Model feedback tickets created: [count and keys]
Pending model updates: [count and affected screens]
Open questions: [list or none]
```

## Completion gate (per portal)

- [ ] All steps 14-18 have artefacts committed
- [ ] All artefacts validate against their JSON schemas
- [ ] All screens address all six states (loading, empty, happy, partial, error, forbidden)
- [ ] All screen fields reference data model entities (no invented fields)
- [ ] All actions reference API contracts
- [ ] Task flows cover every journey that passes through this portal
- [ ] Form validation rules match data model constraints
- [ ] Model feedback tickets created for any gaps
- [ ] Quality Reviewer has no outstanding blockers
- [ ] Design system patterns are consistent within the portal
- [ ] C4 workspace updated — portal container added with backend relationships
