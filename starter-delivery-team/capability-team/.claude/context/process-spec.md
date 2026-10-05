# Process specification discipline

Read by: Capability Lead, every specialist team.

The capability pipeline is an application of the operating-model
pattern *deterministic below, agentic above*. Every artefact-producing
action is a named process carried out by a deterministic script;
agents reason about which process to invoke and whether the result is
satisfactory. This file makes the discipline concrete so the next team
picks it up without having to re-derive it.

## 1. Six-field specification

Every script in `scripts/` MUST declare these six fields in a comment
block at the top of the file:

| Field | Purpose |
|-------|---------|
| **Inputs** | Typed schema of everything the script accepts (argv, files read). No implicit parameters. |
| **Outputs** | Typed schema of everything the script returns (files written, exit code, stdout contract). No implicit side channels. |
| **Preconditions** | What must be true before the script runs. Checked at entry; script refuses if unmet. |
| **Postconditions** | What will be true after successful execution. Callers may rely on this. |
| **Idempotency** | Whether repeated invocation is safe; how duplicates are detected. |
| **Audit events** | What is appended to `artefacts/_audit.jsonl`. Non-optional, non-bypassable. |

Convention:

```python
"""
Short one-line description.

six-field spec
  inputs         argv[1]=slug; reads artefacts/models/{slug}/**
  outputs        stdout + exit 0/1/2; writes artefacts/models/{slug}/evidence/<name>.txt
  preconditions  journey directory exists; schemas/ present
  postconditions evidence file exists; audit line appended
  idempotency    idempotent (re-run produces identical verdict for an unchanged tree)
  audit events   one line: {script, args, exit_code, blockers, warnings}
"""
```

Bash scripts use the same block as a `#`-prefixed comment.

## 2. Audit log

`scripts/audit.py` provides `log_event(...)` and a `@wrap(...)`
decorator. Every invocation of a named process appends one JSONL line
to `artefacts/_audit.jsonl`:

```json
{"ts":"2026-04-19T09:12:33Z","pipeline":"capability-team","script":"validate-completeness","args":["--strict"],"exit_code":1,"blockers":3,"warnings":0,"pid":12345,"meta":{}}
```

The agent never writes to `_audit.jsonl` directly. The *script* writes
it, which means the record is produced whether or not the agent
remembers to mention it. This is the point — the audit trail is the
source of truth for what happened, and nothing else counts.

## 3. Named-process-only during gates

During Gate 1 evaluation, per-journey Gate 2 evaluation, and programme
closure, **agents must not edit artefact files directly to fix
validator failures.** All mutations must go through a named script:

- Fix a sequence-diagram orphan → run `generate-sequence-json-stubs.py`
- Fix annotated IDs → run `cleanup-ids.py`
- Sync central model → run `sync-central-model.py`
- Scaffold new journey → run `scaffold-journey.py`

If no named script exists for the mutation the team needs, the team
must author one (or petition the Capability Lead to). Agents editing
JSON by hand to make a validator pass is the exact failure mode the
deterministic substrate is meant to prevent.

Outside gate evaluation — during artefact authoring itself — free
editing is fine; that's the reasoning layer doing its job.

## 4. Self-critique before signalling complete

Before any team signals `DISCOVERY COMPLETE`, `JOURNEY MODEL COMPLETE`,
`REVIEW COMPLETE`, or `REFINEMENT COMPLETE`, it runs this checklist:

1. **Inputs honoured?** Did I use every input the brief mentioned?
2. **Outputs shaped?** Does every required artefact exist and validate?
3. **Preconditions rechecked?** Did any of my writes invalidate a
   precondition of a downstream script?
4. **Named-process mutations?** Every change I made went through a
   named script, or was an authoring change outside a gate window.
5. **Audit line emitted?** `_audit.jsonl` has an entry for every
   script I invoked.
6. **Escalation?** If I hit ambiguity my brief did not resolve, did I
   surface it rather than improvise?

A self-critique that skips a bullet is not self-critique. Note any
exceptions in the signal to the Capability Lead so the exception is
visible rather than buried.

## 5. Rollout discipline

Not every script has a six-field header yet — this discipline is
being rolled out incrementally. When a team touches a script for any
reason, it adds the header and the audit call as part of the same
change. The Capability Lead tracks coverage in
`PIPELINE-STATE.md` under "Process-spec coverage".

## Never

- Hand-edit `_audit.jsonl`.
- Claim a script is idempotent without declaring it.
- Introduce a named process without the six-field header.
- Skip self-critique because "the validators already passed" — the
  validators catch structural gaps; self-critique catches reasoning
  gaps.
- Edit artefact JSON during a gate window to make a validator quiet.
