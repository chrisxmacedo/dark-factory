# Discovery Team

Triggered by: new capability design project initiated
Spawned by: Programme Lead
Shuts down when: Gate 1 passed — all foundation artefacts baselined, journey inventory prioritised

Pipeline stage: **Phase A (Discovery) + Phase B (Framing) — Steps 1-6**
Confidence goal: "We know what the organisation does, what constrains it, who interacts with it, and what the prioritised journey backlog looks like"

This team produces the stable foundation that all subsequent work
builds on. Steps are **sequential** — each depends on the previous.
Outputs are baselined and rarely revised.

## Deliverables

### Layer 1: Organisational Identity (Steps 1, 3, 4)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 1. Capabilities | `foundation/capabilities/*.json` | Domain Analyst | Drafts from public sources (mandate, legislation, charter) |
| 3. Governance | `foundation/governance/*.json` | Domain Analyst | Structures rules; cannot validate correctness |
| 4. Personas | `foundation/personas/*.json` | Domain Analyst | Generates from capabilities; human adds tacit knowledge |

These artefacts are **deeply institutional**. The agent generates first
drafts from public sources. The Domain Analyst validates against
institutional reality that isn't written in any document.

### Layer 2: Technical Architecture (Steps 2, 5)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 2. Technical services | `foundation/technical-services.json` | Architect | Enumerates from capabilities; identifies shared services |
| 5. Visual architecture | `architecture/visual-architecture.json` + `channel-model.json` | Architect | Produces structured representation; human defines layering |
| 5. C4 workspace (L1 + L2) | `architecture/c4-workspace.dsl` | Architect | Generates Structurizr DSL from capabilities, services, personas, channels |

These artefacts are **structural/technical**. The Architect makes
the service classification and boundary decisions.

The C4 workspace is created at step 5 as a **living artefact** in
Structurizr DSL format:
- **System Context (L1)**: the system boundary, all personas (as people
  or external software systems), external system integrations
- **Container (L2)**: one container per technical service, relationships
  derived from channel model, data stores identified from service
  classifications

The workspace grows in later phases — Journey Modelling refines L2
and adds Component (L3) diagrams, UI Specification adds portal
containers.

### Layer 3: Journey Inventory (Step 6)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 6. Journey inventory | `foundation/journey-inventory.json` | Domain Analyst + Architect | Generates comprehensive list from sub-capability × persona matrix |

This is the bridge between foundation and modelling. The output is
a prioritised backlog of journeys for Phase C.

## Step sequence (strictly sequential)

```
Step 1: Capabilities
  ↓ (capabilities define what services are needed)
Step 2: Technical services
  ↓ (services need governance constraints)
Step 3: Governance mapping
  ↓ (governance constrains who can do what)
Step 4: Personas
  ↓ (personas + capabilities → architecture)
Step 5: Visual architecture
  ↓ (architecture + personas → journey inventory)
Step 6: Journey inventory
  ↓ Gate 1
```

Each step must be completed, reviewed, and baselined before the next
begins. The Review Team reviews each artefact at the Draft → In review
transition.

## Team composition

### Domain Analyst (leads Layers 1 + 3)
- Deep institutional knowledge — the primary value is tacit knowledge
  that isn't in any document
- Leads steps 1, 3, 4, 6
- Validates every artefact against institutional reality
- Applies the sub-capability promotion test:
  1. Distinct external participants?
  2. Separate regulatory framework?
  3. Distinct lifecycle?
  4. Independent scalability requirements?
  If 3+ criteria met → promote to standalone capability
- Identifies shared sub-capabilities across capabilities
- Sources: organisational mandate, legislation, charter, strategic plan,
  annual reports, organisational charts, delegated authority matrices

### Architect (leads Layer 2)
- Structural and technical decisions
- Leads steps 2, 5
- Classifies services: domain-specific, cross-cutting, foundation
- Validates shared sub-capability resolutions match service mapping
- Defines the channel model (how each participant type accesses the system)
- Produces the visual architecture — the single diagram that communicates
  the entire system to stakeholders
- Creates the initial C4 workspace (Structurizr DSL) with System Context
  and Container diagrams derived from capabilities, services, and personas

### Quality Reviewer
- Reviews every artefact before it moves from Draft to In review
- Checks: schema compliance, internal consistency, completeness,
  naming consistency across all artefacts
- Does NOT produce artefacts — only validates
- Sends findings: `REVIEW [info|warning|blocker]: [issue] — [artefact]`

## Signal to Programme Lead

```
DISCOVERY COMPLETE.
Artefacts:
  - Capabilities: [count] capabilities, [count] sub-capabilities
  - Technical services: [count] domain, [count] cross-cutting, [count] foundation
  - Governance rules: [count] across [count] capabilities
  - Personas: [count] internal, [count] external
  - Visual architecture: [count] layers, [count] channels
  - C4 workspace: System Context (L1) + Container (L2) diagrams
  - Journey inventory: [count] journeys, prioritised
Shared sub-capabilities: [count] with resolutions
All artefacts baselined: [yes|no]
Open questions: [list or none]
Recommended first journey for Phase C: [{journey-name}]
```

## Completion gate (Gate 1: Modelling readiness)

- [ ] All foundation artefacts committed and baselined (including C4 workspace)
- [ ] All artefacts validate against their JSON schemas
- [ ] Sub-capability promotion test applied and documented for every sub-capability
- [ ] Shared sub-capabilities recorded with resolution patterns
- [ ] Resolution patterns match technical service mapping
- [ ] Journey inventory is prioritised
- [ ] First journey for Phase C is selected
- [ ] Quality Reviewer has no outstanding blockers
- [ ] Domain Analyst has approved all artefacts
