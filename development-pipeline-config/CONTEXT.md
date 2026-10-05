# development-pipeline-config/

Step-by-step guide for setting up the Jira + Claude Code development pipeline on a new project. Follow the pages in order.

## Location

`templates/development-pipeline-config/` in the pipeline-toolkit repo. This supersedes the old standalone `~/Projects/Pipeline Config/` folder, which is an older copy of these pages.

## Contents

- **index.html** -- Overview, pipeline at a glance, starter template file tree
- **prerequisites.html** -- Required tools, accounts, and local setup
- **jira-setup.html** -- Creating the Jira project, 13 pipeline statuses, transition IDs
- **claude-setup.html** -- Installing starter templates, configuring the Team Lead
- **pipeline.html** -- Full Team Lead orchestration logic, polling loop, gating
- **agent-teams.html** -- All 6 specialist team specifications
- **branching.html** -- Four-branch git model (main, ci, feature/*, release-rc-*)
- **rationale.html** -- Design decisions, roles, testing strategy, and why each stage exists
- **lessons.html** -- 25 improvements discovered during real-world usage
- **development-pipeline-configuration-guide.md** -- Master reference (superset of the HTML pages in Markdown). Where it differs from the HTML it is newer: 12 statuses ("Selected for Development" removed), Diagnostics Team added
- **workflow-improvements.md** -- Chronological log of failures, process changes, and lessons
- **style.css** -- Shared stylesheet for all HTML pages

## Relocated

Essays and styleguides have been moved to `writing/`:
- LinkedIn articles → `writing/articles/The Intelligent Pipeline/`
- Styleguides → `writing/styleguides/`

## For agents

- This is reference documentation, not code. The templates to copy live in `templates/starter-delivery-team/development-team/` (build pipeline). The design pipeline is its sibling, `starter-delivery-team/capability-team/`, documented in `templates/capability-pipeline-config/`.
- `development-pipeline-configuration-guide.md` is the single-file version of the full guide, useful when you need to search or quote specific sections.
