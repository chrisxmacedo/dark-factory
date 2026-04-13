---
description: Move a ticket to a different status column on Mission Control
---

# Move Ticket: $ARGUMENTS

Move a ticket between status columns on the Mission Control board.

Usage:
- `/move-ticket 7 in-progress`
- `/move-ticket 7 done`
- `/move-ticket 7 backlog`

> **CRITICAL — GraphQL quoting rule:**
> ALL `gh api graphql -f query=` strings MUST use **single quotes** `'...'`.
> Shell variables passed via `-F` flags only.

---

## Config

```
ORG=ClauseHub
PROJECT_NUMBER=1
PROJECT_ID=PVT_kwDOD_6XQs4BRzCV
GH="GH_TOKEN=$COMPANY_BOT_TOKEN gh"
```

---

## Step 1 — Parse arguments

Parse `$ARGUMENTS` for:
- Issue number (required)
- Target status (required)

Normalise status aliases:
| Input | Status |
|---|---|
| `backlog` | Backlog |
| `todo` | Todo |
| `in-progress`, `wip`, `start` | In Progress |
| `in-review`, `review` | In Review |
| `done`, `complete`, `close` | Done |

If either is missing, ask the user.

---

## Step 2 — Find the item on the board

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
ISSUE_URL=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json url -q .url)
```

Fetch all board items and find the one matching this issue URL. Extract its
`ITEM_ID`.

---

## Step 3 — Fetch Status field ID and option ID

Fetch project fields (as in `/create-ticket` Step 5). Find the Status field ID
and the option ID for the target status.

---

## Step 4 — Update the status

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
  -F fieldId="$STATUS_FIELD_ID" \
  -F optionId="$TARGET_OPTION_ID"
```

---

## Step 5 — Confirm

```
Ticket moved

  #7 {title}
  {previous status} → {new status}

  Board: https://github.com/orgs/ClauseHub/projects/1
```
