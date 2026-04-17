# Pipeline best practices — Orchestration

Read by: Team Lead only

Covers: polling, claiming, spawning, gating, transitions, scripts, and session management

## Polling

- `jiractl poll` (scripted) — finds tickets in actionable statuses
- Process one ticket at a time — finish before starting the next
- The Team Lead may autonomously pick the next Deliverable from the backlog
  without human approval. Follow Initiative order and dependency chains.
- Strictly ONE Deliverable in a non-Backlog, non-Done status at any time
- `pipelinectl needs-claude {KEY}-{key}` — check if Claude is needed or scripts suffice

## Claiming

- `jiractl transition` + `jiractl comment` (scripted) — no MCP, no tokens
- Transition to "In..." status immediately to prevent double-claiming
- Confirm transition succeeded before proceeding

## Spawning rules

- **NEVER combine multiple pipeline stages into one agent spawn**
- Each stage is a separate invocation — Development, Local Test, Integration, E2E Impact, Regression, Release
- Exception: `pipelinectl` scripts handle mechanical gates without spawning Claude
- Before spawning: check for rate limit warnings — if present, wait for reset

## Scripts vs Claude

| Operation | Tool | Tokens? |
|---|---|---|
| Jira transitions, comments, polling | `jiractl` | No |
| Local test gates (test, build, lint) | `pipelinectl local-gate` | No |
| CI gates (test, lint, format, integration) | `pipelinectl ci-gate` | No |
| Merge feature → ci | `pipelinectl merge-to-ci` | No |
| Cut RC from ci | `pipelinectl cut-rc` | No |
| Merge RC → main + tag + back-merge | `pipelinectl merge-rc` | No |
| Docker rebuild + test | `envctl rebuild` + `envctl test` | No |
| Development (writing code) | Agent spawn | Yes |
| Integration analysis + observability | Agent spawn | Yes |
| E2E journey analysis | Agent spawn | Yes |
| Regression analysis (release readiness) | Agent spawn | Yes |
| Production observation (15 min) | Agent spawn | Yes |
| Fix Agent (diagnose + fix failures) | Agent spawn | Yes |

**Rule:** Always check if a script can do it before spawning an agent.

## Mandatory rebuilds

After EVERY branch operation, rebuild the corresponding Docker environment:

| Event | Commands |
|---|---|
| Merge to ci | `envctl rebuild ci && envctl test ci` |
| Cut RC | `envctl rebuild rc && envctl test rc` |
| Merge to main | `envctl rebuild prod && envctl test prod` |

These are enforced by PostToolUse hooks — if the agent does a `git push origin ci`, the hook injects "MANDATORY: rebuild CI now."

## Build verification gates

- Before merging to ci: build must pass on feature branch
- Before cutting RC: Docker build must pass on ci
- Before merging to main: Docker build must pass on RC
- A failing build at any gate BLOCKS the pipeline — fix first

## Deliverable decomposition

Read `best-practices/pipeline-orchestration.md` is not enough — also read `context/decomposition.md`:
- Journey-first decomposition (what can the user do after this is done?)
- App Shell must be the first feature Deliverable
- Component-first trap: building capabilities without building the surface

## Future work

Every team's completion signal includes FUTURE WORK IDENTIFIED. For each:
- Create a Deliverable in Backlog using `jiractl create-md`
- Include: Summary, Business Rules, Gherkin AC, Data Model, API Surface, Components, Dependencies
- Do NOT start working on future items — Backlog only

## Defect routing

| Where found | Action |
|---|---|
| Feature branch | Return to In Development, fix on same branch |
| CI branch | Fix Agent on ci (2 attempts), or back to Ready for Local Test |
| RC branch | Create Issue ticket, fix on RC, merge RC back into ci, re-run regression |
| Production | Create Issue with `production-defect` label, human decides priority |

## Rate limits

- Claude API at 90%+: finish current operation, don't spawn new agents
- Claude API at 98% or hit: stop, report status, wait for reset automatically
- Jira API: `jiractl` retries on 429, pauses at 98% capacity
- Subagent stall: report if no completion signal received in reasonable time

## Session management

- After merge to main: recommend `/compact` for session reset
- PostToolUse hook fires automatically on `git push origin main`
- Each release cycle should ideally run in a fresh session
- Context files mean a new session picks up all rules without prior conversation

## Retrospectives

After every team completes:
1. Log to `workflow-improvements.md`
2. Apply concrete improvements to agent files + starter templates
3. Skip noise — log all, apply only what's repeatable
4. Create Backlog tickets for future work
5. Update Jira components via `jiractl components`

NEVER:
- Bundle multiple stages into one agent spawn
- Skip mandatory Docker rebuilds after branch operations
- Merge or cut RC with a failing build
- Silently drop a ticket on rate limit — keep status, wait, resume
- Move tickets to In Refinement without human approval — that's a human-only gate
- Merge RC to main without explicit human approval
- Start future work items — they go to Backlog only
- Spawn a team without confirming the Jira transition succeeded — if both
  jiractl and MCP are unavailable, STOP and report to the human. Never let
  code be committed to a ticket that is not in the correct Jira status.
- Create Tasks that duplicate pipeline stages (e.g. "Validate in CI/RC/Prod")
  — the pipeline stages handle environment validation automatically
- Let agents run unchecked for more than 5 minutes — check output at 1-minute
  intervals and intervene if stuck
- Let agents read scripts before executing them — execute first, diagnose
  on failure only
- Run any git operation without first verifying the repo with `pwd && git remote get-url origin`
- Generate code without first reading the existing files in the area being modified
- Kill running dev servers without explicit human permission
- Start an API server without running pending DB migrations first
- Guess CSS class names, template structures, or design system patterns — read the source files
