---
description: Guide the user through creating a Confluence space for a project, then capture the space ID
---

# Create Confluence Space: $ARGUMENTS

Guide the user through creating a Confluence space, then capture the space ID
for use in other skills (e.g. `/migrate-idea`).

**This cannot be fully automated** — Confluence space creation requires admin UI
access. This skill walks the user through it.

---

## Config

```
CLOUD_ID=christianmacedo.atlassian.net
CONFLUENCE_URL=https://christianmacedo.atlassian.net/wiki
```

---

## Step 1 — Gather space details

If `$ARGUMENTS` is non-empty, parse it as the space name.

Ask the user:

| Field | Description | Required |
|-------|-------------|----------|
| **Name** | Space name (e.g. "ClauseHub Energy API") | Yes |
| **Key** | Short uppercase code, should match Jira project key | Yes |

---

## Step 2 — Guide the user through Confluence UI

Tell the user:

> **Create the space in Confluence:**
>
> 1. Go to [Create Space](https://christianmacedo.atlassian.net/wiki/create-space)
> 2. Choose **Blank space**
> 3. Set the name to **{name}**
> 4. Set the key to **{key}**
> 5. Click **Create**
>
> Let me know when it's done.

**Stop and wait for confirmation.**

---

## Step 3 — Verify the space exists

Use `getConfluenceSpaces` with `keys=["{key}"]` to confirm the space is
accessible. Capture the `id` field — this is the `spaceId` needed for
creating pages.

If the space isn't found, ask the user to double-check the key.

---

## Step 4 — Output summary

```
Confluence space ready

  Name     : {name}
  Key      : {key}
  Space ID : {spaceId}
  URL      : https://christianmacedo.atlassian.net/wiki/spaces/{key}

  Next: Migrate idea content with /migrate-idea
```
