---
description: Guide the user through creating a new Jira project with the correct issue type scheme
---

# Create Jira Project: $ARGUMENTS

Guide the user through creating a new Jira project from the Template scheme,
then capture the project key for use in other skills.

**This cannot be fully automated** — Jira project creation requires admin UI
access. This skill walks the user through it step by step.

---

## Config

```
CLOUD_ID=christianmacedo.atlassian.net
JIRA_URL=https://christianmacedo.atlassian.net
TEMPLATE_PROJECT=TEM
```

---

## Step 1 — Gather project details

If `$ARGUMENTS` is non-empty, parse it as the project name.

Ask the user:

| Field | Description | Required |
|-------|-------------|----------|
| **Name** | Project name (e.g. "ClauseHub Energy API") | Yes |
| **Key** | Short uppercase code (e.g. "ENERGY", "HIND") | Yes |

Confirm both before proceeding.

---

## Step 2 — Guide the user through Jira UI

Tell the user:

> **Create the project in Jira:**
>
> 1. Go to [Jira Project Creation](https://christianmacedo.atlassian.net/jira/projects?showCreateProject=true)
> 2. Select **Scrum** or **Kanban** (your preference)
> 3. Select **Team-managed project**
> 4. Set the name to **{name}** and key to **{key}**
> 5. Click **Create**
>
> Once created, you'll need to add the custom issue types:
>
> 1. Go to **Project Settings** → **Issue Types**
> 2. Add these types (matching the Template project):
>    - **Initiative** (hierarchy level 2)
>    - **Deliverable** (hierarchy level 1)
>    - **Task** (standard work type)
>    - **Bug** (standard work type)
>    - **Subtask** (subtask type)
>
> Let me know when it's done.

**Stop and wait for confirmation.**

---

## Step 3 — Verify the project exists

Use `getVisibleJiraProjects` with `searchString={name}` to confirm the
project is accessible. Read the issue types to verify Initiative, Deliverable,
and Task are present.

If any are missing, tell the user which types need to be added.

---

## Step 4 — Output summary

```
Jira project ready

  Name    : {name}
  Key     : {key}
  URL     : https://christianmacedo.atlassian.net/jira/software/projects/{key}/board

  Issue types:
    Initiative  → Level 2 (strategic)
    Deliverable → Level 1 (scoped work)
    Task        → Level 0 (concrete action)
    Bug         → Level 0 (defect)
    Subtask     → Level -1 (sub-work)

  Next: Create a Confluence space with /create-confluence-space
```
