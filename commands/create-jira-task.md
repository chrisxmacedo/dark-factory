---
description: Create a Jira Task ticket under a Deliverable — one concrete action to advance the work
---

# Create Jira Task: $ARGUMENTS

Create a Task issue under an existing Deliverable in the current project's Jira.
Each Task describes one concrete action — something that can be started, done,
and verified in a single work session.

---

## Config

```
CLOUD_ID=christianmacedo.atlassian.net
```

---

## Step 1 — Determine the Jira project

Check if a `CLAUDE.md` or `.claude/settings.json` in the current working
directory specifies a Jira project key. If not, ask the user.

---

## Step 2 — Identify the parent Deliverable

If `$ARGUMENTS` contains an issue key (e.g. `PROJ-42`), use that as the parent.

Otherwise, search for open Deliverables in the project:

Use `searchJiraIssuesUsingJql` with:
- `jql`: `project = {KEY} AND issuetype = Deliverable AND status != Done`

Present the list and ask the user which Deliverable this Task belongs to.

---

## Step 3 — Read the Deliverable for context

Use `getJiraIssue` to read the parent Deliverable's full description. This
contains the platform/system context needed to write a good Task.

---

## Step 4 — Gather task details

If `$ARGUMENTS` contains a title (after the issue key), use it.

Ask the user for anything not provided:

| Field | Description | Required |
|-------|-------------|----------|
| **Title** | Imperative sentence — what to do | Yes |
| **Description** | Concrete steps and definition of done | Generated |

---

## Step 5 — Generate the description

Write the issue description in markdown. Be specific and actionable — someone
picking up this task should know exactly what to do:

```markdown
## What
{1-2 sentences: what exactly needs to happen}

## Steps
1. {First concrete step}
2. {Second concrete step}
3. {Continue as needed}

## Done when
- [ ] {Verifiable outcome 1}
- [ ] {Verifiable outcome 2}

## Context
{Link to parent Deliverable: PROJ-XX. Reference any relevant files,
docs, or configuration. Omit if the Steps section is self-contained.}
```

Use the Deliverable's description to inform the steps. Reference specific
files, endpoints, configs, or commands where possible.

---

## Step 6 — Create the issue

Use `createJiraIssue` with:
- `cloudId`: CLOUD_ID
- `projectKey`: the project key from Step 1
- `issueTypeName`: "Task"
- `summary`: the title
- `description`: the generated description
- `contentFormat`: "markdown"
- `parent`: the Deliverable issue key from Step 2

---

## Step 7 — Output summary

```
Task created

  Key        : {issue key}
  Title      : {title}
  Parent     : {deliverable key} — {deliverable title}
  URL        : https://christianmacedo.atlassian.net/browse/{issue key}
```
