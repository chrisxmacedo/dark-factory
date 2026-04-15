# Defect handling

Read by: Team Lead, Diagnostics Team, all test teams

Where a defect is found determines how it is handled. In all cases, the
**Diagnostics Team** (`diagnostics-team.md`) is spawned by the Team Lead
to investigate and fix — individual teams do not have inline fix agents.

## Found on the feature branch (Local Test, Development)

The defect is in code that hasn't merged yet — fix it in place.

1. Add a Jira comment on the Deliverable: "❌ [test/stage] failed. [what failed]."
2. Team Lead spawns the **Diagnostics Team** with:
   - Branch: `feature/{PROJECT_KEY}-{key}/{slug}`
   - Failure context: error output from the test/build
3. Diagnostics Team investigates, fixes on the feature branch, verifies
4. Do NOT create a separate Issue ticket — the Deliverable owns the fix
5. When fixed (FIX VERIFIED), the pipeline resumes from the stage that failed

## Found on the ci branch (Integration Test, E2E Impact Test)

The defect appeared after merging to ci — fix it on ci.

1. Add a Jira comment: "❌ [stage] failed on ci. [what failed]."
2. Team Lead spawns the **Diagnostics Team** with:
   - Branch: `ci`
   - Failure context: CI gate output or E2E test failures
3. Diagnostics Team investigates (may be cross-service), fixes on ci, verifies
4. When fixed, the pipeline resumes from the stage that failed

## Found on the RC branch (Full E2E Regression)

The defect is in release candidate code — fix it on the RC branch, then
propagate back to ci.

1. Create an **Issue** ticket in Jira describing the regression
2. Team Lead spawns the **Diagnostics Team** with:
   - Branch: `release-rc-{n}` (not ci, not main)
   - Failure context: regression test output
3. Diagnostics Team investigates and fixes on the RC branch
4. After the fix, Team Lead **merges the RC branch back into ci**:
   ```bash
   git checkout ci && git merge --no-ff release-rc-{n} -m "Back-merge RC fix for {PROJECT_KEY}-{issue}"
   git push origin ci
   ```
5. Re-run the full regression suite on the RC branch (`envctl test rc`)
6. Only proceed to human approval when regression is fully green
7. Do NOT cut a new RC — fix the existing one

## Found in production (Release / Production)

The defect is in live code — raise it as an Issue for prioritisation.

1. Create an **Issue** ticket in Jira with full details (steps to reproduce,
   expected vs actual, severity, affected users)
2. Add label `production-defect`
3. The human decides priority and whether it needs a hotfix or goes into
   the normal backlog
4. Do NOT attempt to fix production defects autonomously — report and wait

## Infrastructure config defects (infra/ directory)

The `infra/` directory (Docker Compose files, env files, scripts) is NOT a git
repo — it lives at the project level. The Diagnostics Team cannot commit fixes
through the normal branch workflow.

When a defect is in infrastructure config (e.g. Docker Compose build args,
env file values, port mappings):

1. Diagnostics Team diagnoses the issue and reports `FIX IDENTIFIED`
   with the exact file, line, and change needed
2. **The Team Lead applies the fix directly** to the infra/ file
3. Team Lead rebuilds the affected environment (`envctl rebuild {env}`)
4. Team Lead re-runs the test suite to verify

This is acceptable because infra/ config is operational configuration, not
application code. Changes should still be logged in `workflow-improvements.md`.

## Escalation (FIX EXHAUSTED after 2 attempts)

If the Diagnostics Team cannot resolve the defect in 2 cycles:

| Stage | Escalation |
|---|---|
| Feature / Local Test | Transition back to In Development, add `needs-human` |
| Integration / E2E | Transition back to In Local Test, add `needs-human` |
| Regression | Halt release, report to human with full diagnostic detail |
| Production | Update Issue ticket with diagnosis, human prioritises |
