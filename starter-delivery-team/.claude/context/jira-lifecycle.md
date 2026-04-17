# Jira lifecycle — project, components, tickets

Read by: Programme Lead (always), Capability Lead + Team Lead (for
ticket creation rules that apply to them).

Single source of truth for:
1. Who creates the Jira **projects**, and when
2. Who populates the **components and labels** dropdowns, and when
3. Who creates every **ticket**, in which project, at which stage
4. What goes into **Sprint 0** (the repeatable rule)
5. What goes into each **Journey Deliverable** (the slice rule)
6. What to do with architecture **not touched by any journey**

---

## 1. Project setup — one-time, human-driven

Three Jira projects are created **before any agent pipeline runs**.
The human invokes the skills below. Agents do not create Jira projects.

| Project | Key            | Issue type    | Workflow                                                                 |
|---------|----------------|----------------|--------------------------------------------------------------------------|
| Foundation (design) | {FOUND_KEY} | Task           | Draft → In review → Approved → Baselined                                  |
| Analytical Modelling (design) | {MODEL_KEY} | Epic + Story | Epic: Backlog → In progress → In review → Stable → Revised              |
| Development (build) | {DEV_KEY}   | Deliverable, Task, Issue | Deliverable: Backlog → In Refinement → In Development → In Local Test → In Integration Test → In E2E Impact Test → In Full E2E Regression → Release / Production → Done. Task: Open → In Progress → Done. |

Human setup sequence:

```
1. Invoke /create-jira-project (once per project — three runs)
   - FOUND: simple Task-based workflow
   - MODEL: Epic-based workflow for journeys
   - DEV: Deliverable workflow matching development-team/.claude/context/pipeline-stages.md

2. Capture credentials:
   - Create API token at https://id.atlassian.com/manage-profile/security/api-tokens
   - Write JIRA_EMAIL and JIRA_API_TOKEN to
     development-team/infra/.env.jira

3. Configure dev-team scripts (one-time):
   - development-team/infra/jiractl — set JIRA_SITE, CLOUD_ID
   - development-team/infra/pipelinectl — set PROJECT_KEY (= {DEV_KEY}),
     SERVICE_REPOS (leave empty — populated after Gate 1),
     transition IDs (discover via jiractl transitions)
   - development-team/infra/envctl — SERVICE_REPOS (same rule)
   - development-team/infra/dashboard.py — PROJECT_SLUG, WEB_PORT_CI

4. Replace {PLACEHOLDER}s across the delivery-team folder:
   grep -rn "{[A-Z_]\+}" starter-delivery-team/ | grep -v node_modules
```

Only after all four steps may the Programme Lead spawn the Capability
Lead. The Capability Lead has a hard startup check for `.env.jira` —
if it is missing, the pipeline stops.

---

## 2. Components and labels

### Components (required on every Deliverable)

Components in the **DEV project** represent **service repos**.
`jiractl create` refuses to create a Deliverable without components —
this is an intentional guard rail.

**Lifecycle:**

| Moment                                   | Action                                              | Who       |
|------------------------------------------|-----------------------------------------------------|-----------|
| Project setup                            | DEV project exists with **zero** components         | Human     |
| Gate 1 passes                            | Populate components from `service-catalogue.json`   | Human, prompted by Programme Lead |
| Gate 2 passes (new services introduced)  | Add any new components for new services in slice    | Human, prompted by Programme Lead |

The human invokes `/create-jira-components` — the Programme Lead does
not create components itself because component creation in Jira typically
requires project-admin permission, and that permission is human-held.

**Programme Lead prompt (after Gate 1):**

> "Capability Lead has passed Gate 1. Services in
> `capability-team/artefacts/architecture/service-catalogue.json`:
> {list}. Please run `/create-jira-components` against the DEV project
> to add these as components. Reply when done so I can create the
> Sprint 0 Deliverable."

**Programme Lead prompt (per Gate 2, if journey introduces new services):**

> "Gate 2 passed for journey {slug}. This journey introduces new
> services: {list}. Please run `/create-jira-components` to add these,
> then I will create the Deliverable."

If the journey introduces no new services, the Programme Lead creates
the Deliverable immediately.

### Labels (optional — capabilities)

Jira components are a single flat set (services). To filter by
**capability**, Deliverables carry a label `cap:{capability-id}`
(e.g. `cap:CAP-001`).

The Programme Lead sets this label when creating each Deliverable —
no human interaction needed. Labels are free-text in Jira.

### Other useful labels (conventions)

| Label               | Set by         | Meaning                                            |
|---------------------|----------------|----------------------------------------------------|
| `cap:{CAP-NNN}`     | Programme Lead | Which capability the Deliverable belongs to        |
| `slice:journey`     | Programme Lead | This is a journey Deliverable                      |
| `slice:sprint-0`    | Programme Lead | Sprint 0 platform work                             |
| `slice:remainder`   | Programme Lead | Architectural remainder (see §6)                   |
| `spec-defect`       | Team Lead      | Build failed because the spec is wrong             |
| `blocked-by-refinement` | Programme Lead | Deliverable paused waiting for a refinement    |
| `production-defect` | Team Lead      | Live defect, human prioritisation needed           |
| `needs-human`       | Either Lead    | FIX EXHAUSTED escalation                           |

---

## 3. Ticket creation — end to end

| Ticket type                | Project    | Created by        | When                                                 | How                                              |
|----------------------------|------------|-------------------|------------------------------------------------------|--------------------------------------------------|
| FOUND step ticket (×6)     | FOUND      | Capability Lead   | Start of each Phase A/B step (1–6)                   | MCP `createJiraIssue` (no jiractl in capability side) |
| MODEL journey epic (×N)    | MODEL      | Capability Lead   | Immediately after **Gate 1** passes — one batch, one epic per row in `journey-inventory.json`, priority matches inventory order | MCP `createJiraIssue` (Epic type)        |
| DEV Sprint 0 Deliverable   | DEV        | Programme Lead    | After Gate 1, **after** components populated by human | `development-team/infra/jiractl create-md Deliverable` |
| DEV Journey Deliverable    | DEV        | Programme Lead    | On each **Gate 2** pass                               | `development-team/infra/jiractl create-md Deliverable` |
| DEV Task (child)           | DEV        | Refinement Team   | During **In Refinement** stage                        | `development-team/infra/jiractl create Task ... {DEV_KEY}-{parent}` |
| DEV Issue (regression/prod)| DEV        | Team Lead         | On regression or production defect                    | `jiractl create Issue` / MCP                     |
| DEV Architectural Remainder Deliverable | DEV | Programme Lead | After all prioritised journeys done, only if real (see §6) | `jiractl create-md Deliverable` |

No tickets come from any other source. If a human wants to add work,
they add a row to `journey-inventory.json` (pre-Gate 1) or create a
MODEL epic directly (post-Gate 1) — the Capability Lead picks it up on
its next cycle.

### Sequence of ticket events — bootstrap + first journey

```
T0  Human:            /create-jira-project  × 3
T1  Human:            .env.jira + script placeholders
T2  Capability Lead:  FOUND tickets — step 1 through step 6 (as each step begins)
T3  Capability Lead:  GATE 1 PASSED signal
T4  Capability Lead:  creates MODEL epics for all rows in journey-inventory
T5  Programme Lead:   prompts human for /create-jira-components
T6  Human:            /create-jira-components against DEV with service-catalogue
T7  Programme Lead:   DEV Sprint 0 Deliverable created
T8  Team Lead:        polls DEV, picks up Sprint 0, decomposes into Tasks, builds
T9  Team Lead:        DELIVERABLE DONE (Sprint 0)
T10 Capability Lead:  picks MODEL epic 1 (highest priority), transitions to In progress
T11 Capability Lead:  runs Phase C steps 7–13, Gate 2 passes
T12 Programme Lead:   verifies evidence; prompts human for new components if any
T13 Programme Lead:   DEV Journey Deliverable 1 created
T14 Team Lead:        builds journey 1 slice
…
```

---

## 4. Sprint 0 — what goes in (repeatable rule)

**The test:** can this item be specified using ONLY the Phase B
architecture artefacts, **without any journey model (steps 7–13)**?

- **YES** → Sprint 0
- **NO** → journey slice

This is the single rule. It generalises across every project using
this starter.

### What that means concretely

| Item                                                            | In Sprint 0? | Source artefact                                |
|-----------------------------------------------------------------|--------------|------------------------------------------------|
| Docker Compose CI / RC / prod-parity skeletons                  | ✓            | `architecture/environment-spec.json`           |
| GitHub Actions CI workflows (ci, release)                       | ✓            | (dev-team starter provides skeletons)          |
| T0 platform services (Event Bus, Schema Registry, Auth, Cache, Audit Pipeline) | ✓ | `architecture/service-dependencies.json` tier T0 |
| T1 infrastructure (OTel Collector, secrets manager)             | ✓            | `architecture/service-dependencies.json` tier T1 |
| Four observability stores (Log, Trace, Metrics, Audit WORM)     | ✓            | `architecture/observability-model.json`        |
| Zero-trust mTLS baseline between services                       | ✓            | `architecture/security-model.json`             |
| Network zones (DMZ / Application / Data / Compliance / Management) | ✓         | `architecture/security-model.json`             |
| Secrets rotation policy infrastructure                          | ✓            | `architecture/security-model.json`             |
| One repo per T0/T1 service                                      | ✓            | `architecture/service-catalogue.json`          |
| Dev-team infra scripts configured and working                   | ✓            | `development-team/infra/*`                     |
| Dashboard visible and green                                     | ✓            | `development-team/infra/dashboard.py`          |
| Any T2/T3/T4 service                                            | ✗            | — (built during journey slices)                |
| Any data model entity                                           | ✗            | — (introduced by journeys)                     |
| Any API endpoint                                                | ✗            | — (introduced by journeys)                     |
| Any event                                                       | ✗            | — (introduced by journeys)                     |
| Domain log categories' field extensions                         | ✗            | — (added per journey as services come online)  |
| Data classification values for business entities                | ✗            | — (per journey)                                |
| Channel UI work                                                 | ✗            | — (separate, outside capability pipeline)      |

### Sprint 0 completion criteria

All must be true before the Programme Lead will create the first
journey Deliverable:

- [ ] All T0 + T1 services run in CI, RC, prod-parity
- [ ] mTLS verified between two services end-to-end
- [ ] All four OTel stores accept and retain data; freshness SLAs met
- [ ] Secrets rotation works for at least one secret (proof)
- [ ] Zero-trust policy denial works: an undeclared call is blocked
- [ ] `envctl rebuild ci && envctl test ci` returns green
- [ ] `dashboard.py` renders all services healthy
- [ ] `jiractl`, `pipelinectl`, `envctl` all configured and working
- [ ] One "hello world" deployable capability ships through the full
      pipeline (proof the foundation supports a journey slice)

### Why this rule is repeatable

Every project specifies the same architectural layers in the same
Phase B artefacts. Sprint 0 is **the portion of the architecture that
has no journey-specific content** — tier T0/T1, infrastructure,
policies, skeletons. The rule "cannot be specified without a journey
model" filters it automatically.

---

## 5. Journey Deliverable — slice scope (repeatable rule)

**The test:** does this item appear in the journey's artefacts
(steps 7–13)?

- **YES** → in this Deliverable's scope
- **NO** → out of scope — will be built by whichever journey introduces it

### What a journey slice contains

| Item                                                           | Source artefact                                     |
|----------------------------------------------------------------|----------------------------------------------------|
| Capability scaffold (new repos, DBs) for a **new** capability  | `service-boundaries.json` (services of new capability) |
| New service within an existing capability                      | `service-boundaries.json`                           |
| Entity implementation (schema, fields, validation)             | `data-model.json`                                   |
| Extensions to existing entities (new fields)                   | `data-model.json` → `entity_extensions`             |
| API endpoint(s) added to the capability's OpenAPI              | `api-contracts/{capability}.openapi.json`           |
| Event producers                                                | `events/event-catalogue.json` (entries with source_service in this slice) |
| Event consumers (with `maps_to` projection)                    | `service-boundaries.json` → `consumed_events`       |
| Integration tests — happy, alt, exception paths                | `sequence-diagrams/*.json` + `.mmd`                 |
| Instrumentation: new log category fields for new services      | `observability-model.json` + `data-model.json`      |
| Security classification for new entities                       | `security-model.json` + `data-model.json`           |
| `service.yaml` manifests for new/updated services              | `service-boundaries.json` + `security-model.json`   |
| C4 L3 component diagram updates for touched capabilities       | `c4-workspace.dsl`                                  |

### What a journey slice does NOT contain

- Any capability not in `capabilities_touched`
- Any service not in this slice's `service-boundaries.json`
- Any entity, field, API, or event not in this journey's artefacts
- "Speculative" fields added because they're "probably needed soon"
- Channel UI work (separate concern — channel teams consume the
  capability APIs the slice exposes)

### The ghost architecture

The full architecture is known from Phase B — capabilities, services,
events, tiers, zones. Each journey slice **realises** one section of
it. The Programme Lead tracks progress in `PORTFOLIO-MAP.md`:

- Capability first-touched-by: {JRN-NNN}
- Service first-built-by: {JRN-NNN}
- Event first-published-by: {JRN-NNN}

This makes the architecture fill in visibly. The journey never invents
a new capability — if a journey needs a capability that wasn't
specified at Phase B, that is a **capability-team refinement**, routed
back through the Programme Lead.

---

## 6. Architectural remainder — after all prioritised journeys

After the last prioritised journey passes Gate 2 + Done, walk the
architecture:

For each **capability** in `service-catalogue.json`:
- Has any journey built services in it? → done.
- No journey touches it? → **this capability was over-specified.**
  Remove it from `service-catalogue.json` (Capability Lead task).
  Do NOT build it speculatively.

For each **service** in `service-dependencies.json` at T2+:
- Built by some journey? → done.
- Not built but a journey referenced it? → refinement — a journey
  missed a dependency. Route back to capability team.
- Not built and not referenced? → same as above: over-specified,
  remove from the catalogue.

For **cross-cutting work** that genuinely spans all journeys
(e.g. a periodic reconciliation job that aggregates data from multiple
capabilities):

- Create **one Remainder Deliverable** in DEV.
- Source the spec from the architecture artefacts — obs/sec/environment
  models usually. If it needs a new data model, it needs a journey,
  not a remainder.
- Label: `slice:remainder`.
- This is the only legitimate non-Sprint-0 non-journey Deliverable.

**Default stance:** if no journey needed it, it was not needed.
Remainders are rare and should be examined for "is this actually a
journey we missed?" before accepting.

---

## 7. Summary — three-question answer

**Q1. Who creates tickets, at what stage?**

- FOUND tickets: **Capability Lead**, one per Phase A/B step (6 total)
- MODEL journey epics: **Capability Lead**, batch at Gate 1, one per
  row in journey-inventory
- DEV Sprint 0 Deliverable: **Programme Lead**, after Gate 1 and
  after components populated
- DEV Journey Deliverable: **Programme Lead**, per Gate 2 pass
- DEV Tasks: **Refinement Team**, during In Refinement stage of each
  Deliverable
- DEV Issues: **Team Lead**, on regression / production defects
- DEV Remainder Deliverable: **Programme Lead**, only if a real
  cross-cutting gap remains after all journeys

**Q2. Who creates components and service/capability dropdowns?**

- Components (services) in DEV: **human**, via
  `/create-jira-components`, prompted by Programme Lead at Gate 1
  and on any Gate 2 that introduces new services. Source list is
  `capability-team/artefacts/architecture/service-catalogue.json`.
- Capability dropdown: not a Jira component — capabilities are set as
  labels (`cap:{CAP-NNN}`) by the Programme Lead automatically at
  Deliverable creation. No human step.

**Q3. Who creates the Jira projects, and when?**

- **Human**, via `/create-jira-project`, **once per project** (three
  runs total), **before the Programme Lead ever runs**. Credentials
  and script placeholders must also be in place. Only then does the
  Programme Lead spawn the Capability Lead.
