---
description: Create a Jira Initiative ticket with description and acceptance criteria
---

# Create Jira Initiative: $ARGUMENTS

Create an Initiative issue in the current project's Jira.

---

## Config

Machine- and client-specific settings live in `~/.config/pipeline-toolkit/config.env`,
written by `install.sh` in the pipeline-toolkit repo. Each shell command runs in
a fresh shell, so start every bash block that uses these values with:

```bash
source ~/.config/pipeline-toolkit/config.env
```

If that file doesn't exist, stop and ask the user to run `install.sh` from the
pipeline-toolkit repo. Values: `$ATLASSIAN_SITE` (Atlassian cloud ID / site),
`$JIRA_URL`, `$CONFLUENCE_URL`, `$PROJECTS_DIR`, `$IDEAS_DIR`, `$TOOLKIT_DIR`,
plus working preferences `$PROMOTE_POLICY`, `$NEXT_TICKET_POLICY`, `$GITHUB_ISSUES`.

---

## Step 1 — Determine the Jira project

Check if a `CLAUDE.md` or `.claude/settings.json` in the current working
directory specifies a Jira project key. If not, list available projects:

Use `getVisibleJiraProjects` with `cloudId=CLOUD_ID` and ask the user which
project to use. Remember the key (e.g. `ENERGY`, `TEM`).

---

## Step 2 — Gather initiative details

If `$ARGUMENTS` is non-empty, parse it as the initiative **title**.

Ask the user for anything not provided:

| Field | Description | Required |
|-------|-------------|----------|
| **Title** | Short name for the initiative | Yes |
| **Description** | What this initiative achieves and why | Yes |
| **Acceptance Criteria** | How we know this initiative is complete | Yes |

---

## Step 3 — Generate the description

Write the issue description in markdown using this format:

```markdown
## Overview
{2-3 sentences explaining the initiative's purpose and business value}

## Scope
{What's included and what's explicitly excluded}

## Acceptance Criteria
- [ ] {specific, measurable criterion}
- [ ] {specific, measurable criterion}
- [ ] {add more as needed}

## Dependencies
{Any known dependencies on other initiatives or external factors — omit if none}
```

Use knowledge of the project (read idea docs, CLAUDE.md, architecture docs)
to write meaningful, specific content.

---

## Step 4 — Create the issue

Use `createJiraIssue` with:
- `cloudId`: CLOUD_ID
- `projectKey`: the project key from Step 1
- `issueTypeName`: "Initiative"
- `summary`: the title
- `description`: the generated description
- `contentFormat`: "markdown"

---

## Step 5 — Output summary

```
Initiative created

  Key       : {issue key, e.g. PROJ-42}
  Title     : {title}
  Project   : {project key}
  URL       : $JIRA_URL/browse/{issue key}

  Next: Create deliverables with /create-jira-deliverable
```
