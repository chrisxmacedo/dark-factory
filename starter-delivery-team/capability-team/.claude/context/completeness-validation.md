# Completeness validation

Read by: Capability Lead, Review Team, Journey Modelling Team.

The capability-team pipeline produces a specification that downstream
development teams use to build a real system. A spec with gaps — a
missing error model, an undefined RBAC, no deployment topology — lets
the build team guess, and guessing is where incidents are born.

`scripts/validate-completeness.py` is the deterministic gate that
catches those gaps before they reach the build team. Every Lead runs
it at the gates described below. It is not optional.

## What it checks

Three layers, all declarative in the script's `REQUIREMENTS` and
`DEEP_CHECKS` lists:

1. **Required artefacts exist** — foundation, architecture (including
   the runtime-contract layer: error model, runtime conventions,
   RBAC, deployment topology, SLO catalogue, config schema, data
   retention policy), central model, runtime/operational, test
   fixtures, compliance.
2. **Deep structural checks** — every entity has a primary key, every
   event has a payload schema, every journey has happy/alt/exception
   sequence diagrams, stub markers are surfaced.
3. **Cross-reference resolution** — entity `owning_service` exists in
   the service catalogue; journey `triggering_persona` exists in the
   personas list.

## Severities and exit codes

| Severity | Meaning | Exit code (normal) | Exit code (--strict) |
|----------|---------|--------------------|----------------------|
| blocker  | Must be fixed before the gate passes | 1 | 1 |
| warn     | Surfaced and tracked; non-fatal  | 2 | 1 |

CI and pipeline gates call the validator. In strict mode, warnings
become blockers — use this at programme closure when nothing should
be outstanding.

## When to run

| Moment | Command | Evidence |
|--------|---------|----------|
| **Gate 1 exit** (Phase B → Phase C) | `python3 scripts/validate-completeness.py` | Save to `PIPELINE-STATE.md` ▸ Gate 1 evidence. All blockers MUST be resolved. |
| **After each Gate 2** | `python3 scripts/validate-completeness.py` | Save stdout to `artefacts/models/{slug}/evidence/validate-completeness.txt`. New blockers created by the new journey must be resolved before the next journey starts. |
| **Programme closure** | `python3 scripts/validate-completeness.py --strict` | Exit 0 required. This is the final readiness signal to the Programme Lead. |

## Customising for your project

Projects have different regulatory and operational needs. The defaults
are deliberately generic; promote warnings to blockers when your
project has a specific duty:

- **Regulated (UK banking, insurance, health)** — promote
  `COMPLY-EVIDENCE` to `blocker` and add project-specific artefact
  requirements (e.g. for UK banking: RTS controls mapping, OBIE
  conformance report).
- **High-availability services** — add a `RUN-CHAOS` requirement for
  documented chaos-engineering scenarios.
- **Regulated data residency** — promote `ARCH-RETENTION` to include
  per-jurisdiction evidence.

Edit `REQUIREMENTS` in the script directly. Commit the change with a
message explaining why (the validator's own commit history is the
audit trail for what "complete" means for this project).

## Stub tracking convention

Artefacts may be authored as stubs during active modelling. To stay
within the completeness discipline without blocking progress, mark
them visibly so the validator catches them:

```json
{
  "x-status": "stub",
  "x-todo": "Explain what is missing and who will complete it"
}
```

The validator's `stub-tracking` check counts these and surfaces them
as warnings. A stub is acceptable; an unmarked gap is not.

Typical cases:
- Sequence diagrams for alt/exception paths authored before the
  capability team has fleshed out the narrative.
- Retention rules for an entity whose lifecycle is still being debated.
- Test fixtures for a persona that has not yet been modelled in depth.

When the stub is resolved, remove `x-status` and `x-todo` — the
validator's warning count falls automatically.

## Sequence-diagram pairing

`validate-journey.py` requires every `.mmd` sequence file to be paired
with a `.json` file (the structured source of truth). If you add a
Mermaid stub, create the matching JSON stub at the same time. The
helper `scripts/generate-sequence-json-stubs.py` does this
idempotently — it walks the models tree and creates a matching JSON
stub for any orphan `.mmd` it finds, marked `x-status: "stub"`.

## NEVER

- Mark Gate 1 or Gate 2 passed without running the validator and
  saving its output to evidence.
- Silence a blocker by lowering its severity without a reason recorded
  in the commit message.
- Add an artefact requirement without also updating PIPELINE.md and
  letting teams know.
- Delete a stub marker instead of resolving the underlying gap — the
  spec must accurately reflect what's done.
