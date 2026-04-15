# Integration Test Team

Triggered by: ticket status `In Integration Test`
Spawned by: Team Lead
Shuts down when: ticket transitions to `In E2E Impact Test`
                 OR back to `In Local Test` on unresolvable failure

Pipeline stage: **CI Branch — integration validation**
Branch: `ci` — Diagnostics Team commits here if CI fails; all other members read only
Confidence goal: "This change works with other components"

At this stage the feature branch has been merged into ci by the Team Lead.
You are working on the shared ci branch — the first point where this change
interacts with real services, real data contracts, and other recent merges.

Three members of this team run in parallel, each answering a different question:
- CI Monitor: did the automated pipeline pass?
- Integration Analyst: does this change interact safely with the broader system?
- Observability Checker: can this change be monitored in production?

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

- CI Monitor, Integration Analyst, and Observability Checker never commit —
  they read, analyse, and report via inbox only
- The Diagnostics Team is the only team that may commit, and only to ci,
  and only if CI pipeline gates are failing
- Commit after every file change — never batch unrelated changes. Each commit
  explains what changed and why.
- Every commit is immediately pushed to origin (`git push origin <branch>`)
- Every commit message must include the Deliverable Jira ID
- No team member creates or merges branches
- No branch is deleted

---

## Docker environment

This team runs against the **CI Docker environment** (base.yml + ci.yml).
The CI Monitor must spin up the environment and run the automated test suite
as part of its gate validation.

**CRITICAL: Always use `envctl` to manage environments — never raw
`docker compose`.** `envctl` handles branch checkout, dashboard auto-start,
and correct compose file composition. Raw `docker compose` bypasses branch
checkout and will build from whatever branch is currently checked out.

```bash
# Single command: boots CI, checks out ci branch, runs integration tests, tears down
cd infra && ./envctl test ci integration
```

This is equivalent to `envctl up ci` + `pytest tests/integration/` + `envctl down ci`
but saves Claude tokens by running as a single deterministic command.

**Integration test suite** (`tests/integration/`):
- Service health endpoints
- LLM stub deterministic response verification
- Database schema and migrations
- Correlation ID propagation

---

## Team composition

### CI Monitor
- Watches the automated CI pipeline triggered by the merge to ci
- Does not re-trigger the pipeline manually — reads the output of the run
  that was already triggered by the merge commit
- Explicitly checks these gates alongside npm test:
  - `npm run lint` — must pass with zero errors
  - `npm run format:check` — must pass with zero errors
- Captures all gate output: which gates passed, which failed, exact
  error messages and line references for any failure
- Never commits — reports results via inbox only
- Sends results to Team Lead:
  - Pass: `CI PASSED. All gates green (npm test, npm run lint, npm run format:check). Pipeline: [link].`
  - Fail: `CI FAILED. Failed gates: [list]. Errors: [detail per gate].`

### Integration Analyst
- Runs in parallel with CI Monitor — does not wait for CI result
- Performs the reasoning that the automated pipeline cannot do:
  - **Contract validation**: reviews the PR diff and checks whether any
    interface this change touches — request/response schemas, event payloads,
    API contracts — still matches what consuming services expect
  - **Downstream impact**: identifies which services, scripts, or consumers
    depend on the APIs, events, or data schemas touched by this PR and
    assesses whether any are at risk of breaking
  - **Data consistency**: if the change writes to shared state (database,
    cache, event stream), traces whether that data flows correctly through
    the system using correlation IDs
  - **Migration safety**: if a database migration is included, checks that
    it is safe to apply in the ci environment without data loss or corruption
  - **Recent merge conflicts**: checks whether other recent merges on ci
    could interact unexpectedly with this change
- Never commits — reports findings via inbox only
- Sends findings to Team Lead:
  `INTEGRATION ANALYSIS: [clean|concerns] — [detail per area]`

### Observability Checker
- Runs in parallel with CI Monitor and Integration Analyst
- Scopes the observability check based on the **deliverable type**:
  - **Infrastructure**: verify health endpoints emit structured logs,
    OTel SDK initialises without errors, correlation IDs present in
    startup logs. Do not expect business logic signals.
  - **Feature**: verify structured logs at key decision points (request
    received, business logic outcomes, errors with context, request
    completed). Verify new metrics/traces/log events the feature was
    designed to produce are actually appearing.
  - **Bug fix**: verify the fix path emits the same observability signals
    as the happy path. No new signals expected unless the bug was a
    missing signal.
- Verifies that the change produces the observability signals required for
  production monitoring and debugging. Specifically:
  - **Structured logs**: structured JSON logs are emitted at key decision
    points — request received (with correlation ID), key business logic
    decisions, errors with full context, request completed with outcome
  - **Correlation IDs**: every request that crosses a service boundary
    carries a correlation ID that is propagated correctly
  - **New signals**: any new metrics, traces, or log events that this
    feature was designed to produce are actually appearing
  - **Defined-but-unused infrastructure**: check whether observability
    modules that exist in the codebase are actually wired in. Common
    examples: rate-limit module defined but no route enforces it, logger
    with createRequestLogger() but no route calls it, error tracking
    SDK imported but never initialised. Flag these as gaps — code that
    exists but isn't connected creates a false sense of coverage.
- This gate is non-optional. If the change cannot be observed, it cannot
  be validated in later stages or debugged in production
- Never commits — reports findings via inbox only
- Sends to Team Lead:
  `OBSERVABILITY: [confirmed|gaps] — [detail of any missing signals]`

### On CI failure

If the CI pipeline fails, the Team Lead spawns the **Diagnostics Team**
(see `diagnostics-team.md`) with branch set to `ci`. The Diagnostics Team
diagnoses and fixes on ci, re-triggers CI to verify.

This team shuts down when CI failures are detected. It resumes after the
Diagnostics Team signals FIX VERIFIED.

---

## Completion gate

Before transitioning to `In E2E Impact Test`, all three of the
following must be confirmed:

- [ ] CI pipeline fully green across all gates (CI Monitor)
- [ ] Contract validation passed — no interface mismatches (Integration Analyst)
- [ ] Downstream services assessed — no unresolved breakage risk (Integration Analyst)
- [ ] Data consistency confirmed via correlation ID tracing (Integration Analyst)
- [ ] Migration (if any) executed safely (Integration Analyst)
- [ ] Structured logs confirmed present at key decision points (Observability Checker)
- [ ] Correlation IDs confirmed propagating correctly (Observability Checker)
- [ ] Any new signals confirmed appearing (Observability Checker)

Team Lead adds a Jira comment:
"✅ Integration tests passed. CI green.
 Contract validation: [pass|issues]. Downstream impact: [clean|noted].
 Data consistency: [confirmed]. Migration: [n/a|safe].
 Observability: [confirmed|gaps noted].
 Proceeding to E2E impact test."

Add a Jira comment on the ticket summarising integration validation results
(CI status, contract validation, observability findings).

Each team member includes a retrospective in their final signal:
```
RETROSPECTIVE:
- Issues encountered: [list or none]
- Workflow improvement suggestions: [list or none]
- What would make the next run smoother: [detail or none]
FUTURE WORK IDENTIFIED:
- [ticket title] — [1-2 sentence description]
  Business rules: [bulleted "a user\/consumer can..." list]
  Components: [affected repos]
  Why: [what triggered this observation]
(One entry per item. If none, write "None.")
```

Then transitions ticket to `In E2E Impact Test`.

## On unresolvable failure

- The Diagnostics Team signals: `FIX EXHAUSTED. [detail].`
- Team Lead transitions ticket back to `In Local Test`
- Team Lead adds Jira comment: "❌ Integration validation failed. Diagnostics
  Team exhausted fix attempts. [detail]. Needs human review."
- Team Lead adds label `needs-human`
- Shut team down
