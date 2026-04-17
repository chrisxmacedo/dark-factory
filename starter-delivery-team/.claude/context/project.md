# Project identity — {PROJECT_NAME}

Read by: Programme Lead (top-level). Sub-teams have their own `project.md`
files with pipeline-specific config.

## Identity

- **Project name:** {PROJECT_NAME}
- **Organisation:** {ORG_NAME}
- **Delivery-team folder:** `starter-delivery-team/` (this folder, once
  renamed to the project's own folder)

## Jira projects

| Project  | Key           | Used by          | Workflow                                                         |
|----------|---------------|------------------|------------------------------------------------------------------|
| Foundation | {FOUND_KEY} | Capability Lead  | Draft → In review → Approved → Baselined                          |
| Analytical Modelling | {MODEL_KEY} | Capability Lead | Backlog → In progress → In review → Stable → Revised         |
| Development | {DEV_KEY}   | Programme Lead → Team Lead | Backlog → In Refinement → In Development → Local/Integ/E2E/Regression → Release → Done |

Cross-project links (enforced by the Programme Lead):

- FOUND artefact "enables" MODEL journey epic (created by Capability Lead).
- MODEL journey "Stable" → Programme Lead creates DEV Deliverable
  linked with "implements".
- DEV Deliverable "Done" → Programme Lead comments on the MODEL journey
  epic with the release version.

## Team paths (relative to this file's workspace root)

| Team            | Path                  |
|-----------------|-----------------------|
| Capability team | `capability-team/`    |
| Development team | `development-team/`  |

## Tooling

- **Atlassian MCP** — `read:jira-work`, `write:jira-work`. Used by the
  Programme Lead for Jira operations when the dev-team's `jiractl` is
  unavailable.
- **Development team's `jiractl`** — under `development-team/infra/`.
  Programme Lead may use it for DEV-project operations; it is the
  Team Lead's primary tool.

## Placeholders

Before the first Programme Lead run, replace all `{PLACEHOLDER}`
values in this file, in the sub-team `project.md` files, and in the
three PIPELINE.md files. Check with:

```bash
grep -rn "{[A-Z_]\+}" starter-delivery-team/ | grep -v node_modules
```
