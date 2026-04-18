# capability-team

Capability-driven system design pipeline. Part of the delivery team
(`starter-delivery-team/`). Produces a headless system specification as
machine-readable JSON artefacts consumed by the sibling development
pipeline (`../development-team/`).

The **Capability Lead** runs this pipeline. The **Programme Lead**
(`../PIPELINE.md`) owns the handoff of stable journeys into Jira for
the development team's consumption — you do not create DEV Deliverables
yourself.

## Reference libraries (outside this folder)

At the `templates/` root, two sibling folders hold starter reference
data consumed during Phase A:

- `../../starter-regulations/` — sector-indexed regulations per market.
  The Discovery Team reads this during Phase A step 1 (market research)
  and step 3 (governance mapping). Every governance rule cites a
  regulation `id` from this library where one exists.
- `../../starter-standards/` — non-regulatory standards (accessibility,
  information security, SOC, quality). Read by the Discovery Team
  (Phase A/B) and the Architect (Phase B step 5) when the project
  commits to non-regulatory quality targets.

## Structure

```
.claude/
  agents/
    discovery-team.md          — Phase A + B (steps 1-6, do once)
    refinement-team.md         — Per-journey pre-modelling brief
    journey-modelling-team.md  — Phase C (steps 7-13, per journey)
    review-team.md             — Cross-cutting quality gate
  context/
    project.md                  — Project identity, Jira config
    phases.md                   — Phase model, gates, orchestration
    artefact-standards.md       — JSON format, naming, lifecycle, vocabulary
    architecture-specification.md — Capability-driven architecture (authoritative)
    defect-handling.md          — Blocker handling, FIX EXHAUSTED escalation
    process-improvements.md     — Generalised learnings, script inventory
    best-practices/
      capability-modelling.md   — Index
      capability-decomposition.md — Phase A decomposition + promotion
      journey-modelling.md      — Phase C journey principles
      data-modelling.md         — Entities, fields, transformations
      service-boundaries.md     — Boundary rules, tiers, service.yaml
      api-contracts.md          — Per-capability REST surface
      sequence-diagrams.md      — Four-path rule, JSON + Mermaid pairing
      event-design.md           — Past tense, payloads, consumers
      c4-workspace.md           — L1/L2/L3 rules
      observability.md          — OTel model, stores, categories
      security.md               — Zero-trust, classifications, zones
scripts/
  scaffold-journey.py                — Pre-creation: directories, manifest, templates
  cleanup-ids.py                     — Post-creation: strip annotated IDs
  sync-central-model.py              — Post-creation: sync entities/events/service map
  validate-journey.py                — Post-creation: files, IDs, ownership, central model
  validate-sequences.py              — Post-creation: cross-capability violation checks
  validate-central-model-impact.py   — Cross-journey regression detector (informational)
artefacts/                     — All design outputs (template structure)
  foundation/                  — Phase A + B (JSON)
    capabilities/              — One file per capability
    governance/                — One file per capability
    personas/                  — External + internal persona files
    technical-services/        — Domain, cross-cutting, foundation service files
  architecture/                — Phase B (JSON + Structurizr DSL)
  models/                      — Phase C per journey (JSON + Mermaid + evidence)
  central-model/               — Aggregated from all journeys (JSON)
    entities/                  — One file per entity
  schemas/                     — JSON schemas for validation
PIPELINE.md                    — Capability Lead orchestration
PIPELINE-STATE.md              — Ephemeral: current journey, signals, branch state
ARTEFACT-MAP.md                — Ephemeral: current central-model state
workflow-improvements.md       — Append-only retrospective log
CONTEXT.md                     — This file
```

## Placeholders to replace

| Placeholder | Replace with |
|-------------|-------------|
| `{PROJECT_NAME}` | Full project name |
| `{ORG_NAME}` | Organisation name |
| `{FOUND_KEY}` | Jira Foundation project key |
| `{MODEL_KEY}` | Jira Modelling project key |
| `{DEV_KEY}` | Jira Development project key |
| `{PROJECT_KEY}` | Default project key |
| `{CURRENT_PHASE}` | Starting phase (usually "Phase A — Discovery") |

## Relationship to development pipeline

This pipeline produces a headless system specification — capabilities,
their APIs, their events, and the journey contracts that describe how
they compose. Channel UIs (web, mobile, branch) sit outside the system
boundary and are a separate development concern.

The handoff point is:

  Stable journey model (Phase C, Gate 2 passed)
  = One buildable Deliverable in the DEV project

Design and development overlap. The first journey can be in production
while the fifteenth journey is still being modelled.

## Pipeline flow

The Capability Lead orchestrates:

```
Phase A+B: Spawn Discovery Team → Gate 1
Phase C:   For each journey:
             1. Spawn Refinement Team → refinement brief
             2. scaffold-journey.py (pre-creation)
             3. Spawn Journey Modelling Team
             4. Spawn Review Team (per artefact)
             5. validate-journey.py (post-creation)
             6. validate-sequences.py (post-creation)
             7. validate-central-model-impact.py (informational)
             8. If fails → back to team
             9. Gate 2 → Handoff to DEV
```

See PIPELINE.md for full orchestration instructions.
