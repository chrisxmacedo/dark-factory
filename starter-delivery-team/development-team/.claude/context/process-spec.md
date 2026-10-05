# Process specification discipline

Read by: Team Lead, every specialist team.

The development pipeline is an application of the operating-model
pattern *deterministic below, agentic above*. Every Jira transition,
branch operation, and gate check is a named process executed by a
deterministic script (`infra/jiractl`, `infra/pipelinectl`,
`infra/envctl`); agents are the reasoning layer that decides which
process to invoke and whether the result is acceptable. This file
makes the discipline concrete.

## 1. Six-field specification

Every script in `infra/` MUST declare these six fields in a comment
block at the top of the file:

| Field | Purpose |
|-------|---------|
| **Inputs** | Typed schema of everything the script accepts (argv, env vars, files read). No implicit parameters. |
| **Outputs** | Typed schema of everything the script returns (files written, Jira transitions performed, exit code). No implicit side channels. |
| **Preconditions** | What must be true before the script runs — Jira credentials present, branch clean, Docker up, etc. Checked at entry; script refuses if unmet. |
| **Postconditions** | What will be true after successful execution (ticket in given status, branch merged, tag created). Caller may rely on this. |
| **Idempotency** | Whether repeated invocation is safe; how duplicates are detected (e.g. Jira transition that is already in the target status). |
| **Audit events** | What is appended to `_audit.jsonl` (at the dev-team root). Non-optional, non-bypassable. |

Convention (bash):

```bash
# short one-line description
#
# six-field spec
#   inputs         $1=TICKET_KEY; reads infra/.env.jira; reads $PROJECT_KEY
#   outputs        Jira transition performed; git branch created; exit 0/1
#   preconditions  infra/.env.jira exists; ticket is in expected source state
#   postconditions ticket is in expected target state; audit line appended
#   idempotency    idempotent (re-running when already in target state is a no-op)
#   audit events   one line: {script, args, exit_code, blockers, warnings}
```

Python scripts use a docstring with the same block.

## 2. Audit log

`infra/audit.sh` provides `audit_log "<script>" <exit_code>
[<blockers>] [<warnings>] [<meta_json>]`. Source it at the top of
every infra script and call `audit_log` on every meaningful gate
decision. Every invocation appends one JSONL line to `_audit.jsonl`
in the dev-team root:

```json
{"ts":"2026-04-19T09:12:33Z","pipeline":"development-team","script":"pipelinectl ci-gate","args":["HIN-22"],"exit_code":1,"blockers":2,"warnings":0,"pid":12345,"meta":{}}
```

The agent never writes `_audit.jsonl` directly. The *script* writes
it, so the record is produced whether or not the agent remembers to
mention it. This is the source of truth for what the pipeline
actually did.

## 3. Named-process-only during gates

During CI gate, RC gate, and release gate evaluation, **agents must
not transition Jira tickets by hand or commit to release branches
through free-form git commands.** All mutations must go through a
named script:

- Transition a ticket → `./jiractl transition <KEY> <TARGET>`
- Comment on a ticket → `./jiractl comment <KEY> "<msg>"`
- Merge feature → ci → `./pipelinectl merge-to-ci <KEY>`
- Cut an RC branch → `./pipelinectl cut-rc <KEY>`
- Merge RC → main + tag + back-merge → `./pipelinectl merge-rc <KEY> <N>`
- Start/stop an environment → `./envctl up|down <ci|rc|prod>`

If no named script exists for the mutation the team needs, the team
must author one (or petition the Team Lead). Agents running raw `git
checkout`, `git merge`, or MCP `transitionJiraIssue` to move around a
gate failure is exactly the failure mode the deterministic substrate
is meant to prevent.

Outside gate evaluation — inside a feature branch, during development
work — free git and free editing is fine; that's the reasoning layer
doing its job.

## 4. Self-critique before signalling complete

Before any team signals `FEATURE DONE`, `CI GATE PASSED`, `RC GATE
PASSED`, `DELIVERABLE DONE`, or `SPEC DEFECT RAISED`, it runs this
checklist:

1. **Evidence present?** Every gate named in the ticket has evidence
   in the expected location — test output, CI logs, verification
   results. No claims without a cited artefact.
2. **Preconditions rechecked?** Did any of my commits invalidate a
   precondition of a downstream stage (e.g. merge order, RC cut
   source)?
3. **Named-process mutations?** Every Jira transition and branch
   operation went through `jiractl` / `pipelinectl`, or the exception
   is noted in the ticket.
4. **Audit line emitted?** `_audit.jsonl` has an entry for every
   gate-level script invocation I made during this step.
5. **Diagnostics triggered correctly?** If a test failed, I did not
   patch around the failure — the Diagnostics Team was called.
6. **Escalation?** If I hit a genuine defect I cannot fix, did I
   raise `FIX EXHAUSTED` / `SPEC DEFECT RAISED` rather than improvise?

A self-critique that skips a bullet is not self-critique. Note any
exceptions in the signal so they are visible rather than buried.

## 5. Rollout discipline

Not every script has a six-field header yet — this discipline is
being rolled out incrementally. When a team touches an infra script
for any reason, it adds the header and the audit call as part of the
same change. The Team Lead tracks coverage in `PIPELINE-STATE.md`
under "Process-spec coverage".

## Never

- Hand-edit `_audit.jsonl`.
- Transition a Jira ticket without going through `jiractl`, unless
  `infra/.env.jira` is missing (in which case fall back to MCP but
  still log the equivalent audit line by hand using `audit_log`).
- Cut an RC from anywhere other than `ci HEAD` via `pipelinectl`.
- Merge a feature PR into a release branch without the CI gate having
  written its audit line.
- Skip self-critique because "the pipeline already passed" — the
  pipeline catches mechanical gaps; self-critique catches reasoning
  gaps.
