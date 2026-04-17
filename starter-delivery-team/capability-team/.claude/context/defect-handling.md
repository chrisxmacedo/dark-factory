# Defect handling

Read by: Capability Lead, all agent teams

Where a defect is found determines how it is handled. In all cases, the
team that discovers the defect reports it immediately — no agent silently
continues with incomplete or inconsistent artefacts.

**Cross-pipeline defects** (specification defects discovered during
build, or refinements that invalidate an in-flight Deliverable) are
handled by the Programme Lead — see
`../../../.claude/context/defect-handling.md` at the delivery-team root.
You only act when the Programme Lead opens a refinement ticket in your
`PIPELINE-STATE.md`.

## Where defects are found

### 1. During Phase A + B (Discovery Team)

A step produces an artefact that fails schema validation, contradicts an
earlier step, or cannot be completed because an upstream source is
unavailable.

1. Discovery Team signals `DISCOVERY BLOCKED` to the Capability Lead with:
   - Step number and name
   - Failure (what failed and why)
   - Files completed before failure
   - Files NOT completed
   - Suggested resolution
2. Capability Lead decides: retry the step, roll back to a prior step,
   or escalate to human.
3. Do not proceed to the next step until the blocker is cleared.
4. Update PIPELINE-STATE.md with the blocker and resolution.

### 2. During scaffold (Capability Lead)

`scaffold-journey.py` fails — existing directory, ID scan error, write
permission.

1. Do NOT spawn the Journey Modelling Team.
2. Resolve the scaffold error first.
3. If the scaffold wrote partial output, delete the journey directory
   and re-run. IDs are global so a partial scaffold can be discarded
   without affecting other journeys.

### 3. During modelling (Journey Modelling Team)

A step fails — file write error, central model conflict, schema failure,
tool call error.

1. Journey Modelling Team signals `JOURNEY MODEL BLOCKED` to the Programme
   Lead with step, failure, completed files, uncompleted files, suggested
   resolution.
2. **Never partially update the central model.** Either all central-model
   updates for this journey succeed, or none are applied.
3. Capability Lead decides: re-spawn the modelling team with a fix brief,
   roll back the journey, or escalate to human.

### 4. During central model sync (Journey Modelling Team)

`sync-central-model.py` reports a conflict (e.g. an entity in the journey
data model has fields that differ from the existing central-model entity).

1. Do NOT force the sync.
2. Journey Modelling Team annotates the conflict in the journey's
   `design_decisions` with proposed resolution.
3. Capability Lead reviews — accepts the resolution, requests revisions,
   or escalates to the Architect.
4. Only after explicit resolution is the sync re-run.

### 5. During review (Review Team)

Stage 1 (deterministic): `validate-journey.py` or `validate-sequences.py`
fails.

Stage 2 (reasoning): architectural/consistency/completeness/buildability
issue found.

1. Review Team signals `REVIEW COMPLETE` with verdict `revisions required`
   and an issues list.
2. Capability Lead re-spawns the Journey Modelling Team with the issues
   list as its brief. This is the **remediation cycle**.
3. After remediation, spawn the Review Team again to re-verify.

## Remediation cycles — FIX EXHAUSTED escalation

The remediation cycle is: Review Team finds issues → Journey Modelling
Team fixes → Review Team re-reviews. If the Review Team cannot approve
the journey within **2 remediation cycles**, the Capability Lead declares
`FIX EXHAUSTED`:

| Stage where remediation failed | Escalation |
|-------------------------------|------------|
| Phase A/B step                 | Roll back to previous step. Human reviews both the step instructions and the artefact. |
| Scaffold                       | Inspect `scaffold-journey.py` for a bug. Do not attempt manual scaffolding. |
| Modelling                      | Capability Lead freezes the journey at its current state and escalates the unresolved issues to the human. The journey stays "In progress" — do NOT mark Stable. |
| Central model sync             | Architect and Capability Lead together review the conflict. Resolution may require revising an earlier journey's central-model contribution. |
| Review                         | Journey is held at "In review". Human decides whether to accept with noted issues, send back with expanded guidance, or retire the journey. |

Two cycles is the limit, not the target. If the first remediation cycle
cannot plausibly address the issue list, escalate immediately — do not
burn a second cycle on the same miss.

## Cross-journey regression

When journey N modifies a central-model entity owned by journey N-k, the
earlier journey's artefacts (API contracts, sequence diagrams, events)
may now be inconsistent. This is a **regression**, not a scaffold-time
concern.

1. `sync-central-model.py` flags the impacted prior journeys.
2. `validate-central-model-impact.py` lists the affected artefacts.
3. Capability Lead opens a refinement in PIPELINE-STATE.md linking the
   source journey (N) and impacted journey (N-k).
4. The refinement is scheduled — it is not an emergency unless it blocks
   an in-progress journey. Stable journeys with pending refinements are
   flagged but not automatically reopened.

## Remediation role

The Journey Modelling Team produces **and** fixes its own artefacts
today. This is acceptable while the pipeline is small, but the review
loop should be **independent** — the Review Team never produces
artefacts and never fixes them.

If a project chooses to split the remediation role out later, the
remediation agent receives: the issues list from the Review Team, the
original artefacts, and the journey manifest. It produces fixes and
re-submits. It does not re-run the Review Team's scripts itself — the
Review Team does that on re-submission.

## Reporting discipline

Every blocked signal MUST include:

- **What failed** — a concrete description, not "something went wrong"
- **What succeeded before the failure** — so partial state is visible
- **What did not run** — so the next agent knows what's missing
- **Suggested resolution** — the agent's best hypothesis, even if
  uncertain. This accelerates the Capability Lead's decision.

A silent failure is worse than a loud one. If an agent is uncertain
whether a step succeeded, it reports BLOCKED and lets the Programme
Lead decide.
