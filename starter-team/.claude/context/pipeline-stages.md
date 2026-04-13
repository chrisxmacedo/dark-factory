# Pipeline stages and orchestration

Read by: Team Lead only

## Pipeline and team mapping

```
[Feature Branch]  — isolated development, local validation
  Backlog
  → In Refinement              ← auto-picked from Backlog after previous ticket Done
                               ← SPAWN: refinement-team.md (solution design, tasks, risks)
  → In Development             ← SPAWN: development-team.md (Claude — writes code)
  → In Local Test              ← SCRIPT: pipelinectl local-gate
                               ← SCRIPT: pipelinectl merge-to-ci (if gates pass)
                               ← SPAWN Diagnostics Team if gates fail

[CI Branch]  — first point where changes interact with the broader system
  → In Integration Test          ← set by pipelinectl after merge
                                 ← SCRIPT: pipelinectl ci-gate (mechanical)
                                 ← SPAWN: Integration Analyst + Observability Checker only (reasoning)
  → In E2E Impact Test           ← SPAWN: e2e-impact-team.md (Claude — journey analysis)
                                 ← SCRIPT: pipelinectl cut-rc (after E2E passes)

[Release Branch]  — stabilisation, no new features
  → In Full E2E Regression       ← set by pipelinectl after RC cut
                                 ← SCRIPT: envctl test rc (mechanical regression)
                                 ← SPAWN: Regression Analyst only (release readiness reasoning)

[Main]  — production-ready, receives only the RC merge
  → Release / Production        ← SCRIPT: pipelinectl merge-rc (after human approval)
                                ← SCRIPT: envctl test prod (smoke tests)
                                ← SPAWN: Production Observer only (15-min watch)
  → Done                        ← final status after release completes
```

## Jira status transition IDs

**These IDs change per project.** They MUST be discovered during project setup
(Stage 7) by querying Jira for available transitions on a Deliverable ticket:

```bash
cd infra && ./jiractl transitions {PROJECT_KEY}-{first_deliverable_key}
```

Or via MCP: `getTransitionsForJiraIssue`. Replace the placeholder IDs below
with the actual values for this project.

| Transition target              | Transition ID | Jira status name           |
|-------------------------------|---------------|----------------------------|
| Backlog                        | {T_BACKLOG}   | Backlog                    |
| In Refinement                  | {T_REFINE}    | In Refinement              |
| In Development                 | {T_DEV}       | In Development             |
| In Local Test                  | {T_LOCAL}     | In Local Test              |
| In Integration Test            | {T_INTEG}     | In Integration Test        |
| In E2E Impact Test             | {T_E2E}       | In E2E Impact Test         |
| In Full E2E Regression         | {T_REGRESS}   | In Full E2E Regression     |
| Release / Production           | {T_RELEASE}   | Release / Production       |
| Done                           | {T_DONE}      | Done                       |

**Task workflow** (simpler — Open → In Progress → Done):

| Transition target              | Transition ID      | Jira status name |
|-------------------------------|--------------------|------------------|
| In Progress                    | {T_TASK_INPROGRESS}| In Progress      |
| Done                           | {T_TASK_DONE}      | Done             |

Discover Task transition IDs by querying a Task ticket (not a Deliverable).

## Polling loop

### Step 1 — Poll

```bash
cd infra && ./jiractl poll
```

**Only process one ticket at a time.** Take the first result from the highest
priority query. Do not start a second ticket until the current one reaches
Done.

To check if a ticket needs Claude or scripts:
```bash
cd infra && ./pipelinectl needs-claude {PROJECT_KEY}-{key}
```

### Step 2 — Claim

```bash
cd infra
./jiractl transition {PROJECT_KEY}-{key} {transition_id}
./jiractl comment {PROJECT_KEY}-{key} "🤖 Team Lead: Claimed. [Team/script] starting."
```

### Step 3 — Run script or spawn agent

| Ticket status at poll          | Action                                                |
|-------------------------------|-------------------------------------------------------|
| In Refinement                  | **SPAWN:** refinement-team.md (Claude — solution design, task breakdown, risk assessment). Transition to In Development (51) when refinement complete. |
| In Development                 | **SPAWN:** development-team.md (Claude — writes code). Transition to In Local Test (9) on completion. |
| In Local Test                  | **SCRIPT:** `pipelinectl local-gate`. If pass → `pipelinectl merge-to-ci`. If fail → SPAWN Diagnostics Team. |
| In Integration Test            | **SCRIPT:** `pipelinectl ci-gate`. Then **SPAWN:** Integration Analyst + Observability Checker only. |
| In E2E Impact Test             | **SPAWN:** e2e-impact-team.md. After pass → **SCRIPT:** `pipelinectl cut-rc` |
| In Full E2E Regression         | **SCRIPT:** `envctl test rc`. Then **SPAWN:** Regression Analyst only. |
| Release / Production           | **SCRIPT:** `pipelinectl merge-rc` then `envctl test prod`. Then **SPAWN:** Production Observer only. Transition to Done (41) after release completes. |

**For scripted stages:** capture output, add as Jira comment via `jiractl comment`. Only spawn Claude if the script fails.

### Re-run after Diagnostics fix

When the Diagnostics Team signals `FIX VERIFIED`, the Team Lead must **re-run
the same stage** that originally failed — do NOT skip ahead:

| Stage that failed | After fix, re-run |
|---|---|
| In Local Test | `pipelinectl local-gate` again. If pass → merge to ci. |
| In Integration Test | `pipelinectl ci-gate` again + re-spawn analyst/checker. |
| In E2E Impact Test | Re-spawn e2e-impact-team. If pass → cut RC. |
| In Full E2E Regression | `envctl test rc` again + re-spawn regression analyst. |
| Release / Production | `envctl rebuild {env} && envctl test {env}` again. |

**Do NOT transition the ticket backward** after a Diagnostics fix at the same
stage. The ticket stays in its current status. Only transition backward if
the Diagnostics Team signals `FIX EXHAUSTED` (see defect-handling.md).

Update PIPELINE-STATE.md after re-running: note the fix attempt and the
re-run result.

### Build verification hard gates

**Before merging a feature to ci:** the production build (`next build` or
equivalent) MUST pass on the feature branch. `pipelinectl local-gate`
includes a build check. If the build fails, do NOT merge — return to
In Development.

**Before cutting an RC from ci:** verify the ci branch builds successfully
by running `envctl rebuild ci`. If the Docker build fails, do NOT cut the
RC — the ci branch is broken and must be fixed first.

**Before merging RC to main:** verify the RC images build and all regression
tests pass. If `envctl rebuild rc` fails, do NOT merge to main.

These are non-negotiable. A failing build at any gate means the pipeline
stops until the build is fixed. Never merge or promote code that doesn't
build.

### Mandatory environment rebuild after every branch change

Docker environments MUST be rebuilt and tested after every branch operation.
This is not optional — it ensures the dashboard and browsable environments
always reflect the current state of each branch.

**After every merge to ci:**
```bash
cd infra && ./envctl rebuild ci && ./envctl test ci
```

**After cutting an RC from ci:**
```bash
cd infra && ./envctl rebuild rc && ./envctl test rc
```

**After merging RC to main:**
```bash
cd infra && ./envctl rebuild prod && ./envctl test prod
```

If using `pipelinectl`, these are already built in. If performing branch
operations manually (git merge), you MUST run the rebuild + test commands
yourself. The environments at http://localhost:3000 (CI), :3100 (RC), and
:3200 (Prod) must always show the latest code on their respective branches.

### Step 4 — Supervise

Monitor inboxes from all active teammates. Relay critical messages between
teams where needed.

### Step 5 — Gate on completion

Verify gate criteria from the agent file. Evidence must be present.

After verifying the gate:

1. **Log retrospective** — append to `workflow-improvements.md`
2. **Act on improvements** — apply concrete suggestions to agent files
3. **Skip noise** — log all, apply only what's repeatable
4. **Create backlog tickets for future work** — each team signals FUTURE WORK
   IDENTIFIED. Create Deliverables with full template detail (Business Rules,
   Gherkin AC, Data Model, API Surface, Components, Dependencies).
5. **Update components** via `jiractl components`
6. **Regenerate repository maps** after every Deliverable reaches Done:
   ```bash
   cd infra && ./repomap all
   ```
   This updates REPO_MAP.md in each service repo so the Refinement Team
   has current structure information for the next ticket.

### Step 5b — Session reset after release

After merging RC to main and completing the release (environments rebuilt,
tests run, Production Observer done):

1. Report the release summary to the human
2. Suggest: "Release complete. Recommend starting a fresh session for the
   next ticket to keep context clean."

This prevents context accumulation across releases. Each release cycle
should ideally run in a fresh session.

### Step 6 — Human gates

Only ONE human gate remains:

- **Promote to Main** — add comment "✅ Regression complete. Awaiting human
  approval." Do NOT merge until human replies "Approve promote {PROJECT_KEY}-[key]".

### Step 7 — Auto-advance next ticket

After a ticket reaches **Done**, automatically pick up the next ticket
from the Backlog:

1. Poll Backlog for the highest-priority Deliverable:
   `project = {PROJECT_KEY} AND issuetype = Deliverable AND status = "Backlog" ORDER BY priority ASC, created ASC`
2. If a ticket is found, transition it to In Refinement ({T_REFINE}) and start the pipeline
3. If no tickets in Backlog, report "No tickets in Backlog. Waiting for work."

This means the pipeline is **fully continuous** — after one ticket completes,
the next one starts immediately. The only pause is the promote-to-main
approval.

### Step 8 — Loop

Return to Step 1.
