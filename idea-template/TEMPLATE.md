# {PROJECT_NAME} — Product & Architecture Blueprint

> This template merges product vision with technical architecture.
> Fill each section in order. Later sections depend on earlier ones.

---

## 1. Problem Statement

### Problem observations
- {What users struggle with today}
- {What existing solutions get wrong}
- {What's changing in the market/regulation}

### Who feels this pain
- {Primary persona}: {their role, their frustration}
- {Secondary persona}: {their role, their frustration}

### Cost of inaction
- {What happens if this problem isn't solved}

---

## 2. Vision

### One-liner
{One sentence: what this product does and for whom}

### Product principles
1. {Principle 1 — e.g. "API-first: every capability accessible programmatically"}
2. {Principle 2}
3. {Principle 3}

---

## 3. Categories

Categories are domain groupings that organise capabilities into coherent
business areas. Not hierarchical beyond one level.

| Category | Description | Example capabilities |
|---|---|---|
| {e.g. Account Services} | {What this domain covers} | {Current accounts, savings, switching} |
| {e.g. Lending & Credit} | | |
| {e.g. Payments & Cash} | | |
| {e.g. Risk & Compliance} | | |

---

## 4. Capabilities

A capability is a **stable business ability** the platform provides. It:
- Is tech-agnostic — we'd still need it if we replaced all systems
- Exists whether or not anyone is using it right now
- Has a regulatory context
- Describes WHAT the platform can do, not HOW

| ID | Capability | Category | Description | Regulations |
|---|---|---|---|---|
| CAP-01 | {e.g. Current Account Management} | {Account Services} | {Open, maintain, close current accounts} | {FCA BCOBS, PSRs 2017} |
| CAP-02 | {e.g. Term Loan Origination} | {Lending & Credit} | {Assess, approve, disburse term loans} | {CCA 1974, IFRS 9} |
| CAP-03 | | | | |

---

## 5. Journeys

A journey is a **persona goal across steps/touchpoints** that can span
multiple capabilities. It has:
- A persona (who)
- A goal (what they want to achieve)
- Stages with entry/exit criteria
- Measurable drop-off points

### Journey: {J-01: e.g. SME applies for a term loan}

**Persona:** {e.g. CFO of a £2M revenue company}
**Goal:** {e.g. Secure a £200K term loan within 5 business days}
**Success metric:** {e.g. Application-to-disbursement < 5 days, drop-off < 20%}

| Step | Description | Capability used | Channel | Drop-off risk |
|---|---|---|---|---|
| 1 | {e.g. CFO logs in and starts application} | {CAP-01: Account Mgmt} | {Web portal} | {Low} |
| 2 | {e.g. Completes KYC/AML checks} | {CAP-05: KYC Onboarding} | {Web + async} | {Medium — document upload friction} |
| 3 | {e.g. Submits financial documents} | {CAP-02: Loan Origination} | {Web portal} | {High — complexity of requirements} |
| 4 | {e.g. Credit decision made} | {CAP-06: Credit Decisioning} | {Automated} | {N/A — system decision} |
| 5 | {e.g. Loan offer presented, accepted} | {CAP-02: Loan Origination} | {Web + email} | {Medium — pricing negotiation} |
| 6 | {e.g. Funds disbursed to account} | {CAP-03: Payments} | {Automated} | {Low} |

### Journey: {J-02: ...}

{Repeat for each major persona goal}

---

## 6. Technical Services

A technical service is a **deployable software boundary** that:
- Encapsulates logic and data
- Exposes a contract (API, events, or both)
- Has SLOs (latency, availability, error rate)
- Can be owned end-to-end by a team (build + run)
- Can deploy independently
- Can be consumed by other systems via its contract

Technical services **realise** capabilities:
- A capability may be realised by multiple technical services
- A technical service may support multiple capabilities

| ID | Service | Capabilities realised | Contract | Data owned | SLO | Starter template |
|---|---|---|---|---|---|---|
| SVC-01 | {e.g. Customer Profile Service} | {CAP-01, CAP-05} | {REST API + events} | {Customer, Address, KYC Record} | {p99 < 200ms, 99.9%} | {starter-api} |
| SVC-02 | {e.g. Loan Origination Service} | {CAP-02} | {REST API + events} | {Application, Facility, Offer} | {p99 < 500ms, 99.9%} | {starter-orchestrator} |
| SVC-03 | {e.g. Credit Decision Service} | {CAP-06} | {REST API} | {Decision, Score, Model} | {p99 < 1s, 99.95%} | {starter-api} |
| SVC-04 | {e.g. Payments Processing} | {CAP-03} | {REST + events + SWIFT} | {Payment Instruction, Settlement} | {p99 < 300ms, 99.99%} | {starter-worker} |
| SVC-05 | {e.g. Notification Service} | {All} | {Events (consumer)} | {Notification, Template, Preference} | {p99 < 500ms, 99.9%} | {starter-notification} |
| SVC-06 | {e.g. Audit Service} | {All} | {Events (consumer)} | {Audit Event} | {p99 < 100ms, 99.99%} | {starter-audit} |
| SVC-07 | {e.g. Customer Portal} | {All (UI)} | {Browser} | {None (BFF)} | {p99 < 2s, 99.9%} | {starter-web} |
| SVC-08 | {e.g. API Gateway} | {All (routing)} | {REST} | {None (routing)} | {p99 < 50ms, 99.99%} | {starter-gateway} |

### Service dependency matrix

| Service | Depends on | Required by |
|---|---|---|
| SVC-01 Customer Profile | SVC-06 Audit | SVC-02, SVC-04, SVC-07 |
| SVC-02 Loan Origination | SVC-01, SVC-03, SVC-04, SVC-06 | SVC-05, SVC-07 |
| ... | | |

---

## 7. C4 Model

### C1 — System Context

The platform as a whole and its external dependencies.
{Reference: commercial-banking-c4.html system context view}

| External system | Interaction | Protocol |
|---|---|---|
| {e.g. SWIFT Network} | {International payments} | {SWIFT MT/MX} |
| {e.g. Faster Payments (Vocalink)} | {UK domestic payments} | {ISO 20022} |
| {e.g. Companies House} | {Company verification} | {REST API} |
| {e.g. Credit Reference Agencies} | {Credit checks} | {REST API} |
| {e.g. HMRC} | {Tax reporting} | {XBRL / API} |

### C2 — Containers (per technical service)

Each technical service maps to one or more containers (deployable units).

| Service | Container(s) | Technology | Starter template |
|---|---|---|---|
| SVC-01 Customer Profile | customer-profile-api | FastAPI / PostgreSQL | starter-api |
| SVC-02 Loan Origination | loan-origination-api, loan-workflow-engine | FastAPI + state machine | starter-api, starter-orchestrator |
| SVC-03 Credit Decision | credit-decision-api | FastAPI + ML model | starter-api, starter-ml |
| SVC-04 Payments | payments-api, payments-worker | FastAPI + Kafka consumer | starter-api, starter-worker |
| SVC-05 Notification | notification-service | Node.js multi-channel | starter-notification |
| SVC-06 Audit | audit-service | Node.js append-only | starter-audit |
| SVC-07 Customer Portal | customer-web | Next.js | starter-web |
| SVC-08 API Gateway | gateway | Express / Node.js | starter-gateway |
| — | PostgreSQL cluster | PostgreSQL 16 | (infrastructure) |
| — | Redis cluster | Redis 7 | (infrastructure) |
| — | Kafka / Redpanda | Event streaming | (infrastructure) |
| — | S3 / MinIO | Document storage | (infrastructure) |
| — | Observability stack | Grafana LGTM | starter-observability |

### C3 — Components (per container)

Defined per service during the Refinement stage. Not upfront.
The Refinement Team produces C3 detail for each Deliverable.

---

## 8. Data Entities

Canonical business objects that flow through services.

| Entity | System of record | Classification | Retention | Consumers |
|---|---|---|---|---|
| {e.g. Customer} | {SVC-01} | {PII} | {6 years post-closure} | {SVC-02, SVC-04, SVC-07} |
| {e.g. Facility} | {SVC-02} | {Financial} | {10 years} | {SVC-03, SVC-04, SVC-06} |
| {e.g. Payment Instruction} | {SVC-04} | {Financial} | {7 years} | {SVC-06, SVC-05} |
| {e.g. KYC Record} | {SVC-01} | {PII + Regulatory} | {5 years post-relationship} | {SVC-02, SVC-06} |
| {e.g. Audit Event} | {SVC-06} | {Regulatory} | {7 years (financial), 5 years (access)} | {Read-only query API} |

---

## 9. Regulations

| Regulation | Scope | Services affected | Key requirement |
|---|---|---|---|
| {e.g. MLR 2017} | {AML/KYC} | {SVC-01, SVC-06} | {Customer due diligence, ongoing monitoring} |
| {e.g. IFRS 9} | {Credit risk} | {SVC-02, SVC-03} | {Expected credit loss provisioning} |
| {e.g. PSRs 2017} | {Payments} | {SVC-04} | {Strong customer authentication} |
| {e.g. SM&CR} | {Governance} | {All} | {Senior management accountability} |

---

## 10. Initiatives

Timeboxed change efforts delivering increments to journeys/capabilities
via technical services. Ordered by dependency — later initiatives build
on earlier ones.

| # | Initiative | Journeys impacted | Capabilities delivered | Services involved | Approx size |
|---|---|---|---|---|---|
| I1 | {Infrastructure Setup} | {None (foundation)} | {None} | {All — pipeline, Docker, CI/CD} | {S} |
| I2 | {Customer Onboarding} | {J-01 steps 1-2} | {CAP-01, CAP-05} | {SVC-01, SVC-06, SVC-07, SVC-08} | {L} |
| I3 | {Loan Origination} | {J-01 steps 3-6} | {CAP-02, CAP-06} | {SVC-02, SVC-03, SVC-04, SVC-05} | {XL} |
| I4 | {Payments Core} | {J-02} | {CAP-03} | {SVC-04, SVC-05, SVC-06} | {L} |

### Decomposition chain

```
Initiative
  └─► Deliverable (pipeline unit — Business Rules, Gherkin AC, Data Model, API Surface)
        └─► Task (created by Refinement Team — file paths, patterns, acceptance criteria)
```

Deliverables are decomposed journey-first:
- "A user can complete KYC onboarding" (not "build the KYC service")
- App Shell is always the first feature Deliverable
- Each Deliverable answers: "what can the user do after this that they couldn't before?"

---

## 11. Metrics

| Metric | Target | Measured by |
|---|---|---|
| {e.g. Onboarding completion rate} | {> 80%} | {Journey J-01 drop-off tracking} |
| {e.g. Loan time-to-disbursement} | {< 5 business days} | {Journey J-01 step timestamps} |
| {e.g. Payment processing latency} | {p99 < 300ms} | {SVC-04 OTel metrics} |
| {e.g. System availability} | {99.9%} | {Health endpoint monitoring} |
| {e.g. Audit completeness} | {100% of financial actions} | {SVC-06 event count vs source count} |

---

## 12. Structurizr Workspace

The C4 model is maintained as a Structurizr DSL file at `architecture/workspace.dsl`.
Generated during the Solution Architecture phase. Updated as services are added.

Views:
- C1 System Context — platform + external dependencies
- C2 Containers — all deployable units + relationships
- C2 per-service — focused view of one service's containers
- Deployment: Production — cloud hosting topology
- Deployment: CI — Docker Compose treemail-ci
- Deployment: RC — Docker Compose treemail-rc
- Deployment: Prod-parity — Docker Compose treemail-prod

---

## Appendix: How this template maps to the pipeline

| This template | Pipeline artefact | Who produces it |
|---|---|---|
| Problem + Vision | Confluence pages (via `/migrate-idea`) | Product owner |
| Categories + Capabilities | Reference for all teams | Solution Architect |
| Journeys | Deliverable acceptance criteria source | Solution Architect + Product |
| Technical Services | ARCHITECTURE.md, starter template selection | Solution Architect |
| C4 Model | `workspace.dsl`, deployment diagrams | Solution Architect |
| Data Entities | Prisma schema design, data model section of Deliverables | Solution Architect |
| Regulations | Compliance requirements in Deliverables | Solution Architect + Legal |
| Initiatives | Jira Initiatives (via `/create-jira-initiative`) | `/create-project` |
| Deliverables | Jira Deliverables (via `/create-jira-deliverable`) | `/create-project` |
| Tasks | Jira Tasks (via Refinement Team) | Refinement Team |

## Appendix: Relationships summary

```
Category ──1:many──► Capability
Capability ──1:many──► Journey Step (via Journey)
Journey ──1:many──► Step
Step ──many:1──► Capability (uses)
Capability ──many:many──► Technical Service (realised by)
Technical Service ──1:many──► Container (C2, implemented as)
Container ──1:many──► Component (C3, contains)
Technical Service ──many:many──► Regulation (constrained by)
Technical Service ──many:many──► Data Entity (owns or consumes)
Initiative ──1:many──► Deliverable (delivers via)
Deliverable ──1:many──► Task (broken down by Refinement Team)
```
