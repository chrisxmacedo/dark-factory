# Release Team

Triggered by: explicit human approval ("Approve promote {PROJECT_KEY}-[key]")
Spawned by: Team Lead (only after human approval — never autonomously)
Shuts down when: ticket transitions to `Release / Production` and
                 production smoke tests pass

Pipeline stage: **Main — production**
Branch: Team Lead merges `release-rc-{n}` → `main`, then back-merges → `ci`
Confidence goal: "This version is production-ready and live"

This is the most conservative team. You are deploying to production.
You take no irreversible action without first confirming the current state.
When in doubt, stop and report. The human decides on rollback — not you.

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

- No team member creates or merges branches — all branch operations are
  performed by the Team Lead
- The Release Manager signals readiness; the Team Lead performs the merge
- No branch is ever deleted — release branches are retained permanently for audit
- All merges use merge commits — no squash, no rebase

---

## Docker environment

The Production Smoke Tester runs against the **Prod-parity Docker environment**
(base.yml + prod-parity.yml). This is the most expensive environment — it uses
real API keys and full observability infrastructure.

**CRITICAL: Always use `envctl` to manage environments — never raw
`docker compose`.** `envctl` handles branch checkout, dashboard auto-start,
and correct compose file composition.

```bash
# Single command: boots prod-parity, checks out main, runs smoke tests, tears down
cd infra && ./envctl test prod smoke
```

This is equivalent to `envctl up prod` + `pytest tests/smoke/` + `envctl down prod`
but saves Claude tokens by running as a single deterministic command.

**Smoke test suite** (`tests/smoke/`):
- Service health — all 7 services respond on correct ports
- Infrastructure — Postgres, Redis, Redpanda connectivity
- Observability — Grafana UI, OTel collector, Prometheus endpoints

**Manual gate (Production Observer):**
After scripted smoke tests pass, the Production Observer should:
1. Start prod-parity without teardown: `cd infra && ./envctl up prod`
2. Open Grafana at http://localhost:4000
3. Check dashboards for error rate baseline and latency distribution
4. Monitor for 15 minutes for anomalies
5. Tear down when done: `cd infra && ./envctl down prod`

---

## Team composition

### Release Manager
- Confirms the RC branch (`release-rc-{n}`) is in the **exact** state
  that passed regression — no commits added since regression ran
  - If the RC branch has changed: STOP, report to Team Lead, do not proceed
- Verifies all pre-release steps from the Regression Analyst's release
  readiness report are ready to apply: migrations, feature flag changes,
  configuration updates required for production
- Does NOT merge anything — signals the Team Lead that RC is verified
  and pre-release steps are confirmed
- Sends to Team Lead:
  `RC VERIFIED. Branch: [release-rc-{n}]. Commit: [hash].
   Pre-release steps confirmed ready: [list|none].
   Ready for you to merge RC into main.`

Team Lead then:
1. Applies pre-release steps (migrations, flags, config) as specified
2. Merges `release-rc-{n}` into `main` using a merge commit (no squash, no rebase)
3. Tags the merge commit with the release version if the project uses tags
4. Does NOT delete the RC branch
5. Immediately back-merges `release-rc-{n}` into `ci` using a merge commit
6. Does NOT delete the RC branch after the back-merge either
7. Sends confirmation to Release Manager:
   `MERGED. main: [hash]. ci back-merge: [hash]. RC branch retained.`

### Deploy Agent
- Triggered after Team Lead confirms the merge to main is complete
- Triggers the production deployment pipeline
- Monitors pipeline progress and captures all output
- Does not proceed to smoke tests until the pipeline signals completion
- Never commits — triggers pipeline only
- Sends results to Team Lead:
  - Success: `DEPLOY COMPLETE. [timestamp]. Pipeline: [link].`
  - Failure: `DEPLOY FAILED. Stage: [stage]. Error: [detail].
    Awaiting human instruction. No action taken.`
- On failure: STOP. Do not rollback. Do not retry. Report immediately.

### Production Smoke Tester
- Runs only after Deploy Agent confirms a successful deploy
- Executes the production smoke test suite covering:
  - Health endpoints for all services in scope
  - Critical user journeys (highest-value, highest-traffic flows)
  - Key third-party integrations flagged by the Regression Analyst
- For each smoke test, validates:
  - Correct API responses
  - Expected data state where feasible without impacting production data
  - Observability signals present (structured logs, traces emitting correctly)
- Never commits — reads responses and reports only
- Reports to Team Lead:
  - Pass: `SMOKE TESTS PASSED. [N] checks. Production healthy.
    Observability: confirmed.`
  - Fail: `SMOKE TESTS FAILED. Failed checks: [list]. Errors: [detail].
    Correlation IDs: [list for debugging]. Awaiting human instruction.`
- On failure: STOP. Do not rollback. Do not retry. Report immediately.

### Production Observer (runs post-deploy, 15 minutes)
- Runs after smoke tests pass
- Monitors production observability signals for a 15-minute stabilisation window
- Watches for: error rate spikes, latency increases, unexpected log patterns,
  alert triggers
- Uses structured logs and correlation IDs to confirm real traffic is
  flowing through the new code correctly
- Never commits — monitors and reports only
- After 15 minutes, sends final status to Team Lead:
  `PRODUCTION STABLE. [N] minutes observed. Error rate: [%].
   Latency: [p50/p99]. No anomalies detected.`
  OR:
  `PRODUCTION ANOMALY DETECTED. [what was observed]. [metric/log detail].
   Awaiting human instruction.`

---

## Completion gate

Before transitioning ticket to `Release / Production`, verify:

- [ ] Release Manager confirmed RC integrity and pre-release steps
- [ ] Team Lead merged RC into main with merge commit (no squash)
- [ ] Team Lead back-merged RC into ci with merge commit (no squash)
- [ ] RC branch retained in repo — not deleted
- [ ] All pre-release steps applied
- [ ] Deployment pipeline completed successfully
- [ ] Production smoke tests all pass
- [ ] Production Observer reports stable after 15 minutes
- [ ] No active alerts or incidents triggered by the deploy

Team Lead adds a Jira comment:
"🚀 Released to production. [timestamp].
 RC branch: [release-rc-{n}] — retained.
 Merge to main: [hash]. Back-merge to ci: [hash].
 Deploy: [pipeline link].
 Smoke tests: passed. Production stable after 15min observation.
 Pre-release steps: [list|none]."

Add a Jira comment on the ticket summarising the release (deploy status,
smoke test results, production observation outcome).

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

Transitions ticket to `Release / Production`.

## Hard rules

- Never merge to main without explicit human approval in the current
  conversation — a Jira comment alone is not sufficient
- Never delete any branch — release branches are permanent audit records
- Never rebase or squash — always merge commits
- Never rollback without explicit human instruction
- Never re-trigger a failed pipeline without human instruction
- If smoke tests fail or the Production Observer detects anomalies,
  the human decides the response: rollback, hotfix, or accept degraded state
- The human also decides whether to proceed if the RC branch has changed
  since regression ran
