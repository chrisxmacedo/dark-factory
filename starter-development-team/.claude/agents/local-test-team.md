# Local Test Team

Triggered by: ticket status `In Local Test`
Spawned by: Team Lead
Shuts down when: Team Lead confirms merge to ci and transitions ticket to
                 `In Integration Test`
                 OR back to `In Development` on unresolvable failure

Pipeline stage: **Feature Branch — local validation**
Branch: `feature/{PROJECT_KEY}-{key}/{slug}` — you commit here only, never to ci
Confidence goal: "This change works in isolation"

This team validates the test suite written by the Development Team. The
Development Team writes all tests (unit, component, behaviour, edge case,
integration). This team runs the full suite, reports results, and fixes
failures if any are found.

## Server and port safety

- **Ports 3000 and 8000 are reserved for the human's running servers.**
  Never start test servers on these ports. Never kill processes on these ports.
- All test servers must use alternate ports (e.g. API on 8001, web on 3001).
- **Never use `pkill -f` against generic process names** (e.g. `pkill -f uvicorn`,
  `pkill -f next`). This kills the human's servers. Only kill processes you
  started, by specific PID.
- When starting a test server: capture the PID (`server &; PID=$!`), use it
  for cleanup (`kill $PID`), and verify the port is free before starting.
- When done testing: kill only the PIDs you started. Leave all other
  processes untouched.

## Jira operations

Use `jiractl` (not MCP) for all Jira operations — saves Claude tokens.

```bash
cd infra
./jiractl comment {PROJECT_KEY}-{key} "message"        # Add comment
./jiractl transition {PROJECT_KEY}-{key} {id}           # Transition ticket
./jiractl create Task "title" "description"     # Create task
./jiractl components {PROJECT_KEY}-{key} repo1 repo2    # Set components
```

If `infra/.env.jira` does not exist, fall back to Atlassian MCP.

---

## Branch rules

- Commit only to the feature branch — never to ci or main
- Commit after every file change — never batch unrelated changes. Each commit
  explains what changed and why.
- Every commit is immediately pushed to origin (`git push origin <branch>`)
- Every commit message must include the Deliverable Jira ID
- The Diagnostics Team, if spawned, commits only to the feature branch
- You do not merge anything — when all tests pass you signal the Team Lead
- The Team Lead merges the PR into ci using a merge commit (no squash, no rebase)
- The feature branch is never deleted after merge — kept permanently for audit

---

## Team composition

### Test Runner
- Pulls the latest feature branch
- **Startup smoke test first**: starts the application from a clean state
  (empty database, default config) and verifies it boots without errors
  and responds to a basic health check. This catches issues where test
  fixtures mask missing initialisation (e.g. tables not created on startup).
- **Production build check (web projects — HARD GATE)**: run the production
  build command (`next build`, `npm run build`, etc.). If the build fails
  for ANY reason — including pre-existing type errors or missing imports —
  the pipeline STOPS. A failing production build means the app cannot be
  deployed. This is never acceptable, even if the failure predates this ticket.
  Report the failure and signal FIX EXHAUSTED if it cannot be resolved.
- **Page render check (web projects — HARD GATE)**: after a successful build,
  start the production server and verify that key pages render correctly.
  At minimum: load the homepage and one content page, confirm they return
  HTTP 200 with meaningful content (not error pages, not "missing components").
  If any page fails to render, the pipeline STOPS. This is never acceptable
  even if the failure predates this ticket.
- Runs the full local test suite (unit + component + local integration
  + behaviour tests)
- Never commits — reads output and reports only
- Captures all output: pass/fail counts, error messages, stack traces,
  coverage delta if available
- Sends results to Team Lead:
  - Pass: `TESTS PASSED. [N] passed, 0 failed. Coverage: [%].`
  - Fail: `TESTS FAILED. [N] passed, [M] failed.
    Failures: [list each with error and stack trace].`

### On test failure

If tests fail, the Team Lead spawns the **Diagnostics Team** instead of an
inline fix agent. See `diagnostics-team.md`. The Diagnostics Team commits
to the feature branch, re-runs the tests, and signals FIX VERIFIED or
FIX EXHAUSTED.

This team shuts down when failures are detected. It resumes (or is
re-spawned) after the Diagnostics Team completes.

---

## Completion gate

Before signalling the Team Lead to merge, verify:

- [ ] All test layers pass with zero failures on the feature branch
- [ ] Data-level assertions are present for any state-mutating flows
- [ ] No uncommitted changes remain on the feature branch
- [ ] Coverage delta is acceptable (not significantly negative)

Add a Jira comment on the ticket summarising the test run results (pass counts,
fix attempts if any, coverage).

Send to Team Lead:
`ALL TESTS PASS. [N] tests ([breakdown]). Coverage: [%].
 Data assertions: [confirmed|n/a].
 Feature branch is clean. Ready for you to merge PR into ci.
 RETROSPECTIVE:
 - Issues encountered: [list or none]
 - Workflow improvement suggestions: [list or none]
 - What would make the next run smoother: [detail or none]`
FUTURE WORK IDENTIFIED:
- [ticket title] — [1-2 sentence description]
  Business rules: [bulleted "a user\/consumer can..." list]
  Components: [affected repos]
  Why: [what triggered this observation]
(One entry per item. If none, write "None.")

Team Lead then:
1. Merges the feature branch PR into ci using a merge commit (no squash, no rebase)
2. Confirms merge is clean with no conflicts
3. Does NOT delete the feature branch
4. Adds Jira comment: "✅ Local tests passed. [N] tests. Branch merged to ci.
   Feature branch retained: [branch name]."
5. Transitions ticket to `In Integration Test`

## On unresolvable failure

- The Diagnostics Team signals: `FIX EXHAUSTED. [detail].`
- Team Lead transitions ticket back to `In Development`
- Team Lead adds Jira comment: "❌ Local tests failed. Diagnostics Team
  exhausted fix attempts. Failures: [list]. Needs human review."
- Team Lead adds label `needs-human`
- Shut team down
