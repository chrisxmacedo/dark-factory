---
description: Update priority, size, or category on a ticket
---

# Update Ticket: $ARGUMENTS

Update metadata fields on a Mission Control ticket.

Usage:
- `/update-ticket 7 priority high`
- `/update-ticket 7 size l`
- `/update-ticket 7 category bug`
- `/update-ticket 7 priority critical size xl`

> **CRITICAL — GraphQL quoting rule:**
> ALL `gh api graphql -f query=` strings MUST use **single quotes** `'...'`.
> Shell variables passed via `-F` flags only.

---

## Config

Mission Control settings live in `~/.config/pipeline-toolkit/config.env`,
written by `install.sh` in the pipeline-toolkit repo. Each shell command runs
in a fresh shell, so start every bash block with:

```bash
source ~/.config/pipeline-toolkit/config.env
ORG="$MC_ORG"; PROJECT_NUMBER="$MC_PROJECT_NUMBER"; PROJECT_ID="$MC_PROJECT_ID"
GH="gh"; [ -n "$MC_TOKEN_VAR" ] && [ -n "${!MC_TOKEN_VAR:-}" ] && GH="GH_TOKEN=${!MC_TOKEN_VAR} gh"
```

If `MC_ORG` is empty, Mission Control isn't set up on this machine — tell the
user to re-run `install.sh` and stop.

---

## Step 1 — Parse arguments

Parse `$ARGUMENTS` for:
- Issue number (required)
- One or more field/value pairs

Supported fields and normalised values:

**Priority:** `critical`, `high`, `medium`, `low`
**Size:** `xs`, `s`, `m`, `l`, `xl`
**Category:** `feature`, `bug`, `chore`, `design`, `documentation`, `research`

If the issue number is missing, ask. If no fields are provided, ask what to update.

---

## Step 2 — Find the item on the board

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
ISSUE_URL=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json url -q .url)
```

Fetch board items and find the `ITEM_ID` for this issue.

---

## Step 3 — Fetch field IDs and option IDs

Fetch project fields (as in `/create-ticket` Step 5). Build a lookup of field
IDs and option IDs for all fields being updated.

---

## Step 4 — Apply each update

For each field being updated, run the GraphQL mutation (single-quoted):

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

---

## Step 5 — Confirm

```
Ticket updated

  #7 {title}
  Priority  : {old} → {new}   (if changed)
  Size      : {old} → {new}   (if changed)
  Category  : {old} → {new}   (if changed)

  Board: https://github.com/orgs/$MC_ORG/projects/$MC_PROJECT_NUMBER
```
