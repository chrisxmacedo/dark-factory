# Documentation Index

This folder documents the rationale, design decisions, and operational
detail behind the agent team pipeline system used in this project.

This is a **framework-level** document set. It applies to any project
scaffolded from this starter. Project-specific details (Jira project key,
cloud ID, Jira URL, transition IDs) are configured in `PIPELINE.md` at
the project root.

---

## Documents

| File | Contents |
|------|----------|
| [01-pipeline-rationale.md](01-pipeline-rationale.md) | Why this pipeline exists, the progressive confidence principle, and the reasoning behind each stage |
| [02-agent-team-design.md](02-agent-team-design.md) | How Claude Code agent teams work, why Pattern 2 was chosen, and how teams relate to Jira |
| [03-roles-and-responsibilities.md](03-roles-and-responsibilities.md) | The Software Engineer and Test Developer role split, and what each agent is responsible for |
| [04-testing-strategy.md](04-testing-strategy.md) | Test types, where each belongs in the pipeline, data validation requirements, and observability |
| [05-jira-workflow.md](05-jira-workflow.md) | Jira status design, transition IDs, human gates, and setup instructions |

---

## Quick reference

```
[Feature Branch]
  Backlog → Ready for Dev → In Development → Ready for Local Test → In Local Test

[CI]
  Ready for Integration Test → In Integration Test
  → Ready for E2E Impact Test → In E2E Impact Test

[Release Candidate]
  Ready for Full E2E Regression → In Full E2E Regression

[Main]
  Release / Production
```

Each "In…" status has a dedicated agent team defined in `.claude/agents/`.
The Team Lead in `PIPELINE.md` is the persistent orchestrator that polls
Jira and spawns teams.

---

## Setup checklist for a new project

1. Copy this starter to your project repository
2. Edit `PIPELINE.md` — replace all `{PLACEHOLDER}` values:
   - `{PROJECT_NAME}` — human-readable project name
   - `{PROJECT_KEY}` — Jira project key (e.g. `HIN`, `BTS`)
   - `{CLOUD_ID}` — from `getAccessibleAtlassianResources`
   - `{JIRA_URL}` — e.g. `https://yoursite.atlassian.net`
3. Create the pipeline statuses in Jira (see `05-jira-workflow.md`)
4. Run `getTransitionsForJiraIssue` and fill in all TBC transition IDs
5. Start a Claude Code session with `claude` — the Team Lead wakes up
   and begins polling immediately
