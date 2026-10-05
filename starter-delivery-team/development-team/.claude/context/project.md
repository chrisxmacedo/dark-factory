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

- **Issue** (hierarchy level 1) is the defect type — there is no separate
  Bug type. Defects found in the pipeline are raised as Issues.

## Working preferences

Set by `/create-project` from `~/.config/pipeline-toolkit/config.env`
(answers given to the toolkit's `install.sh`). The Team Lead follows these
wherever `pipeline-stages.md` says "per Working preferences".

- **Promote to production:** {PROMOTE_POLICY}
- **After a ticket reaches Done:** {NEXT_TICKET_POLICY}
- **GitHub issues:** {GITHUB_ISSUES_POLICY}

## Infrastructure changes

PIPELINE.md / CLAUDE.md changes that affect pipeline operations should be
committed directly to ci and merged to main — not routed through feature
branches. These are operational configuration changes, not feature work.

## Reference libraries

At the `templates/` root, two sibling folders are consumed indirectly —
via the capability team's specifications, not by dev-team agents
directly. Read them only when verifying a regulation citation or
tracing a spec defect:

- `../../../starter-regulations/` — sector-indexed regulations that
  shape the security-model, governance, and NFR specs the dev team
  builds against
- `../../../starter-standards/` — non-regulatory standards (WCAG,
  ISO 27001, SOC 2, ISO 9001) that shape the test and audit scope

Details of when to read these are in `best-practices/security.md`,
`best-practices/observability.md`, `best-practices/database.md`,
`best-practices/api-design.md`, and `best-practices/testing.md`.
