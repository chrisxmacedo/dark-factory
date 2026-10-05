---
description: Migrate an idea from the local Ideas folder into a Confluence space as structured pages
---

# Migrate Idea: $ARGUMENTS

Read all content from a local idea folder in `$IDEAS_DIR/`
and create corresponding pages in a Confluence space.

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

## Step 1 — Identify the idea

If `$ARGUMENTS` is non-empty, use it to match an idea folder name.

Otherwise, list available ideas:

```bash
ls $IDEAS_DIR/
```

Present the list and ask which idea to migrate.

---

## Step 2 — Identify the target Confluence space

Ask the user which Confluence space to migrate into. Use `getConfluenceSpaces`
to list available spaces and let them pick, or accept a space key directly.

Capture the `spaceId`.

---

## Step 3 — Read all idea content

Read every HTML file in the idea folder. For each file, extract:
- The page title (from `<title>` or the first `<h1>`)
- The main content (text, sections, tables, lists)

Convert HTML content to clean markdown suitable for Confluence. Preserve:
- Section headings and hierarchy
- Tables (convert to markdown tables)
- Lists (bulleted and numbered)
- Code blocks
- Key metrics and data points

Skip CSS files, SVG icons, and purely presentational elements.

---

## Step 4 — Create a parent page

Use `createConfluencePage` to create a top-level page:
- `cloudId`: CLOUD_ID
- `spaceId`: the space ID from Step 2
- `title`: "{Idea Name} — Product Overview"
- `contentFormat`: "markdown"
- `body`: A summary page linking to all child pages, including:
  - Product name and one-line description
  - Table of contents (Problem, Vision, Strategy, Metrics, Initiatives)
  - Key dates and status

Capture the page ID — this becomes the parent for all other pages.

---

## Step 5 — Create child pages

For each HTML file in the idea folder, create a Confluence page:
- `cloudId`: CLOUD_ID
- `spaceId`: the space ID
- `parentId`: the parent page ID from Step 4
- `title`: appropriate title (e.g. "Problem Statement", "Product Vision")
- `contentFormat`: "markdown"
- `body`: the converted markdown content

Create pages in this order:
1. Problem
2. Vision (including architecture, data model, deployment)
3. Strategy
4. Metrics
5. Initiatives

---

## Step 6 — Output summary

```
Idea migrated to Confluence

  Idea     : {idea name}
  Space    : {space key}
  Pages    : {count} pages created
  Root     : $CONFLUENCE_URL/spaces/{key}/pages/{parentId}

  Pages created:
    - {title 1} ({url})
    - {title 2} ({url})
    ...
```
