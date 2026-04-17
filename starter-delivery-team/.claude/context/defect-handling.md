# Defect handling — cross-pipeline

Read by: Programme Lead

Each sub-pipeline handles its own defects. This file covers only the
cross-boundary cases where the Programme Lead is involved.

- In-capability defects → `capability-team/.claude/context/defect-handling.md`
- In-build defects → `development-team/.claude/context/defect-handling.md`

## Three cross-pipeline cases

### 1. Specification defect discovered during build

The Diagnostics Team (inside the dev pipeline) concludes that the
defect's root cause is in the specification — an API contract that
contradicts itself, an event schema that cannot be produced from the
data model, a sequence diagram whose cross-capability event does not
match the event catalogue, etc.

**Team Lead action:** signals `SPEC DEFECT RAISED` to the Programme
Lead, attaches the Diagnostics report to the DEV ticket, transitions
the ticket back to Backlog with a `spec-defect` label.

**Programme Lead action:**
1. Read the Diagnostics report.
2. Open a refinement in `capability-team/PIPELINE-STATE.md` under
   "Open refinement tickets" with the source DEV key, target journey
   slug, and a one-line summary.
3. Notify the Capability Lead (update
   `capability-team/PIPELINE-STATE.md` — "Last action" field).
4. Update top-level `PIPELINE-STATE.md` — Cross-pipeline defects table.
5. The DEV Deliverable stays in Backlog until the capability team
   releases a refined Stable journey.

Never route a spec defect to the Team Lead for in-code workaround —
the specification must be corrected first.

### 2. Capability-team refinement invalidates an in-flight Deliverable

While the dev team is building DEV-42 (implementing journey JRN-003),
the capability team runs a refinement on JRN-001 that changes the
Customer entity's field set. JRN-003 depends on those Customer fields.

**How it gets noticed:** `validate-central-model-impact.py` output in
a later journey flagged DEV-42's dependencies, OR the Team Lead's
Refinement Team noticed when decomposing.

**Programme Lead action:**
1. Decide whether the in-flight Deliverable can still ship as-is or
   must pause.
2. If pause: ask the Team Lead to transition DEV-42 back to Backlog
   with a `blocked-by-refinement` label and a comment linking the
   refinement.
3. Track both the refinement and the paused Deliverable in top-level
   `PIPELINE-STATE.md`.
4. When the refinement completes, notify the Team Lead that DEV-42
   is unblocked; append to `workflow-improvements.md` if the
   invalidation was avoidable.

### 3. FIX EXHAUSTED in either sub-pipeline

The Capability Lead declares FIX EXHAUSTED after two Review Team
remediation cycles on a journey. OR the Team Lead declares FIX
EXHAUSTED after two Diagnostics cycles on a Deliverable.

**Programme Lead action:**
1. Freeze the affected work — journey stays "In review" or Deliverable
   stays in its current stage, not transitioned.
2. Read the failing cycle's evidence:
   - Capability side: `capability-team/artefacts/models/{slug}/evidence/`
   - Build side: the DEV ticket's Diagnostics comments
3. Report to the human with a single-screen summary:
   - Which sub-pipeline
   - Which journey / Deliverable
   - Both remediation attempts summarised
   - What the Programme Lead thinks the options are (not what it
     decides — the human decides)
4. Do NOT spawn a third remediation cycle without explicit human
   direction.
5. Append the escalation to `workflow-improvements.md`.

## Deciding where a defect belongs

A simple test: can the defect be fixed by changing the specification
alone, without changing code?

- **Yes** → specification defect → capability team refinement
- **No, the spec is correct but the code does not match it** →
  build-pipeline defect → Diagnostics Team (dev-pipeline)
- **Both** → specification is incomplete **and** code is broken —
  start with the specification fix; the code fix follows once the
  spec is settled.

If the test is ambiguous, default to routing to the capability team.
It is cheaper to revise a specification than to un-ship an
implementation.
