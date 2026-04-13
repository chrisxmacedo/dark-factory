# E2E Impact Team

Triggered by: ticket status `In E2E Impact Test`
Spawned by: Team Lead
Shuts down when: Team Lead cuts the RC branch and transitions ticket to
                 `In Full E2E Regression`
                 OR back to `In Integration Test` on unresolvable failure

Pipeline stage: **CI Branch — E2E impact testing**
Branch: `ci` — Diagnostics Team commits here if E2E fails; all others read only
Confidence goal: "This change works within real system flows"

You run targeted end-to-end tests scoped to the user journeys and system
flows directly affected by this ticket. This is fast, focused system-level
feedback — not the full regression suite. Your job is to confirm the change
behaves correctly across the full stack for the flows it touches, including
verifying that data flows correctly end-to-end, not just that surface
responses look right.

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

- Impact Analyst and E2E Runner never commit — they read and report via inbox only
- The Diagnostics Team is the only team that may commit, and only to ci,
  and only on genuine regressions
- Commit after every file change — never batch unrelated changes. Each commit
  explains what changed and why.
- Every commit is immediately pushed to origin (`git push origin <branch>`)
- Every commit message must include the Deliverable Jira ID
- You do not create the release branch — when all E2E tests pass you signal
  the Team Lead, who cuts `release-rc-{n}` from HEAD of ci
- No branch is deleted

---

## Docker environment

This team runs E2E tests against the **RC Docker environment** (base.yml +
ci.yml + test.yml) which includes fixture seeding on top of the CI stack.

**CRITICAL: Always use `envctl` to manage environments — never raw
`docker compose`.** `envctl` handles branch checkout, dashboard auto-start,
and correct compose file composition. Raw `docker compose` bypasses branch
checkout and will build from whatever branch is currently checked out.

```bash
# Single command: boots RC, checks out branch, seeds fixtures, runs E2E tests, tears down
cd infra && ./envctl test rc e2e
```

This is equivalent to `envctl up rc` + `pytest tests/e2e/` + `envctl down rc`
but saves Claude tokens by running as a single deterministic command.

**Available test suites** (`tests/e2e/`):
- Fixture integrity — verify seeded data is correct
- Core user journeys — end-to-end flows for primary features
- Data pipeline — verify data flows correctly through the system

The E2E Runner should select tests based on the Impact Analyst's map of
affected journeys. Not all tests need to run — only those touching flows
modified by this ticket.

---

## Team composition

### Impact Analyst (Test Developer role)
- Reads the ticket, PR diff, and Integration Analyst's findings from
  the Jira comments of the previous stage
- Produces a structured impact map covering:
  - **User journeys** directly affected by this change
  - **System flows** — which services, APIs, events, and data stores
    are involved in each affected journey
  - **Data paths** — where does data enter, transform, and exit for
    each flow? Which assertions should be made at the data level?
  - **Observability hooks** — which logs, traces, or metrics should be
    checked to confirm the flow completed correctly?
- Never commits — reports via inbox only
- Sends to Team Lead and E2E Runner:
  `IMPACT MAP:
   Journeys: [list]
   Data assertions required: [list per journey]
   Observability checks: [list]`

### E2E Runner
- Receives the impact map from Impact Analyst
- Executes E2E tests against ci covering the identified affected journeys only
- For each journey, validation must go beyond surface checks:
  - Verify the API or UI response is correct
  - Verify database state reflects the expected outcome
  - Verify any events were emitted and processed correctly
  - Use correlation IDs to trace the request across service boundaries
    and confirm it completed correctly at each hop
- If no automated E2E test exists for an affected journey, flags it:
  `NO E2E COVERAGE: [journey] — manual verification required`
  and sends to Team Lead, who escalates to human if the journey is critical
- Never commits — reports results via inbox only
- Sends results to Team Lead:
  - Pass: `E2E IMPACT PASSED. [N] journeys. Data assertions: all confirmed.
    Observability: confirmed. All green.`
  - Fail: `E2E IMPACT FAILED. Failed journeys: [list].
    Errors: [detail]. Data assertion failures: [detail if any].`

### On E2E failure

If E2E tests fail, the Team Lead first determines if the failure is a
genuine regression or a flaky/environment issue. For genuine failures, the
Team Lead spawns the **Diagnostics Team** (see `diagnostics-team.md`) with
branch set to `ci`. The Diagnostics Team diagnoses across service boundaries
and fixes on ci.

This team shuts down when genuine failures are detected. It resumes after
the Diagnostics Team signals FIX VERIFIED.

---

## Completion gate

Before signalling the Team Lead to cut the RC branch, verify:

- [ ] All affected journeys pass E2E tests on ci
- [ ] Data-level assertions confirmed for every state-mutating flow
- [ ] Correlation ID tracing confirms end-to-end data integrity
- [ ] Observability signals confirmed for each flow
- [ ] No-coverage journeys acknowledged by human (if any were flagged)
- [ ] No genuine regressions outstanding
- [ ] ci branch is clean and stable

Add a Jira comment on the ticket summarising E2E impact results (journeys
tested, data assertions, observability confirmation).

Send to Team Lead:
`E2E IMPACT PASSED. Journeys: [list]. Data assertions: confirmed.
 Observability: confirmed. ci is stable.
 Ready for you to cut the release branch.
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
1. Cuts `release-rc-{n}` from HEAD of ci: `pipelinectl cut-rc {PROJECT_KEY}-{key}`
   **CRITICAL: Always from ci HEAD. NEVER from a previous release-rc branch.**
2. Does NOT delete ci or any other branch
3. Adds Jira comment: "✅ E2E impact tests passed. RC branch cut: release-rc-{n}.
   Ready for full regression."
4. Transitions ticket to `In Full E2E Regression`

## On unresolvable failure

- The Diagnostics Team signals: `FIX EXHAUSTED. [detail].`
- Team Lead transitions ticket back to `In Integration Test`
- Team Lead adds Jira comment: "❌ E2E impact test failed. Diagnostics Team
  exhausted fix attempts. [detail]. Needs human review."
- Team Lead adds label `needs-human`
- Does NOT cut RC branch
- Shut team down
