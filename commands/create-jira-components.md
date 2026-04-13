---
description: Guide the user through creating Jira components that match the project's architectural services
---

# Create Jira Components: $ARGUMENTS

Review the project's architecture and guide the user through creating
Jira components for each service, platform, or system in the architecture.

**This cannot be fully automated** — Jira component creation requires project
admin access via the UI. This skill identifies what components are needed and
walks the user through creating them.

---

## Config

```
CLOUD_ID=christianmacedo.atlassian.net
JIRA_URL=https://christianmacedo.atlassian.net
```

---

## Step 1 — Determine the Jira project

Check if a `CLAUDE.md` or `.claude/settings.json` in the current working
directory specifies a Jira project key. If not, ask the user.

---

## Step 2 — Review the architecture

Read the project's architecture documentation. Check these sources in order:

1. `../CLAUDE.md` (parent-level architecture docs)
2. `CLAUDE.md` in the current repo
3. Idea docs in the project folder (e.g. `idea-{name}/`)
4. Any `api-architecture.html` or similar docs

Extract every distinct service, platform, or system mentioned. Examples:
- **Hosting**: Fly.io, DigitalOcean, Vercel
- **Database**: Supabase, PostgreSQL, Redis/Upstash
- **DNS/CDN**: Cloudflare
- **Observability**: Axiom, Sentry, Checkly
- **Auth**: Supabase Auth
- **CI/CD**: GitHub Actions
- **External APIs**: Any third-party integrations

---

## Step 3 — Present proposed components

Show the user the list of components to create:

```
Proposed Jira components for {PROJECT_KEY}:

  Infrastructure:
    - Fly.io (hosting & deployment)
    - Cloudflare (DNS & CDN)
    - GitHub Actions (CI/CD)

  Data:
    - Supabase (database & auth)
    - Upstash Redis (caching)

  Observability:
    - Axiom (logs & traces)
    - Sentry (error tracking)
    - Checkly (uptime monitoring)

  External:
    - {any third-party APIs}

Add, remove, or rename any before I guide you through creation?
```

Wait for approval. Incorporate changes.

---

## Step 4 — Guide the user through Jira UI

Tell the user:

> **Create components in Jira:**
>
> 1. Go to [Project Settings → Components](https://christianmacedo.atlassian.net/jira/software/projects/{KEY}/settings/components)
> 2. For each component below, click **Create component** and enter the name:

Then list each component with its name and a one-line description:

> | Component | Description |
> |-----------|-------------|
> | Fly.io | Container hosting and deployment |
> | Cloudflare | DNS management and CDN |
> | ... | ... |
>
> Let me know when all components are created.

**Stop and wait for confirmation.**

---

## Step 5 — Output summary

```
Jira components created for {PROJECT_KEY}

  Total: {count} components

  {list each component}

  These can now be assigned to Deliverables and Tasks.
```
