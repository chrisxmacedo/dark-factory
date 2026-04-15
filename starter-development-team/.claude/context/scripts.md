# Token-saving scripts

Read by: Team Lead only

Shell scripts in `infra/` handle mechanical pipeline operations without
using Claude tokens. **Use these instead of MCP calls or spawning agents
for mechanical work.**

## SETUP REQUIRED — customise scripts before first use

These scripts are copied from the starter template with `{PLACEHOLDER}`
values. The Team Lead MUST customise them during Stage 7 (pipeline setup)
or the first Infrastructure Setup deliverable:

### `infra/envctl`
- `SERVICE_REPOS` — list all service repo paths
- `WEB_PORT_CI` — base port for the first service (others offset from this)
- `checkout_branch` — verify branch names match your Git workflow

### `infra/pipelinectl`
- `PROJECT_KEY` — Jira project key (e.g. `SENT`, `HIND`)
- `SERVICE_REPOS` — same list as envctl
- `T_BACKLOG`, `T_IN_DEV`, etc. — Jira transition IDs (get from `getTransitionsForJiraIssue`)
- `{BUILD_COMMAND}` — Docker build verification command

### `infra/jiractl` — CONFIGURE FIRST
- Requires `infra/.env.jira` with `JIRA_EMAIL` and `JIRA_API_TOKEN`
- Create token at: https://id.atlassian.com/manage-profile/security/api-tokens
- **This MUST be configured during project setup (Stage 8).** Without it,
  the pipeline cannot transition tickets, which is a hard gate for all
  team spawns. If both jiractl and MCP are unavailable, the pipeline stops.

### `infra/dashboard.py`
- `PROJECT_SLUG` — Docker Compose project name prefix
- `WEB_PORT_CI` — must match envctl
- `SERVICES` array in HTML — list your services and ports

**Do not skip this.** Uncustomised scripts will fail with placeholder
errors or operate on wrong repos/ports.

| Script | Purpose | Replaces |
|--------|---------|----------|
| `infra/jiractl` | Jira transitions, comments, polling, components | Atlassian MCP calls |
| `infra/pipelinectl` | CI gates, local tests, branch ops, RC cuts | Agent spawns for mechanical stages |
| `infra/envctl` | Docker environment management | Manual docker compose |

**Rule:** For every operation, check if `pipelinectl` or `jiractl` can do it
before using MCP or spawning an agent. Only use Claude tokens for reasoning
tasks (development, code review, analysis, impact assessment).

**Credentials:** Scripts require `infra/.env.jira` with `JIRA_EMAIL` and
`JIRA_API_TOKEN`. If this file does not exist, **fall back to Atlassian MCP**
for Jira operations — do not fail silently. Check for the file before
attempting to use `jiractl`:
```bash
test -f infra/.env.jira && ./infra/jiractl poll || echo "No .env.jira — use MCP"
```

## Branch operations via pipelinectl

| Action | Command |
|--------|---------|
| Merge feature PR into ci | `cd infra && ./pipelinectl merge-to-ci {PROJECT_KEY}-{key}` |
| Cut release-rc-{n} from ci | `cd infra && ./pipelinectl cut-rc {PROJECT_KEY}-{key}` (always from ci HEAD) |
| Merge RC into main + tag + back-merge | `cd infra && ./pipelinectl merge-rc {PROJECT_KEY}-{key} {N}` |

## Jira operations via jiractl

```bash
cd infra
./jiractl poll                              # Find actionable tickets
./jiractl backlog                           # Show next Deliverable in Backlog
./jiractl transition {PROJECT_KEY}-{key} {id}       # Transition ticket
./jiractl comment {PROJECT_KEY}-{key} "message"     # Add comment
./jiractl components {PROJECT_KEY}-{key} svc1 svc2  # Set components
./jiractl status {PROJECT_KEY}-{key}                # Show ticket info
```
