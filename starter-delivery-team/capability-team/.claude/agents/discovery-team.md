# Discovery Team

Triggered by: new capability design project initiated
Spawned by: Capability Lead
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
| 1. Capabilities | `foundation/capabilities/*.json` | Domain Analyst | Researches market landscape, competitive structure, and regulatory horizon before drafting capabilities (see Step 1 research brief below) |
| 3. Governance | `foundation/governance/*.json` | Domain Analyst | Structures current rules AND flags incoming regulation from Step 1 horizon scanning; every rule cites a regulation by `id` from `starter-regulations/` where one exists; cannot validate correctness |
| 4. Personas | `foundation/personas/*.json` | Domain Analyst | Generates from capabilities including persona types revealed by market research (e.g. TPPs from open banking, ESG rating agencies from sustainability regulation); human adds tacit knowledge |

These artefacts are **deeply institutional**. The agent generates first
drafts from public sources and market research. The Domain Analyst
validates against institutional reality that isn't written in any
document. The research depth at Step 1 determines the quality of
everything that follows.

### Step 1 research brief

Before producing any capability artefact, the agent must research the
market context for the organisation's sector. This is not optional — a
capability list derived only from the org chart or mandate produces a
shallow architecture that misses strategic context. The agent does the
breadth; the Domain Analyst does the depth.

**Market landscape (per capability domain):**
- What do the leading organisations in this sector currently offer?
  What is table stakes vs genuine differentiator?
- Which capabilities are being unbundled by specialist or technology-led
  entrants? Which are being re-bundled by platform players?
- Where is the margin — what commercial model sustains each capability?
- For each capability, who are the top incumbents and top challengers?
- What capabilities are candidates for buy-not-build (platform providers,
  BaaS, SaaS)? What must be built in-house for regulatory or competitive
  reasons?

**Regulatory landscape:**
- What current legislation and regulation creates or constrains each
  capability? (This feeds directly into the mandate_source field)
- What regulation is coming in the next 2-3 years that will create new
  capabilities or reshape existing ones?
- What enforcement actions or supervisory statements signal where the
  regulator's attention is focused?

**Start with the starter library:**

Read `../../../../../starter-regulations/` (from
`capability-team/.claude/agents/` that is five levels up) as the
first pass. It is indexed by sector — read the sector files that
correspond to the capabilities under design plus any cross-cutting
files (e.g. `data-protection.json`, `cybersecurity-and-resilience.json`).
Also read `../../../../../starter-standards/` for non-regulatory
standards the project may need to meet (accessibility, ISO, SOC).

Each regulation in the starter library has an `applicable_countries`
field — filter by the project's target markets. Each regulation
carries a canonical `id` — use that id verbatim in
`capability.mandate_source.reference` and
`governance.rules[].source.reference` (step 3). Do NOT invent
alternative identifiers.

If a regulation you need is not in the starter library, create a
governance rule anyway and flag to the Domain Analyst that the
library should be extended — the starter library is a baseline, not
exhaustive.

**Competitive positioning:**
- What is being commoditised vs where is there genuine differentiation?
- Where are partnerships replacing build?
- What industry standards or shared infrastructure exist (e.g. payment
  schemes, industry utilities, shared data platforms)?
- What technology shifts are changing the cost structure of capabilities
  (e.g. AI in fraud detection, digitisation of trade finance documents)?

**Sub-capability boundary evidence:**
The market research directly informs the promotion test:
- If specialist providers exist for a sub-capability, that is evidence
  for "distinct external participants" and "independent scalability"
- If a separate regulatory framework governs a sub-capability, that is
  evidence for "separate regulatory framework"
- If the market treats something as a distinct product with its own
  lifecycle, that is evidence for "distinct lifecycle"

**Output:** The research findings are captured in a `market_context`
section within each capability artefact (competitive landscape,
regulatory horizon, build-vs-buy assessment) and in the design
decisions (rationale for promotion/retention informed by market
evidence).

The Domain Analyst reviews the research against what this specific
organisation actually does and intends to do. The agent can find that
a capability is being disrupted by technology entrants; only the Domain
Analyst knows whether this organisation is investing in it, outsourcing
it, or exiting it.

### Layer 2: Technical Architecture (Steps 2, 5)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 2. Technical services | `foundation/technical-services/*.json` | Architect | Enumerates from capabilities; identifies shared services; considers industry standards and buy-vs-build from Step 1 research |
| 5. Visual architecture | `architecture/visual-architecture.json` + `channel-model.json` | Architect | Produces structured representation; human defines layering |
| 5. C4 workspace (L1 + L2) | `architecture/c4-workspace.dsl` | Architect | Generates Structurizr DSL from capabilities, services, personas, channels |
| 5. Service dependencies | `architecture/service-dependencies.json` | Architect | Assigns tier (T0-T4), maps dependency criticality (hard/soft), defines build order |
| 5. Service catalogue | `architecture/service-catalogue.json` | Architect | Consolidates all services with owner, API style, data store, SLA |
| 5. Observability model | `architecture/observability-model.json` | Architect | Defines log routing, instrumentation checklist, logging schemas, data freshness |
| 5. Security model | `architecture/security-model.json` | Architect | Defines zero-trust policy, mTLS, data classification, network segmentation |
| 5. Environment specification | `architecture/environment-spec.json` | Architect | Derives CI, RC, prod-parity configs from service catalogue + dependencies + security model |

These artefacts are **structural/technical**. The Architect makes
the service classification and boundary decisions.

#### C4 workspace

Created at step 5 as a **living artefact** in Structurizr DSL format:
- **System Context (L1)**: the system boundary, all personas (as people
  or external software systems), external system integrations
- **Container (L2)**: one container per technical service, relationships
  derived from channel model, data stores identified from service
  classifications

The workspace grows in later phases — Journey Modelling refines L2
and adds Component (L3) diagrams.

#### Service dependency tiers

Every service is assigned a build tier based on its upstream dependencies:

| Tier | Name | Rule |
|------|------|------|
| T0 | Foundation | No upstream dependencies — build first |
| T1 | Core Infrastructure | Depends only on T0 — compliance prerequisites |
| T2 | Business Services | Depends on T0 + T1 — core money-movement and data |
| T3 | Composite | Depends on T0 + T1 + T2 — multi-dependency capabilities |
| T4 | Overlay | Depends on full stack — build last |

Each dependency is classified by criticality:
- **hard**: sync dependency — caller cannot function if this is down
- **soft**: async/degradable — caller can function in degraded mode

The build order defines phases where services within a phase can be
built in parallel. The recommended build order is regulatory-driven:
compliance prerequisites (KYC, sanctions, fraud) must be live before
any payment or onboarding service.

#### Observability model

Defines the telemetry architecture following OTel Collector as sole
ingestion point. Key principles:
- All services emit via OTLP — never connect to stores directly
- PII scrubbing in the collector pipeline before data reaches stores
- Four stores with different retention/access: Log (90d), Trace (30d),
  Metrics (13mo), Audit (7yr WORM, auditor-only)
- Per-service instrumentation checklist (6 items, mandatory gate)
- Logging schema by service category (7 categories)
- `service.yaml` manifest per repo: id, tier, depends_on with
  criticality, data_classification, secrets with rotation_days

#### Security model

Defines zero-trust security posture:
- service.yaml as authoritative allowed-call policy source
- mTLS via service mesh with workload identity
- Data classification levels (public → regulated) driving SIEM severity
- Network segmentation zones (DMZ, Application, Data, Compliance, Management)
- Security controls: zero-trust policy map, mTLS status, secret rotation,
  blast radius visualiser, CVE exposure, audit log separation

#### Environment specification

Derived from service catalogue, dependencies, and security model.
Defines three environments (CI, RC, prod-parity) with what is real
vs stubbed in each:
- Service list and startup ordering (from dependency tiers)
- Database provisioning (from service catalogue data_store)
- External system stubs (from C4 external software systems)
- Secrets and .env configuration (from security model)
- OTel pipeline configuration (from observability model)
- Network zones (from security model segmentation)

### Layer 3: Journey Inventory (Step 6)

| Step | Artefact | Lead | Agent role |
|------|----------|------|------------|
| 6. Journey inventory | `foundation/journey-inventory.json` | Domain Analyst + Architect | Generates comprehensive list from sub-capability × persona matrix |

This is the bridge between foundation and modelling. The output is
a prioritised backlog of journeys for Phase C.

## Step sequence (strictly sequential)

```
Step 1: Capabilities
  │  1a. Market research (agent: competitive landscape, regulatory
  │      horizon, build-vs-buy, sub-capability boundary evidence)
  │  1b. Capability drafting (agent: from research + mandate + legislation)
  │  1c. Domain Analyst review (human: validates against institutional
  │      reality, adjusts promotion decisions, makes build-vs-buy calls)
  ↓ (capabilities define what services are needed)
Step 2: Technical services
  ↓ (services need governance constraints)
Step 3: Governance mapping (includes incoming regulation from Step 1 horizon scan)
  ↓ (governance constrains who can do what)
Step 4: Personas (includes persona types revealed by market research)
  ↓ (personas + capabilities → architecture)
Step 5: Visual architecture + service dependencies + observability + security + environments
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
- Reviews the agent's market research against what this specific
  organisation actually does, intends to do, and has decided not to do
- Applies the sub-capability promotion test, using market evidence
  from the research to support or challenge the agent's assessment:
  1. Distinct external participants? (market: do specialist providers exist?)
  2. Separate regulatory framework? (market: is there distinct regulation?)
  3. Distinct lifecycle? (market: is it treated as a separate product?)
  4. Independent scalability requirements? (market: different demand drivers?)
  If 3+ criteria met → promote to standalone capability
- Identifies shared sub-capabilities across capabilities
- Makes build-vs-buy decisions informed by market research — the agent
  identifies what platforms and providers exist; the Domain Analyst
  decides what this organisation builds, buys, or partners for
- Sources: organisational mandate, legislation, charter, strategic plan,
  annual reports, organisational charts, delegated authority matrices,
  regulator publications, industry body reports, competitor analysis

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
- Assigns service dependency tiers (T0-T4) with criticality (hard/soft)
  and defines the recommended build order
- Produces the observability model: log routing architecture, instrumentation
  checklist, logging schemas by category, data freshness contracts
- Produces the security model: zero-trust policy, mTLS, data classification,
  network segmentation zones

### Quality Reviewer
- Reviews every artefact before it moves from Draft to In review
- Checks: schema compliance, internal consistency, completeness,
  naming consistency across all artefacts
- Does NOT produce artefacts — only validates
- Sends findings: `REVIEW [info|warning|blocker]: [issue] — [artefact]`

## Error handling

See `context/defect-handling.md` for the full protocol.

Summary for this team:
- Stop immediately on any failure.
- Signal `DISCOVERY BLOCKED` with step, failure, completed files,
  suggested resolution.
- Never silently skip or work around a failure.

## Signal to Capability Lead

```
DISCOVERY COMPLETE.
Artefacts:
  - Capabilities: [count] capabilities, [count] sub-capabilities
  - Technical services: [count] domain, [count] cross-cutting, [count] foundation
  - Governance rules: [count] across [count] capabilities
  - Personas: [count] internal, [count] external
  - Visual architecture: [count] layers, [count] channels
  - C4 workspace: System Context (L1) + Container (L2) diagrams
  - Service dependencies: [count] services across T0-T4, [count] build phases
  - Service catalogue: [count] services with owner, SLA, API style
  - Observability model: [count] instrumentation checklist items, [count] log categories
  - Security model: [count] controls, [count] data classification levels, [count] network zones
  - Journey inventory: [count] journeys, prioritised
Shared sub-capabilities: [count] with resolutions
All artefacts baselined: [yes|no]
Open questions: [list or none]
Recommended first journey for Phase C: [{journey-name}]
```

## Completion gate (Gate 1: Modelling readiness)

- [ ] All foundation artefacts committed and baselined (including C4 workspace, service dependencies, observability model, security model)
- [ ] All artefacts validate against their JSON schemas
- [ ] Sub-capability promotion test applied and documented for every sub-capability
- [ ] Shared sub-capabilities recorded with resolution patterns
- [ ] Resolution patterns match technical service mapping
- [ ] Journey inventory is prioritised
- [ ] First journey for Phase C is selected
- [ ] Quality Reviewer has no outstanding blockers
- [ ] Domain Analyst has approved all artefacts
