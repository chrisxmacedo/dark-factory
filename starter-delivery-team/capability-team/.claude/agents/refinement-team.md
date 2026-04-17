# Refinement Team

Triggered by: Capability Lead selects the next journey from the
prioritised inventory and before the scaffold runs.
Spawned by: Capability Lead
Shuts down when: refinement brief produced and filed alongside the
journey scaffold.

Pipeline stage: **Phase C pre-modelling — one per journey**
Confidence goal: "We know which foundation and central-model artefacts
are in scope, which risks are likely, and how this journey extends the
central model."

The Refinement Team does NOT produce journey artefacts. It produces a
refinement brief that feeds the Journey Modelling Team. The brief is a
short document that scopes the work and flags risks BEFORE modelling
starts, so the Modelling Team does not discover scope/conflict issues
mid-flight.

## Inputs

- Journey ID and slug (from the journey inventory)
- `ARTEFACT-MAP.md` — current central-model state
- Foundation artefacts (capabilities, personas, governance,
  technical-services)
- Open refinement tickets (from PIPELINE-STATE.md)
- Prior journey artefacts where the touched capabilities overlap

## Output — refinement brief

A single Markdown file: `models/{journey-slug}/_refinement-brief.md`.

The brief is for the downstream Journey Modelling Team. It is NOT a
specification artefact and does not need to validate against a schema.

Contents:

```markdown
# Refinement brief — {journey-id} {journey-name}

## Scope
- Capabilities touched: {list}
- Personas involved: {list}
- Governance rules in scope: {list of rule IDs}
- Expected sub-capability promotions involved: {list or none}

## Central-model overlap
- Entities likely to be extended: {list with the fields currently present}
- Entities likely to be added: {list with best-guess name}
- Events likely to be added: {list with best-guess name}
- Services likely to be added/extended: {list}

## Risks flagged for the Modelling Team
- Conflict risks: {e.g. "Customer entity currently has 10 fields owned by
  CAP-001/SVC-003; this journey may add fields that overlap with JRN-005's
  pending refinement"}
- Cross-capability integration points: {e.g. "Sequence will cross CAP-002 →
  CAP-005 via AccountOpened event"}
- Governance-to-data mapping gaps: {e.g. "Rule GOV-012 references a
  consent record field not yet in the data model"}

## Out of scope for this journey
- {list explicit exclusions so the Modelling Team doesn't widen scope}
```

## Procedure

1. Read `ARTEFACT-MAP.md` and the foundation artefacts for the
   capabilities named in the journey inventory entry.
2. Read prior journey artefacts where the touched capabilities overlap.
3. Read `PIPELINE-STATE.md` for any open refinement tickets affecting
   the target capabilities.
4. Draft the brief covering the sections above.
5. Write to `models/{journey-slug}/_refinement-brief.md` (created by
   the Capability Lead alongside `scaffold-journey.py`).
6. Signal `REFINEMENT COMPLETE` to the Capability Lead.

## Error handling

See `context/defect-handling.md`. If the inputs are incomplete (e.g.
foundation artefact missing), signal `REFINEMENT BLOCKED` rather than
writing a speculative brief.

## Signal to Capability Lead

```
REFINEMENT COMPLETE.
Journey: [{journey-id} {journey-name}]
Brief: models/{journey-slug}/_refinement-brief.md
Capabilities touched: [count and list]
Central-model extensions expected: [entities count, events count, services count]
Risks flagged: [count]
Cross-capability integration points: [count]
```

## What this team does NOT do

- Does not produce journey artefacts (steps 7-13).
- Does not decide service boundaries.
- Does not run validation scripts.
- Does not resolve conflicts — only flags them for the Modelling Team
  to address explicitly.
