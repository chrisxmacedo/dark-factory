# Capability modelling best practices — index

Read by: Discovery Team, Journey Modelling Team

This file is an index. Read only the files relevant to the current step.
Every file here specifies what the capability pipeline produces as
**design output** for the downstream development pipeline. None of them
prescribe implementation.

## Phase A — Discovery (steps 1-4)

| File | Read at step |
|------|---------------|
| [`capability-decomposition.md`](capability-decomposition.md) | 1 — capabilities + sub-capabilities |
| [`service-boundaries.md`](service-boundaries.md) | 2 — technical services |

## Phase B — Framing (step 5-6)

| File | Read at step |
|------|---------------|
| [`service-boundaries.md`](service-boundaries.md) | 5 — service dependencies + tiers |
| [`c4-workspace.md`](c4-workspace.md) | 5 — C4 L1 + L2 |
| [`observability.md`](observability.md) | 5 — observability model |
| [`security.md`](security.md) | 5 — security model |
| [`journey-modelling.md`](journey-modelling.md) | 6 — journey inventory |

## Phase C — Analytical Modelling (steps 7-13, per journey)

| File | Read at step |
|------|---------------|
| [`journey-modelling.md`](journey-modelling.md) | 7 — journey detail |
| [`data-modelling.md`](data-modelling.md) | 10 — data model, 11-13 transformations |
| [`service-boundaries.md`](service-boundaries.md) | 11 — service boundaries |
| [`api-contracts.md`](api-contracts.md) | 12 — API contracts |
| [`sequence-diagrams.md`](sequence-diagrams.md) | 12 — sequence diagrams |
| [`event-design.md`](event-design.md) | 13 — event catalogue |
| [`c4-workspace.md`](c4-workspace.md) | post-13 — L2 refinement + L3 |

## Cross-cutting (read once per session)

- [`capability-decomposition.md`](capability-decomposition.md) — what
  a capability is vs a service
- [`service-boundaries.md`](service-boundaries.md) — the capability
  boundary rules and the four valid communication paths

## External reference libraries (at `templates/` root)

- `starter-regulations/` — sector-indexed regulations (finance,
  data-protection, cybersecurity-and-resilience, etc.). Read at
  Phase A step 1 and step 3. Cite regulation `id`s in
  `mandate_source` and in governance rule `source.reference`.
- `starter-standards/` — non-regulatory standards (WCAG, ISO 27001,
  SOC 2, ISO 9001). Referenced from `security.md` and
  `observability.md` as baseline control sets.

## The handoff

Every file in this directory describes **what the capability team
specifies** so the downstream development team can build. Nothing here
tells the development team how to implement — that is their concern.
The specification is the contract; how the contract is satisfied is
decided by the dev team in their own pipeline.
