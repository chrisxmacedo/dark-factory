---
description: Create a GitHub issue and add it to Mission Control
---

# Create Ticket: $ARGUMENTS

Create a GitHub issue in the current repository and automatically add it to the
**Mission Control** project board.

> **CRITICAL — GraphQL quoting rule:**
> ALL `gh api graphql -f query=` strings MUST use **single quotes** `'...'`.
> Never use double quotes or heredocs for the query string. Shell variables are
> passed via `-F` flags only.

---

## Config (never change these)

```
ORG=ClauseHub
PROJECT_NUMBER=1
PROJECT_ID=PVT_kwDOD_6XQs4BRzCV
GH="GH_TOKEN=$COMPANY_BOT_TOKEN gh"
```

Use `$GH` instead of `gh` for every command so actions appear as `ClauseHub-bot`.
If `$COMPANY_BOT_TOKEN` is not set, fall back to plain `gh`.

---

## Step 1 — Gather ticket details

If `$ARGUMENTS` is non-empty, parse it as the ticket **title** and skip asking
for one. For all other fields, use sensible defaults unless the user provided
them in `$ARGUMENTS`.

Ask the user for the following (all optional — use defaults shown):

| Field        | Options                                                  | Default    |
|--------------|----------------------------------------------------------|------------|
| **Title**    | Short imperative sentence                                | (required) |
| **Category** | Feature / Bug / Chore / Design / Documentation / Research | Feature    |
| **Priority** | Critical / High / Medium / Low                           | Medium     |
| **Size**     | XS / S / M / L / XL                                     | M          |
| **Status**   | Backlog / Todo / In Progress / In Review / Done          | Backlog    |
| **Assignee** | GitHub username                                          | (none)     |

**Always generate the issue body** — never leave it blank. Based on the title
and category, write a body using this format:

```
## Overview
{2-3 sentences explaining what this is and why it's needed}

## Acceptance Criteria
- [ ] {specific, testable criterion}
- [ ] {specific, testable criterion}
- [ ] {add more as needed}

## Notes
{Any relevant context, links, constraints, or implementation hints — omit if none}
```

Use knowledge of the codebase (read relevant files first) to write meaningful,
specific criteria.

---

## Step 2 — Detect the current repo

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
REPO_NAME=$(echo "$REPO" | cut -d'/' -f2)
```

If this fails (not in a git repo), ask the user which repo to use:
```bash
gh repo list ClauseHub --json nameWithOwner -q '.[].nameWithOwner'
```

---

## Step 2b — Ensure repo label exists

```bash
gh label list --repo "$REPO" --json name -q '.[].name' | grep -x "$REPO_NAME" || \
  gh label create "$REPO_NAME" --repo "$REPO" --color "0075ca" \
    --description "Issues from the $REPO_NAME repository"
```

---

## Step 3 — Create the GitHub issue

```bash
$GH issue create \
  --repo "$REPO" \
  --title "$TITLE" \
  --body "$BODY" \
  --label "$REPO_NAME"
```

Add `--assignee "$ASSIGNEE"` only if an assignee was specified.
Capture the issue URL. Extract the issue number from the URL.

---

## Step 4 — Add issue to Mission Control

```bash
ITEM_ID=$($GH project item-add "$PROJECT_NUMBER" \
  --owner "$ORG" \
  --url "$ISSUE_URL" \
  --format json | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

---

## Step 5 — Fetch all field IDs and option IDs

```bash
FIELDS=$(gh api graphql -f query='
  query($org: String!, $number: Int!) {
    organization(login: $org) {
      projectV2(number: $number) {
        fields(first: 30) {
          nodes {
            ... on ProjectV2SingleSelectField {
              id
              name
              options { id name }
            }
          }
        }
      }
    }
  }
' -F org="$ORG" -F number="$PROJECT_NUMBER")
```

Parse with Python into a dict: `{field_name: {id, options: {option_name: option_id}}}`.

---

## Step 6 — Set Status, Priority, Size, and Category fields

For each field (using single-quoted query string — required):

```bash
gh api graphql -f query='
  mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
    updateProjectV2ItemFieldValue(input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }) {
      projectV2Item { id }
    }
  }
' -F projectId="$PROJECT_ID" \
  -F itemId="$ITEM_ID" \
  -F fieldId="$FIELD_ID" \
  -F optionId="$OPTION_ID"
```

Repeat for Status, Priority, Size, and Category.

---

## Step 7 — Output a summary

```
Ticket created

  Title     : {title}
  Repo      : {repo}
  Issue     : {issue_url}
  Status    : {status}
  Priority  : {priority}
  Size      : {size}
  Category  : {category}

  Board     : https://github.com/orgs/ClauseHub/projects/1
```
