# C4 workspace best practices

Read by: Discovery Team (step 5), Journey Modelling Team (post-step 13
C4 updates)

## Format

- Single Structurizr DSL file at `architecture/c4-workspace.dsl`.
- The source of truth for all architecture diagrams.
- **A living artefact** — not baselined. Continuously updated across
  all phases.

## Scope — C4 shows only what runs in production

Design-time artefacts do NOT appear on C4 diagrams:
- API specs
- Journey specs
- Regulatory constraints
- AI development agents

The Contract Layer does not appear on L2.

## Level 1 — System Context

- The system boundary.
- Actual system users (personas).
- External systems (integrations).
- No AI agents. No design-time artefacts.

## Level 2 — Container

Two boundary groupings within the system:

### Capabilities boundary
- Each capability appears as one container.
- Arrows between capabilities are labelled with the async events they
  exchange.
- **No synchronous arrows between capabilities.**

### Platform boundary
- Sits below capabilities.
- Contains: Event Bus, Schema Registry, Observability, Audit Pipeline,
  Auth, Cache.
- Dependency arrows flow downward from capabilities to platform.

## Level 3 — Component

Zooms into a single capability. Shows:
- Internal services
- Inbound ports (event consumers)
- Outbound ports (event publishers)
- API controllers
- Data stores
- Platform adapters (to Event Bus, Audit, etc.)

External dependencies shown are the platform containers the capability
connects to at runtime — not other capabilities (cross-capability
integration is via events on L2).

## Traceability

Every element on the workspace traces to a JSON artefact:

- Personas → `foundation/personas/*.json`
- Capabilities → `central-model/service-map.json`
- Containers within a capability → `service-boundaries.json`
- Platform services → `architecture/service-catalogue.json`

The Review Team validates C4-to-JSON consistency at every review.

## When to update

- **Phase B, step 5:** Discovery Team produces L1 + L2.
- **Phase C, after each journey:** Journey Modelling Team refines L2
  relationships (new events labelled on capability arrows) and adds L3
  component diagrams for newly-touched capabilities.

## Anti-patterns

- Drawing synchronous arrows between capabilities "just for this
  diagram".
- Showing design-time artefacts (journey specs, API specs) as containers.
- Omitting the Event Bus from L2 when two capabilities communicate.
- Letting the DSL drift from the JSON — it is the same model, just a
  different view.
