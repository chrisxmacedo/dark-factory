---
description: Generate a full product idea breakdown — Problem, Vision, Strategy, Metrics, and Initiatives pages from a user's problem observations and vision
---

# Idea: $ARGUMENTS

Generate a complete product idea breakdown as a set of HTML pages following the VR Pipeline Dashboard format. These pages become the source of truth for the idea's definition, strategy, and execution plan.

The output is a folder of HTML pages inside `$IDEAS_DIR/` using the shared design system from `$TOOLKIT_DIR/idea-template/design-system/styles.css`.

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

## CRITICAL — Step-by-step collaborative process

**Do NOT batch all questions at once or generate all pages in one go.**

Work through it one section at a time:

1. Ask the **Problem** questions → wait for answers → confirm understanding
2. Ask the **Vision** questions → wait for answers → confirm understanding
3. Ask the **Data Model** questions → wait for answers → propose complete model → confirm
4. Present a **full summary of Problems + Vision + Data Model** → wait for user approval
5. Generate all pages → show summary → wait for approval
6. Commit and push to the Ideas repo

At each step, pause and wait. If the user corrects anything, incorporate it before moving on. Never assume — always confirm.

---

## Step 1 — Gather problems (ask these first, wait for answers)

Ask the user:

1. **What problems have you observed?** List as many as you've spotted — these can be pain points, inefficiencies, missing tools, or frustrations. Each will become a numbered problem on the Problem page.
2. **Who experiences these problems?** (developers, managers, end users, a specific industry, etc.)
3. **How are people currently dealing with these problems?** (workarounds, existing tools, manual processes)
4. **What's the worst consequence of these problems going unsolved?**

Listen carefully. Rephrase each problem back as a crisp 1-2 sentence statement and confirm with the user before moving on.

---

## Step 2 — Gather vision (ask after Problems, wait for answers)

Ask the user:

1. **What is your idea?** Describe what you imagine the solution looks like.
2. **What makes this different from what exists today?** What's the unique angle?
3. **Who is the primary user?** Be specific about the target persona.
4. **What does success look like?** If this works perfectly, what changes in the world?
5. **What name would you give this product?** (can be a working title)

---

## Step 3 — Gather data model (ask after Vision, wait for answers)

Ask the user:

1. **What are the core entities/resources?** (e.g. users, events, articles, orders — the nouns in the system)
2. **What are the key relationships between them?** (e.g. an event has many articles, a user can save events)
3. **Are there any specific fields you already know about?** (e.g. "articles need a source URL and publication date")

Listen to whatever the user provides — they may give a rough sketch or just a few entity names. Then:

**Fill in the gaps yourself.** Based on the problems, vision, and architecture already discussed, propose a complete data model. For each entity include:
- Entity name
- Key fields with types (id, created_at always included)
- Relationships to other entities
- Any indexes or constraints that are obvious (e.g. unique on URL, full-text search on title)

Present the full proposed model as a table per entity:

```
Entity: {name}
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| created_at | timestamp | auto |
| ... | ... | ... |
Relationships: {entity} has many {other}, belongs to {other}
Indexes: {field} (unique), {field} (full-text search)
```

Walk through each entity one at a time. After presenting each entity, pause and ask if it looks right or needs changes. Once all entities are confirmed, move on.

---

## Step 4 — Confirm full understanding

Present a structured summary including the data model:

```
Product: {name}
Target user: {persona}

Problems identified:
1. {problem 1}
2. {problem 2}
...

Vision: {1-2 sentence vision statement}
Differentiator: {what makes this unique}

Data Model:
- {Entity1} ({field_count} fields) → has many {Entity2}
- {Entity2} ({field_count} fields) → belongs to {Entity1}
- ...
```

Wait for approval. Incorporate any corrections.

---

## Step 5 — Generate the pages

Once approved, generate the full set of pages. Use the exact same HTML structure, CSS classes, and design patterns as the VR Pipeline Dashboard pages in `$TOOLKIT_DIR/idea-template/design-system/example-vr-pipeline/`.

### Colour rotation

Each new idea gets a unique brand colour. Do NOT reuse `#6C3FA0` (purple, used by VR Pipeline Dashboard). Pick a distinct primary colour and derive the palette from it. Good candidates:

- Teal: `#0D9488` (accent: `#5EEAD4`)
- Coral: `#E11D48` (accent: `#FDA4AF`)
- Indigo: `#4338CA` (accent: `#A5B4FC`)
- Amber: `#D97706` (accent: `#FDE68A`)
- Emerald: `#059669` (accent: `#6EE7B7`)
- Cyan: `#0891B2` (accent: `#67E8F9`)
- Rose: `#BE123C` (accent: `#FECDD3`)

Create a `{idea}-styles.css` file that overrides the brand tokens (same structure as `vr-styles.css` but with the new colour). Include the deployment diagram components (`.deploy-diagram`, `.deploy-region`, `.deploy-node`, `.deploy-connector`, `.deploy-externals`, `.deploy-footer`) and the click-to-expand modal components (`.diagram-expandable`, `.diagram-modal-overlay`, `.diagram-modal-content`, `.diagram-modal-close`, `.diagram-modal-body`). Reference `$IDEAS_DIR/Hindsite/hindsite-styles.css` for the full implementation of these components.

### Icon

Create a novel SVG favicon for the idea. The icon should:
- Be 32x32 viewBox with a 6px border-radius rect background using the brand gradient
- Contain a simple, recognisable symbol related to the idea's domain
- Use the accent colour for the symbol strokes/fills
- Save as `{idea}-favicon.svg`

### Pages to generate

Create a folder: `$IDEAS_DIR/{Product Name}/`

Copy `$TOOLKIT_DIR/idea-template/design-system/styles.css` as the base stylesheet.

Generate these pages:

#### 1. `{idea}-problem.html` — Problem page
- Hero: "The Problem"
- Section 01: Identified Problems — numbered problem cards (from Step 1)
- Section 02: Problem Statement — a single refined statement block synthesising all problems
- Section 03: Vision — the vision statement block + design principles as notes

#### 2. `{idea}-vision.html` — Vision page
- Hero: "Product Vision"
- Section 01: Vision Statement — the statement block
- Section 02: Design Principles / Core Concepts — card grid of 4 key concepts
- Section 03: System Architecture — layered architecture diagram using arch-diagram, arch-layer, arch-zone patterns. Show clients, frontend, API, data processing, data stores, observability, CI/CD.
- Section 04: Data Model — render the confirmed data model as a series of entity cards. Each entity is displayed as a `.data-model-entity` block showing entity name, a table of fields (name, type, notes), relationships, and indexes. Use the `.data-table` class for field tables. Show an entity relationship summary at the top as a simple flow diagram connecting entities with their relationship types (has many, belongs to, many-to-many).
- Section 05: Event/Data Lifecycle — pipeline flow showing the stages data moves through (use pipeline-stage pills with arrows)
- Section 06: Deployment — physical deployment topology using the deploy-diagram components. Show cloud provider regions (`.deploy-region`), service nodes (`.deploy-node`), connectors (`.deploy-connector`), and external APIs (`.deploy-externals`). Include a cost breakdown table and infrastructure notes.

**Deployment diagram components** (defined in the idea's styles CSS):
- `.deploy-diagram` — outer container with header, body, externals row, and footer
- `.deploy-region` — dashed-border region representing a cloud provider (e.g. Vercel, Supabase, DO). Variants: `.vercel`, `.supabase`, `.do`
- `.deploy-node` — individual service within a region (icon + name + detail + cost tag)
- `.deploy-connector` — arrow between regions with label
- `.deploy-externals` — row of external API dependencies below the main regions
- `.deploy-footer` — version and estimated cost

**Click-to-expand modal**: Both the system architecture and deployment diagrams must be wrapped in `.diagram-expandable` with an `onclick="openDiagramModal('{id}')"`. Add corresponding modal overlays and JavaScript at the end of the page:
- `.diagram-modal-overlay` with `.diagram-modal-content` > `.diagram-modal-close` + `.diagram-modal-body`
- JS: `openDiagramModal(id)` clones diagram innerHTML into modal body, adds `.active` class, locks body scroll
- JS: `closeDiagramModal(event, id)` removes `.active`, unlocks scroll
- JS: Escape key closes all active modals
- Modal renders diagrams at expanded size (larger icons, readable text, no truncation)

#### 3. `{idea}-strategy.html` — Strategy page
- Hero: "Go-to-Market Strategy"
- Section 01: Target Market — card grid of 3-4 market segments
- Section 02: Competition — competitor cards with gap analysis
- Section 03: Strategy Options — 3 candidate strategies with pros/cons (one marked recommended)

#### 4. `{idea}-metrics.html` — Metrics page
- Hero: "Objectives & Key Results"
- Section 01: Indicators — legend of tracked indicators with colour dots
- Section 02-06: 4-5 Objectives, each with 3-4 Key Results referencing specific indicators with target values (% or absolute)

#### 5. `{idea}-initiatives.html` — Initiatives page
- Hero: "Product Initiatives"
- **Section 00: Infrastructure Setup** — ALWAYS the first initiative (I0). This provisions and configures the deployment architecture from the Vision page before any feature work begins. It includes:
  - Every node from the deployment diagram as a feature: hosting platform setup, application scaffold, database provisioning, schema & migrations, API route foundation, cache setup, cron configuration, CI/CD pipeline, external API credentials, monitoring & observability
  - OKR reference: "Prerequisite for all Objectives"
  - Each feature tagged with the deployment icons it provisions
  - This must be complete before any other initiative can ship to production
- Sections 01+: 5-7 feature initiatives, each containing:
  - Initiative header with number, title, subtitle
  - Description paragraph
  - Targeted OKRs section listing which objectives/KRs it addresses with targets
  - Features & Deliverables list with tagged items (Frontend, Backend, Integration, Design, Infra, Growth). Each feature must also show architecture impact as `.feature-arch-icon` spans — small coloured icons matching the deployment diagram nodes. Icons use `data-label` attributes for hover tooltips (no visible text). Reference `$IDEAS_DIR/Hindsite/hindsite-initiatives.html` for the full implementation.

### Navbar

All pages share the same nav: **Problem | Vision | Strategy | Metrics | Initiatives**

- Logo links to the Problem page
- Logo text: `{Product Name}` with the accent portion in the brand colour
- Active state on the current page
- `nav-meta`: "Product Docs · Internal"

### Footer

All pages: `{Product Name}` brand + `{Page name} · {Month Year}`

---

## Step 6 — Commit and push

```bash
cd $IDEAS_DIR
git add "{Product Name}/"
git commit -m "Add {Product Name} product breakdown

Problem, Vision, Strategy, Metrics, and Initiatives pages
generated from /idea command.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push
```

---

## Step 7 — Summary

```
Idea generated: {Product Name}

  Location : Ideas/{Product Name}/
  Pages    : Problem, Vision, Strategy, Metrics, Initiatives
  Colour   : {brand colour name}
  Icon     : {idea}-favicon.svg

  Next step: Review the Problem page, then refine Strategy and Metrics.
```

---

## Rules

- Never skip the Problem gathering step — problems are the foundation
- Always confirm the problem summary before generating pages
- Each idea gets a UNIQUE brand colour — never reuse purple (#6C3FA0)
- The vision statement must be concise (2-3 sentences max)
- OKRs must have specific, measurable targets (%, £, absolute values)
- Initiatives must reference specific OKRs they address
- Features within initiatives must be tagged by type
- All pages must be valid HTML with correct cross-page nav links
- HTML structure MUST use: `<div class="page-wrap">` > `<nav>` + `<main class="main">` > TOC + hero + `<div class="guide-section">` sections + `<div class="guide-footer">`
- Hero tag needs SVG dot: `<svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor"><circle cx="4" cy="4" r="4"/></svg>`
- Hero meta uses `<div><strong>Label</strong> Value</div>` pattern (no colons)
- Section numbers use `<div class="section-number" style="background:{brand-colour};">`
- Architecture and deployment diagrams must be click-to-expand (`.diagram-expandable` + modal)
- The Vision page must include a deployment diagram showing where components physically run, with a cost breakdown table
- Copy `$TOOLKIT_DIR/idea-template/design-system/styles.css` as the base — never modify the original
- Commit to the Ideas repo, not github-pages-docs
