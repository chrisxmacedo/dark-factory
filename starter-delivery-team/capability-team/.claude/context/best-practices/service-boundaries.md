# Service boundaries best practices

Read by: Discovery Team (step 2 — technical services), Journey Modelling
Team (step 11 — service boundaries)

## The capability boundary is hard

- No shared databases across capabilities.
- No synchronous calls between capabilities.
- No shared data models across capabilities.
- The Event Bus is the sole cross-capability integration mechanism.

## Within a capability

Services communicate by whatever means suits the domain:
- Direct method calls
- Shared database (within the capability)
- Internal REST/gRPC
- Internal queues

This is an internal technical decision. The Architect documents the
choice in `service-boundaries.json` but channels and other capabilities
never see it.

## Boundary drawing rules

- Each capability owns: its own data (one or more databases/schemas),
  its own services, its own event contracts, its own REST API surface.
- High revision counts on a capability boundary signal it should be
  redrawn.
- The Architect makes boundary decisions — the agent provides options
  analysis (at least two).
- A service never spans multiple capabilities. If a service appears to,
  it is actually two services sharing a name — split them.

## Service dependency tiers

Every service is assigned a build tier based on upstream dependencies:

| Tier | Name | Rule |
|------|------|------|
| T0 | Foundation | No upstream dependencies — build first |
| T1 | Core Infrastructure | Depends only on T0 — compliance prerequisites |
| T2 | Business Services | Depends on T0 + T1 — core money-movement / data |
| T3 | Composite | Depends on T0 + T1 + T2 — multi-dependency capabilities |
| T4 | Overlay | Depends on full stack — build last |

Each dependency is classified by criticality:
- **hard** — sync dependency, immediate failure if upstream is down
- **soft** — async or degradable, caller can run in degraded mode

The dependency graph + criticality drives the blast radius visualiser
and the zero-trust policy enforcement.

## service.yaml manifest

Per service repo. The authoritative source for the zero-trust policy
engine and the deployment pipeline:

- `id` — service identifier (SVC-NNN)
- `tier` — T0-T4
- `depends_on` — list of services with `protocol` and `criticality`
- `topics_produced` — events this service publishes
- `topics_consumed` — events this service consumes
- `data_classification` — public | internal | confidential | regulated
- `secrets` — list with `rotation_days`

## Classifications

- **Channel services** (Digital Channels, Online Banking, Mobile App)
  are NOT capabilities. They sit outside the system boundary and may
  call any capability's REST API synchronously. Classify as `channel`.
- **Platform services** (IAM, Event Bus, Audit, Observability, Cache,
  Notifications) are `foundation`. They are invisible to
  cross-capability violation checks.
- **Domain services** live inside a capability. Classified by capability.

## Anti-patterns

- Creating a capability-to-capability synchronous API "just this once".
- Sharing a database across capabilities to avoid event plumbing.
- A service with hard dependencies on a higher tier than itself
  (dependency inversion — redraw).
- Assigning tier without evidence from the dependency graph.
