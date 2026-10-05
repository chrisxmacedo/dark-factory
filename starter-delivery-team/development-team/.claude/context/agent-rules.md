# Agent spawning rules

Read by: Team Lead only

**Jira transition is a HARD GATE.** Before spawning any team, the Team Lead
MUST confirm the Jira ticket has been transitioned to the correct status.
If jiractl fails AND MCP is unavailable, do NOT proceed — report to the
human and wait. Never assume a transition happened. Never let code be
committed to a ticket that is not in "In Development" status.

**NEVER combine multiple pipeline stages into a single agent spawn.**
Each pipeline stage MUST be a separate agent invocation:

1. Development Team → separate agent (writes code)
2. Local Test Team → separate agent or pipelinectl (validates independently)
3. Integration Test Team → separate agent (CI + reasoning roles)
4. E2E Impact Team → separate agent (journey analysis)
5. Regression Team → separate agent (full regression + release readiness)

The Team Lead orchestrates between them, checking completion signals
and gate criteria before spawning the next team. **Bundling stages into
"Dev + full pipeline" prompts is explicitly forbidden** — it defeats
independent validation.

Exception: `pipelinectl` scripts can handle mechanical gates (local-gate,
ci-gate) without spawning a Claude agent. Only reasoning tasks need
separate agent spawns.

## Responding to the human mid-session

Always respond immediately. Report:
- Which tickets are in which stage
- Which branch each team is working on
- Which teams are active and what they are doing
- Any blockers or notable inbox messages

Accept mid-session instructions:
- "Skip {PROJECT_KEY}-xxx" → transition back one status, move to next ticket
- "Pause" → finish current team task, then wait before spawning next
- "Prioritise {PROJECT_KEY}-xxx" → finish current ticket first, then jump to it
- "Approve promote {PROJECT_KEY}-xxx" → `pipelinectl merge-rc {PROJECT_KEY}-xxx {N}`,
  then `envctl test prod`, then spawn Production Observer only

## Error handling

If any team or script cannot resolve a blocker:
- `jiractl transition {PROJECT_KEY}-{key} {previous_ready_status_id}`
- `jiractl comment {PROJECT_KEY}-{key} "❌ [stage] failed. [what failed]. Needs human review."`
- Shut the affected team down
- Report to the human immediately
- Continue polling other tickets

Never leave a ticket stranded in an "In…" status with no active team.

## Rate limit handling

**Claude API rate limits:** Monitor for rate limit warnings in the session.
When you see a rate limit notification or percentage warning:

- At **90%+ usage**: report to the human: "⚠️ Approaching Claude API rate
  limit (90%+). Completing current operation then pausing."
  Finish the current operation but do NOT spawn a new agent.

- At **98%+ usage or limit hit**: report the current state, then **wait
  autonomously for the limit to reset**:
  "⚠️ Claude API rate limit reached. Pausing pipeline work.
  {PROJECT_KEY}-{key} is in [current status]. Will resume automatically when
  the rate limit resets."
  Then wait — do NOT ask the human to tell you when to resume. When the
  limit resets and you can operate again, resume from where you left off.
  Re-read the ticket status and continue the pipeline.

- **Before spawning any agent**, check if a rate limit warning has appeared
  in the current session. If so, do NOT spawn — wait for the reset, then
  spawn.

Do NOT silently drop the ticket — keep it in its current "In…" status
and resume automatically when capacity is available.

**Jira API rate limits:** `jiractl` automatically retries on HTTP 429 with
exponential backoff (up to 3 retries). If all retries fail, fall back to
Atlassian MCP for the operation and report:
"⚠️ Jira API rate limited. Falling back to MCP for {PROJECT_KEY}-{key}."

**Subagent failures:** If a spawned agent fails silently (returns no
completion signal within a reasonable time), report to the human:
"⚠️ Agent [team name] for {PROJECT_KEY}-{key} appears stalled. No completion
signal received. May need manual intervention or session restart."

## Ticket creation — use jiractl only

**All ticket creation MUST go through `jiractl create` or `jiractl create-md`.**
Do NOT use Atlassian MCP, raw API calls, or any other method to create tickets.

`jiractl` enforces:
- Deliverables require components (repo names) — creation fails without them
- Consistent formatting and field population
- Components are matched case-insensitively to Jira component names

```bash
# Deliverable (components required)
cd infra && ./jiractl create Deliverable "Add search" "description" "prediction-service,web-service"

# Task (components optional)
cd infra && ./jiractl create Task "Add route" "description" "prediction-service" {PROJECT_KEY}-42

# With markdown description from file
cd infra && ./jiractl create-md Deliverable "Add search" desc.md "prediction-service,web-service"
```

If `jiractl` is unavailable (e.g. `.env.jira` missing), report to the human
rather than falling back to MCP for ticket creation.

## Repository awareness

**Before ANY git operation** (commit, push, checkout, branch, merge), every
agent MUST verify it is in the correct repo:

```bash
pwd && git remote get-url origin
```

- If the repo does not match the current ticket's project, STOP and report
  to the human before proceeding
- Check existing branches (`git branch -a | head -20`) before creating a
  new one — follow the project's naming conventions
- Never push to a repo without first confirming it matches the ticket

This applies to the Team Lead AND all spawned agents. Include the repo
verification instruction in every agent spawn prompt.

## Context-first rule

**Always read existing files before generating code or making changes.**

Before writing any code:
1. Read the service's CLAUDE.md for conventions
2. Read existing files in the area being modified
3. If the ticket references a design system, component library, or template,
   read the actual source files — do not guess class names or structures
4. Read PRD.md and PLAN.md if they exist

Never generate code based on assumptions about file structure, CSS classes,
API shapes, or template patterns. Read first, then write.

## Dev server safety

- **Never kill running dev servers** without explicit human permission
- Before running commands that bind to ports, check if something is already
  running: `lsof -i :{port} 2>/dev/null`
- Always run DB migrations before starting API servers after schema changes:
  - Python: `uv run alembic upgrade head`
  - TypeScript: `npx prisma migrate deploy`
- **Never check out a different branch in a repo whose dev server is
  running** — the server keeps serving, its build cache (e.g. `.next`) is
  corrupted, and the human's environment breaks. Check with `lsof` first; if a
  server is running, ask before switching.
- If a `.next` cache exists and the branch has changed, the cache may be
  stale — but NEVER delete it without human permission.

## Working rules (learned in practice)

- **One ticket at a time.** Never batch several tickets into one branch or
  PR — each gets its own branch, commits and PR, so each can be reviewed,
  tested and reverted on its own.
- **Re-query Jira before deciding there is no work.** Tickets get moved by
  humans between polls; a board that was empty earlier may not be now.
- **Absolute paths in every bash command.** Each command may run in a fresh
  shell — start with `cd /absolute/path && …` rather than relying on the
  previous working directory.
- **Never dismiss a failure as "pre-existing".** A failing build, test or
  page render at any stage blocks that stage, whoever introduced it. Fix it
  or raise an Issue and stop — don't advance past it.

## Execute first, diagnose on failure

**Agents must execute commands immediately — do not read scripts or analyse
code before running them.** The scripts (`envctl`, `pipelinectl`, `jiractl`)
are deterministic and tested. Run the command first. If it fails, then read
the script to diagnose. Never spend tokens understanding how a script works
before trying it.

Bad: read envctl → read docker-compose → analyse ports → read test files → run
Good: run `./envctl test prod smoke` → if it fails, read the error → fix

## Agent timeout monitoring

**After spawning any background agent, check its progress within 1 minute.**

- Read the agent's output file to verify it is making progress
- If making progress (new output, active Docker pulls, test execution):
  let it continue, check again in 1 minute
- If stuck (no new output, git command hanging, Docker build stalled):
  intervene immediately — kill stuck processes, send the agent a message,
  or take over the task directly
- **Never let an agent run for more than 5 minutes without at least one
  status check.** Long-running agents waste tokens and block the pipeline.
- Report stuck agents to the human proactively — do not wait to be asked.
