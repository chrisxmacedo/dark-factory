# Project — {PROJECT_NAME}

## Position in the delivery team

This repo-set is the build pipeline of the delivery team
(`starter-delivery-team/`). DEV Deliverables arrive from the
**Programme Lead** (`../../../PIPELINE.md`) who sources them from
stable journeys in the sibling `capability-team/`. You do not accept
direct ticket creation from humans — if someone tries, ask them to
route through the Programme Lead.

## Jira configuration

- Project key: {PROJECT_KEY}
- Cloud ID: {CLOUD_ID}
- Jira URL: https://{JIRA_SITE}
- MCP: Atlassian MCP with read:jira-work and write:jira-work

## Repository structure

Each service gets its own git repo. The workspace directory is NOT a git repo.
Each service subdirectory (e.g. {service-1}/, {service-2}/) is its own
standalone repo with its own branches, PRs, and CI configuration.

## Work item types

- **Tasks** use a simple 3-status workflow: Open -> In Progress -> Done.
  They do not flow through the full pipeline.
- **Deliverables** flow through the full pipeline
  (Backlog -> In Refinement -> In Development -> ... -> Release / Production -> Done).

Only Deliverables trigger the team spawning and gating process.

## Infrastructure changes

PIPELINE.md / CLAUDE.md changes that affect pipeline operations should be
committed directly to ci and merged to main — not routed through feature
branches. These are operational configuration changes, not feature work.
