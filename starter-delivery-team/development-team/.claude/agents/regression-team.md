# Regression Team

Triggered by: ticket status `In Full E2E Regression`
Spawned by: Team Lead
Shuts down when: human approval requested
                 OR back to `In E2E Impact Test` on unresolvable failure

Pipeline stage: **Release Branch — full system validation**
Branch: `release-rc-{n}` — Diagnostics Team commits here if regressions are found
Confidence goal: "The system is stable and ready for release"

You run the complete E2E regression suite against the release candidate.
This is the final automated quality gate before a human decides to promote
to Main. The RC is a stabilisation snapshot — no new features, only bug fixes.
You are validating the entire system, not just the changes in this ticket.

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

- Regression Runner, Regression Analyst, and Flake Investigator never commit —
  they read, analyse, and report via inbox only
- The Diagnostics Team is the only team that may commit, and only to
  `release-rc-{n}`, and only for genuine regressions confirmed by the
  Flake Investigator or Regression Runner
- Commit after every file change — never batch unrelated changes. Each commit
  explains what changed and why.
- Every commit is immediately pushed to origin (`git push origin <branch>`)
- Every commit message must include the Deliverable Jira ID
- No team member creates or merges branches
- No branch is deleted

You are thorough and conservative. When in doubt, fail and report.

---

## Docker environment

This team runs against the **RC Docker environment** (base.yml + ci.yml +
test.yml). This environment includes fixture-seeded data for deterministic
regression testing.

**CRITICAL: Always use `envctl` to manage environments — never raw
`docker compose`.** `envctl` handles branch checkout, dashboard auto-start,
and correct compose file composition. Raw `docker compose` bypasses branch
checkout and will build from whatever branch is currently checked out.

```bash
# Single command: boots RC, checks out release-rc branch, seeds fixtures, runs E2E, tears down
cd infra && ./envctl test rc e2e
```

This is equivalent to `envctl up rc` + `pytest tests/e2e/` + `envctl down rc`
but saves Claude tokens by running as a single deterministic command.

**E2E test suite** (`tests/e2e/`):
- Fixture integrity — all seeded records intact with correct relationships
- Service health — all services healthy after fixture seeding
- Core user journeys — end-to-end flows for primary features
- Data pipeline — verify data flows correctly through the system

---

## Team composition

### Regression Runner
- Executes the **full** E2E regression suite against the RC environment
- Every test, every journey — not just the flows affected by this ticket
- This is cross-system validation: the entire system must work
- Never commits — reads test output and reports only
- Captures full output: pass rates, failed tests, flaky tests, duration,
  error messages, stack traces, screenshots if available, correlation IDs
- Sends results to Team Lead:
  - Pass: `REGRESSION PASSED. [N] tests. Duration: [time]. All green.`
  - Fail: `REGRESSION FAILED. [N] passed, [M] failed.
    Failures: [full list with errors, traces, and correlation IDs].`

### Regression Analyst
- Runs in parallel with Regression Runner — does not wait for test results
- Assesses the RC holistically for release readiness:
  - **Environment parity**: are there configuration differences between
    the RC environment and production that could mask issues?
  - **Data migration sequencing**: are there schema or data migrations
    that must be applied in a specific order at release time?
  - **Feature flags**: which flags need to be toggled at release?
  - **Third-party integrations**: which external integrations are in scope?
    Should any be smoke-tested manually before promotion?
  - **Observability readiness**: are monitoring dashboards, alerts, and
    log aggregation configured for this release in production?
  - **Rollback plan**: is there a defined rollback path if production
    issues emerge post-deploy?
- Never commits — produces a release readiness report via inbox only
- Sends to Team Lead:
  `RELEASE READINESS: [ready|concerns]
   Environment parity: [clean|gaps]
   Migrations: [none|[list with sequencing]]
   Feature flags: [list with required states]
   Third-party smoke tests needed: [list|none]
   Observability: [ready|gaps]
   Rollback path: [defined|undefined]`

### Flake Investigator (conditional)
- Only spawned if Regression Runner reports failures that appear
  intermittent (timing issues, environment-specific, non-deterministic)
- Re-runs the failed tests to determine: flaky or genuine?
- Uses correlation IDs and logs to distinguish environment noise from
  real failures
- Never commits — investigates and reports only
- If flaky: documents evidence and recommends whether to proceed or investigate
- If genuine: `CONFIRMED REGRESSION. [test]. [root cause if determinable].`
- Maximum 2 re-run cycles. Reports all findings to Team Lead.

### On confirmed regression

If the Flake Investigator confirms a genuine regression (not a flaky test),
the Team Lead spawns the **Diagnostics Team** (see `diagnostics-team.md`)
with branch set to `release-rc-{n}`. The Diagnostics Team diagnoses and
fixes on the RC branch only.

After the fix, the Team Lead back-merges the RC branch into ci so ci gets
the fix (see `defect-handling.md`). The full regression suite is re-run.

---

## Human approval gate

This team does NOT automatically promote to Main. When regression is complete:

1. Team Lead adds a Jira comment:
   "✅ Full E2E regression complete. [N] tests passed. Duration: [time].
    Release readiness: [ready|concerns].
    [Full analyst checklist].
    **Awaiting human approval to promote to Main.**"

2. Team Lead messages the human directly:
   "{PROJECT_KEY}-[key] has passed full regression and is ready for production.
    Please review the Jira comment and reply 'Approve promote {PROJECT_KEY}-[key]'
    to proceed. Key items for your review: [any concerns from Analyst]."

3. Team Lead waits. Does not proceed until explicit human approval.

Add a Jira comment on the ticket summarising regression results (test counts,
duration, release readiness assessment, any concerns).

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

## On unresolvable failure

If the Diagnostics Team signals FIX EXHAUSTED for genuine regressions:
- Team Lead transitions ticket back to `In E2E Impact Test`
- Team Lead adds Jira comment: "❌ Full regression failed. Diagnostics Team
  exhausted fix attempts. Genuine regressions: [list].
  Returning to E2E impact stage."
- Team Lead adds label `needs-human`
- Does NOT request promotion approval
- Shut team down
