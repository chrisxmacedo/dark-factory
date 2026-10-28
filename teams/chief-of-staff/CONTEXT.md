# Technical chief of staff

Operating rhythm for a technology organisation. The coordinator's rulebook is `CLAUDE.md` (authority, responsibility, ability). Specialists are `.claude/agents/`. Counting and calendar logic are `scripts/`. Deadlines are `schedules/jobs.json`.

This template does not contain product code and does not include the delivery team. At work, install it with `harness/export-chief-of-staff.sh` so the checkout is only this team plus the shared harness.

## What the agent must not decide

Architecture, people matters, new positions, engineering reprioritisation, and spend the budget script marks `needs_human`. Those are drafts under `drafts/`.

## Placeholders

There are no `{PLACEHOLDER}` tokens. Non-secret settings go in `config/ara.env` (copied from the example). Tokens stay in the environment: `GITHUB_TOKEN`, `JIRA_API_TOKEN`, `LINEAR_API_KEY`.
