---
description: Claim a Jira ticket and advance it through the pipeline stages
---

# Take Task: $ARGUMENTS

Claim a Jira ticket and advance it through the full pipeline. This command
acts as the Team Lead — it does NOT implement code directly. It reads the
ticket's current status and routes to the correct action (spawn a specialist
agent, run a pipelinectl script, etc.).

**Before doing anything:** read `.claude/CLAUDE.md` for context file references.
On first invocation, read all context files. On subsequent invocations,
re-read `context/pipeline-stages.md` and `context/scripts.md`.

**Read the relevant best practices** before spawning any team:
- `context/best-practices/pipeline-orchestration.md` — your rules
- `context/best-practices/pipeline-{branch}.md` — the team's rules

---

## Step 1 — Identify the ticket

If `$ARGUMENTS` is a Jira key (e.g. `TREEM-175`), use it directly.

If `$ARGUMENTS` is `next`, poll Jira for the next actionable ticket:

```bash
test -f infra/.env.jira && cd infra && ./jiractl poll
```

If `jiractl` is not available (no `.env.jira`), fall back to Jira MCP.

**Only process one ticket at a time.** Do not start a second ticket until
the current one reaches Done.

---

## Step 2 — Read the ticket

Use `jiractl status` or Jira MCP to read the ticket's full details:
- Summary, description, acceptance criteria
- **Current Jira status** — this determines which pipeline action to take
- Issue type — Tasks use a simple workflow, only Deliverables use the full pipeline

```bash
cd infra && ./jiractl status {KEY}-{key}
```

---

## Step 3 — Route based on current status

**For Tasks** (simple 3-status workflow):
Move to In Progress, spawn a development agent, move to Done when complete.

**For Deliverables** (full pipeline): check the ticket's current Jira status
and advance through each stage. **NEVER combine multiple stages into one
agent spawn.** Each stage is a separate agent invocation.

| Current status              | Action |
|-----------------------------|--------|
| Backlog (auto-picked)       | Transition to In Refinement (4). SPAWN: refinement-team.md (solution design, task breakdown, risk assessment). |
| In Refinement (complete)    | Transition to In Development (51). SPAWN: development-team.md. |
| In Development (complete)   | Transition to In Local Test. RUN: `pipelinectl local-gate`. If pass → `pipelinectl merge-to-ci`. If fail → spawn Fix Agent. |
| In Local Test (complete)    | Transition to In Integration Test. RUN: `pipelinectl ci-gate`. Then SPAWN: Integration Analyst + Observability Checker. |
| In Integration Test (complete) | Transition to In E2E Impact Test. SPAWN: e2e-impact-team agent. After pass → RUN: `pipelinectl cut-rc`. |
| In E2E Impact Test (complete) | Transition to In Full E2E Regression. RUN: `envctl test rc`. Then SPAWN: Regression Analyst. |
| In Full E2E Regression (human approves) | RUN: `pipelinectl merge-rc` then `envctl test prod`. SPAWN: Production Observer. Transition to Release / Production. |

---

## Step 4 — Advancing through stages

**After each stage completes successfully, immediately advance to the next
stage.** Do not wait for human confirmation between stages — the pipeline
is continuous.

The only point where the pipeline pauses for human input is:

- **In Full E2E Regression → Release / Production** — human says
  "Approve promote {KEY}-{key}"

After a ticket reaches **Done**, automatically pick up the next Backlog
ticket: poll for the highest-priority Deliverable in Backlog, transition
to In Refinement (4), and start the pipeline. The human does not need to
move tickets to In Refinement manually.

At all other transitions, report the result and immediately proceed:

```
Stage: In Development → complete
Result: PASS — 85 tests, lint clean, build clean
Proceeding to: In Local Test
```

Then run the next stage. Do NOT stop and wait.

---

## Step 5 — Claim and execute each stage

**Claim:** transition the ticket and add a Jira comment:

```bash
cd infra && ./jiractl transition {KEY}-{key} {transition_id}
cd infra && ./jiractl comment {KEY}-{key} "Team Lead: [stage] starting."
```

**Execute:**

- **Scripted stages** (local-gate, ci-gate, envctl test): run the script,
  capture output, add result as Jira comment. Only spawn a Claude agent if
  the script fails.

- **Agent stages** (refinement, development, e2e-impact): spawn the
  specialist agent with full ticket context. The Team Lead does NOT write
  code or perform analysis — that's the team's job.

**Mandatory environment rebuilds after branch operations:**
- After merge to ci: `cd infra && ./envctl rebuild ci && ./envctl test ci`
- After cutting RC: `cd infra && ./envctl rebuild rc && ./envctl test rc`
- After merge to main: `cd infra && ./envctl rebuild prod && ./envctl test prod`

These are hook-enforced — if you push to ci/rc/main, the hook injects
"MANDATORY: rebuild now."

---

## Step 6 — Gate verification

After each action completes, verify gate criteria with **evidence** (test
results, build output, analysis findings). Never transition on assumption.

If the stage passed → transition to next stage and continue.
If the stage failed → follow `context/defect-handling.md`:
- Feature branch failure → return to In Development
- CI failure → Fix Agent on ci (2 attempts)
- RC failure → create Issue, fix on RC, merge back to ci, re-run regression
- Production failure → create Issue with `production-defect` label

---

## Step 7 — Completion signals

After each team completes, capture:
- **RETROSPECTIVE** — log to `workflow-improvements.md`
- **FUTURE WORK IDENTIFIED** — create Backlog tickets with full Deliverable template
- **Component updates** — `jiractl components {KEY}-{key} repo1 repo2`

---

## Step 8 — Session reset after release

After merge to main and production observation:
- Report release summary
- Run `/compact` to clear context for next ticket

---

## Rate limit handling

- At 90%+ Claude API usage: finish current stage, don't spawn next agent
- At 98% or hit: stop, report status, wait for reset automatically
- Before any agent spawn: check for rate limit warnings first
