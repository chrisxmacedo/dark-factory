---
description: Create a Jira Deliverable ticket under an Initiative with full context for task breakdown
---

# Create Jira Deliverable: $ARGUMENTS

Create a Deliverable issue under an existing Initiative in the current
project's Jira.

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
directory specifies a Jira project key. If not, ask the user.

---

## Step 2 — Identify the parent Initiative

If `$ARGUMENTS` contains an issue key (e.g. `PROJ-42`), use that as the parent.

Otherwise, search for open Initiatives in the project:

Use `searchJiraIssuesUsingJql` with:
- `jql`: `project = {KEY} AND issuetype = Initiative AND status != Done`

Present the list and ask the user which Initiative this Deliverable belongs to.

---

## Step 3 — Gather deliverable details

If `$ARGUMENTS` contains a title (after the issue key), use it.

Ask the user for anything not provided:

| Field | Description | Required |
|-------|-------------|----------|
| **Title** | What is being delivered | Yes |
| **Business rules** | What a user/consumer can do | Yes |
| **Exceptions** | Edge cases, error states, limitations | Yes |
| **Components** | Which repos are impacted (e.g. treemail-web, treemail-sync) | Yes |
| **Dependencies** | Other Deliverables that must be done first | No |

For each field, read project documentation (idea docs, CLAUDE.md, Confluence,
architecture docs) to pre-fill with real details, then confirm with the user.

---

## Step 4 — Generate the description

Write the issue description using the structured template below. Every section
serves a specific pipeline stage — do not skip sections or merge them.

The description must be **self-contained**: a developer should be able to
implement, test, and integrate this Deliverable without looking elsewhere.

```markdown
## Summary
{One sentence: what this delivers and why it matters.}

## Business Rules
- A user can {action} so that {outcome}
- A user can {action} except when {exception}
- A consumer can {action} and receives {response}
- When {condition}, the system {behaviour}

{List every rule. Use "A user can..." for user-facing behaviour,
"A consumer can..." for API consumers, "When..." for system behaviour.
Always include exceptions and error states.}

## Acceptance Criteria

Scenarios express expected behaviour ONLY. Four scenario types:

1. **Successful cases** — the happy path works as specified
2. **Edge cases** — boundary conditions (empty lists, max lengths, first/last item)
3. **Corner cases** — unusual but valid combinations (concurrent access, timezone boundaries)
4. **Exceptions** — invalid input, missing data, auth failures, downstream errors

Format: Gherkin.
- **Given** = the data start state (what exists in the DB/system before the action)
- **When** = the inflection point (the single action that changes state)
- **Then** = the expected data state (what the DB/system looks like after)

Other Gherkin structures apply: And, But, Background, Scenario Outline, Examples.

```gherkin
Feature: {feature name}

  Scenario: Successful — {description}
    Given {data start state}
    When {inflection point}
    Then {expected data state}

  Scenario: Edge case — {description}
    Given {boundary data state}
    When {action at boundary}
    Then {expected data state}

  Scenario: Corner case — {description}
    Given {unusual but valid data state}
    When {action}
    Then {expected data state}

  Scenario: Exception — {description}
    Given {data start state}
    When {invalid action or missing prerequisite}
    Then {expected error state}
    And {system state unchanged}
```

Rules:
- Write one Scenario per business rule minimum
- Include at least one exception scenario
- Given/Then describe DATA STATE not UI state — "Given user has 3 threads"
  not "Given the inbox page is open"
- When describes ONE action — not a sequence of steps
- These become the Test Writer's source of truth: unit/behaviour tests
  validate the data states, browser tests validate the UI renders them

## Data Model Changes
- New tables/columns: {list with types, or "none"}
- Migrations: {ordering, backfill needs, rollback safety, or "none"}
- Indexes: {new indexes needed, or "none"}

{The Integration Analyst uses this to validate migration safety and data
consistency. If no schema changes, write "No data model changes."}

## API Surface
- `POST /api/{resource}` — {description, request/response shape}
- `GET /api/{resource}/:id` — {description}
- Changed contracts: {what changed and why, or "none"}

{The E2E Impact team uses this to map affected journeys and trace data
through the system. If no API changes, write "No API surface changes."}

## Components
{repo-1}, {repo-2}

## Dependencies
- Requires: {PROJ-N} ({what it provides}) — or "None"

## Supporting Documentation
- Confluence: {link to relevant page, or "n/a"}
- Design: {link to mockup/wireframe, or "n/a"}
- Reference: {link to external docs, API reference, or "n/a"}
```

### Section purpose reference

| Section | Who reads it | Pipeline stage |
|---------|-------------|----------------|
| Summary | Everyone | All |
| Business Rules | Implementer, Devil's Advocate | Development |
| Acceptance Criteria | Test Writer, Local Test team | Development, Local Test |
| Data Model Changes | Integration Analyst | Integration Test |
| API Surface | Integration Analyst, E2E Runner | Integration, E2E Impact |
| Components | Team Lead | All (branch + component tracking) |
| Dependencies | Team Lead | Backlog (ordering) |
| Supporting Documentation | Everyone | All |

---

## Step 5 — Create the issue

Use `createJiraIssue` with:
- `cloudId`: CLOUD_ID
- `projectKey`: the project key from Step 1
- `issueTypeName`: "Deliverable"
- `summary`: the title
- `description`: the generated description
- `contentFormat`: "markdown"
- `parent`: the Initiative issue key from Step 2

---

## Step 6 — Set components

Use `editJiraIssue` to set the `components` field on the newly created issue
based on the repos listed in the Components section of the description.

---

## Step 7 — Output summary

```
Deliverable created

  Key          : {issue key}
  Title        : {title}
  Parent       : {initiative key} — {initiative title}
  Components   : {repo-1, repo-2}
  Dependencies : {PROJ-N or "none"}
  Scenarios    : {count} Gherkin scenarios
  URL          : $JIRA_URL/browse/{issue key}

  Next: Create tasks with /create-jira-task
```
