# Blueprint Template — Token Reference

All placeholder tokens in `template-blueprint.html`, organised by tab.

---

## Global / Header

| Token | Description |
|-------|-------------|
| `{PRODUCT_NAME}` | Full product name (used in C4 diagrams and title) |
| `{PRODUCT_TAGLINE}` | h1 content, may include `<span>` for gold accent |
| `{PRODUCT_SUBTITLE}` | Uppercase label (e.g. "PRODUCT & ARCHITECTURE BLUEPRINT") |
| `{VERSION}` | Semantic version (e.g. "v3.0") |

---

## Tab 1: Problems & Problem Statement

| Token | Description |
|-------|-------------|
| `{PROBLEM_1_TITLE}` | First problem title |
| `{PROBLEM_1_DESCRIPTION}` | First problem description |
| `{PROBLEM_2_TITLE}` | Second problem title |
| `{PROBLEM_2_DESCRIPTION}` | Second problem description |
| `{PERSONA_1_NAME}` | First persona name |
| `{PERSONA_1_PAIN}` | First persona's key pain point |
| `{PERSONA_2_NAME}` | Second persona name |
| `{PERSONA_2_PAIN}` | Second persona's key pain point |
| `{COST_OF_INACTION_DESCRIPTION}` | What happens if the problem is not solved |
| `{PROBLEM_STATEMENT}` | **Synthesised problem statement** — a narrative paragraph that ties all the problems, personas, and costs together into a cohesive statement |

---

## Tab 2: Vision & Core Concepts

| Token | Description |
|-------|-------------|
| `{VISION_STATEMENT}` | One-sentence vision statement |
| `{PRINCIPLE_1_NAME}` | First product principle name |
| `{PRINCIPLE_1_DESCRIPTION}` | First principle description |
| `{PRINCIPLE_2_NAME}` | Second principle name |
| `{PRINCIPLE_2_DESCRIPTION}` | Second principle description |
| `{PRINCIPLE_3_NAME}` | Third principle name |
| `{PRINCIPLE_3_DESCRIPTION}` | Third principle description |
| `{CAT_1_NAME}` | First business category |
| `{CAT_1_DESCRIPTION}` | Category description |
| `{CAT_1_FOCUS}` | Key focus areas |
| `{CAT_2_NAME}` | Second category |
| `{CAT_2_DESCRIPTION}` | Second category description |
| `{CAT_2_FOCUS}` | Second category focus |

---

## Tab 3: Strategy

### Target Market

| Token | Description |
|-------|-------------|
| `{TARGET_MARKET_DESCRIPTION}` | Overview of the target market |
| `{MARKET_SIZE}` | Total addressable market size |
| `{MARKET_SEGMENT_1_NAME}` | First market segment |
| `{MARKET_SEGMENT_1_DESC}` | First segment description |
| `{MARKET_SEGMENT_2_NAME}` | Second market segment |
| `{MARKET_SEGMENT_2_DESC}` | Second segment description |

### Competition

| Token | Description |
|-------|-------------|
| `{COMPETITOR_1_NAME}` | First competitor name |
| `{COMPETITOR_1_STRENGTHS}` | First competitor strengths |
| `{COMPETITOR_1_WEAKNESSES}` | First competitor weaknesses |
| `{COMPETITOR_2_NAME}` | Second competitor name |
| `{COMPETITOR_2_STRENGTHS}` | Second competitor strengths |
| `{COMPETITOR_2_WEAKNESSES}` | Second competitor weaknesses |
| `{COMPETITIVE_ADVANTAGE}` | Our key competitive advantage |

### Strategy Options

| Token | Description |
|-------|-------------|
| `{STRATEGY_OPTION_1_NAME}` | First strategy option name |
| `{STRATEGY_OPTION_1_DESC}` | First option description |
| `{STRATEGY_OPTION_1_PROS}` | First option pros |
| `{STRATEGY_OPTION_1_CONS}` | First option cons |
| `{STRATEGY_OPTION_2_NAME}` | Second strategy option name |
| `{STRATEGY_OPTION_2_DESC}` | Second option description |
| `{STRATEGY_OPTION_2_PROS}` | Second option pros |
| `{STRATEGY_OPTION_2_CONS}` | Second option cons |
| `{CHOSEN_STRATEGY}` | The selected strategy name |
| `{STRATEGY_RATIONALE}` | Rationale for the chosen strategy |

---

## Tab 4: Metrics (OKR format)

### Indicators Legend

| Token | Description |
|-------|-------------|
| `{INDICATOR_1_NAME}` | First indicator name (e.g. "Monthly API Calls") |
| `{INDICATOR_1_COLOR}` | CSS color value (e.g. "#059669") |
| `{INDICATOR_2_NAME}` | Second indicator name |
| `{INDICATOR_2_COLOR}` | Second indicator color |
| `{INDICATOR_3_NAME}` | Third indicator name |
| `{INDICATOR_3_COLOR}` | Third indicator color |

> Repeat indicators as needed with `<!-- Repeat -->` comment.

### Objectives & Key Results

Each objective block uses this pattern:

| Token | Description |
|-------|-------------|
| `{OBJ_N_ID}` | Objective ID (e.g. "O1") |
| `{OBJ_N_TEXT}` | Objective description text |
| `{OBJ_N_TIMEFRAME}` | Timeframe (e.g. "Q1–Q2") |
| `{OBJ_N_KR_M_ID}` | Key result ID (e.g. "KR 1.1") |
| `{OBJ_N_KR_M_TEXT}` | Key result description |
| `{OBJ_N_KR_M_INDICATOR_COLOR}` | Indicator dot color |
| `{OBJ_N_KR_M_INDICATOR_NAME}` | Which indicator this KR tracks |
| `{OBJ_N_KR_M_DIRECTION}` | CSS class: `up`, `down`, or `absolute` |
| `{OBJ_N_KR_M_ARROW}` | Arrow HTML entity: `↑`, `↓`, `≥`, or `≤` |
| `{OBJ_N_KR_M_TARGET}` | Target value (e.g. "200 API keys") |

Template includes 2 example objectives: O1 with 3 KRs, O2 with 2 KRs.

---

## Tab 5: Capabilities

| Token | Description |
|-------|-------------|
| `{CAP_01_ID}` | Capability ID (e.g. "CAP-01") |
| `{CAP_01_NAME}` | Capability name |
| `{CAP_01_CATEGORY}` | Parent category |
| `{CAP_01_DESCRIPTION}` | Detailed description |
| `{CAP_02_ID}` | Second capability ID |
| `{CAP_02_NAME}` | Second capability name |
| `{CAP_02_CATEGORY}` | Second capability category |
| `{CAP_02_DESCRIPTION}` | Second capability description |
| `{REG_1_CODE}` | Regulation code tag (in capabilities table) |
| `{REG_1_NAME}` | Regulation full name |
| `{REG_1_SCOPE}` | Regulation scope |
| `{REG_1_SERVICES}` | Affected services |
| `{REG_1_REQUIREMENT}` | Key compliance requirement |
| `{REG_2_CODE}` | Second regulation code |
| `{REG_2_NAME}`, `{REG_2_SCOPE}`, `{REG_2_SERVICES}`, `{REG_2_REQUIREMENT}` | Second regulation details |

> Repeat `CAP_NN_*` and `REG_N_*` patterns.

---

## Tab 6: Use Cases (JavaScript)

Use cases are defined in the `useCases` object in `<script>`.

| Token | Description |
|-------|-------------|
| `{UC_N_SLUG}` | URL-safe use case ID (object key) |
| `{UC_N_TITLE}` | Use case display name |
| `{UC_N_CATEGORY}` | Category (e.g. "Primary", "Operations") |
| `{UC_N_DESCRIPTION}` | Full description |
| `{UC_N_PAIN_1}`, `{UC_N_PAIN_2}` | Pain points |
| `{UC_N_FLOW_1}`, `{UC_N_FLOW_2}`, `{UC_N_FLOW_3}` | Process flow steps |
| `{UC_N_SEQUENCE_PLACEHOLDER}` | Sequence diagram description or SVG |

Template includes 3 example use cases. Each references `{REG_N_CODE}` and `{SVC_NN_NAME}` in its regulations/services arrays.

---

## Tab 7: Architecture

### C4 Model — L1 System Context

| Token | Description |
|-------|-------------|
| `{ACTOR_1_NAME}` | Primary actor/person |
| `{ACTOR_1_DESCRIPTION}` | What they do |
| `{SYSTEM_DESCRIPTION}` | Central system description |
| `{EXT_SYSTEM_1_NAME}` | External system name |
| `{EXT_SYSTEM_1_DESCRIPTION}` | External system description |

### C4 Model — L2 Containers

| Token | Description |
|-------|-------------|
| `{CONTAINER_1_NAME}` | First container name |
| `{CONTAINER_1_DESCRIPTION}` | Container description |
| `{CONTAINER_1_TECH}` | Technology stack |
| `{CONTAINER_2_NAME}` | Second container |
| `{CONTAINER_2_DESCRIPTION}` | Second container description |
| `{CONTAINER_2_TECH}` | Second container tech |
| `{INFRA_1_NAME}` | Infrastructure component |
| `{INFRA_1_DESCRIPTION}` | Infrastructure description |

### Service Catalogue

| Token | Description |
|-------|-------------|
| `{SVC_01_ID}` | Service ID |
| `{SVC_01_NAME}` | Service name |
| `{SVC_01_CAPABILITIES}` | Capabilities it implements |
| `{SVC_01_PROTOCOL}` | API/protocol type |
| `{SVC_01_DATA}` | Data entities owned |
| `{SVC_01_SLO}` | Service level objective |
| `{SVC_01_CATEGORY}` | Category (used in JS `services` array) |
| `{SVC_01_DESCRIPTION}` | Description (used in JS `services` array) |
| `{SVC_02_*}`, `{SVC_03_*}` | Same patterns for additional services |

### Structurizr DSL Mapping

| Token | Description |
|-------|-------------|
| `{STRUCTURIZR_WORKSPACE_URL}` | URL to live Structurizr workspace |
| `{DSL_COMPONENT_1_NAME}` | First DSL component name |
| `{DSL_COMPONENT_1_ELEMENT}` | Structurizr element type |
| `{DSL_COMPONENT_1_TECH}` | Technology tag |
| `{DSL_COMPONENT_2_*}` | Same pattern for second component |

---

## Tab 8: Observability & Security (8 sections)

### Section 01: Log Routing + Mandatory Instrumentation

| Token | Description |
|-------|-------------|
| `{LOG_DEST_1}` | First log destination (e.g. "Loki") |
| `{LOG_DEST_2}` | Second log destination (e.g. "Tempo") |
| `{LOG_DEST_3}` | Third log destination (e.g. "Prometheus") |
| `{INSTRUMENTATION_LIBRARY}` | Shared instrumentation library name (e.g. "@platform/logger") |
| `{MESSAGE_BUS_NAME}` | Message bus name (e.g. "Kafka") |
| `{METRIC_HISTOGRAM_NAME}` | Primary latency histogram metric name |
| `{METRIC_CONSUMER_LAG_NAME}` | Consumer lag metric name |
| `{METRIC_SECRET_EXPIRY_NAME}` | Secret expiry gauge metric name |
| `{EVENT_ENVELOPE_STANDARD}` | Event envelope standard (e.g. "CloudEvents 1.0") |
| `{DATA_CLASS_LEVELS}` | Classification levels (e.g. "CONFIDENTIAL / INTERNAL / PUBLIC") |

### Section 02: Security Posture

| Token | Description |
|-------|-------------|
| `{ZERO_TRUST_IMPL}` | Zero trust implementation |
| `{ZERO_TRUST_SCOPE}` | Zero trust scope |
| `{MTLS_IMPL}` | mTLS implementation |
| `{MTLS_SCOPE}` | mTLS scope |
| `{SECRET_ROTATION_IMPL}` | Secret rotation implementation |
| `{SECRET_ROTATION_SCOPE}` | Secret rotation scope |
| `{BLAST_RADIUS_IMPL}` | Blast radius containment |
| `{BLAST_RADIUS_SCOPE}` | Blast radius scope |
| `{CVE_IMPL}` | CVE scanning implementation |
| `{CVE_SCOPE}` | CVE scanning scope |
| `{AUDIT_IMPL}` | Audit trail implementation |
| `{AUDIT_SCOPE}` | Audit trail scope |

### Section 03: Logging Schema

| Token | Description |
|-------|-------------|
| `{SVC_CAT_1_NAME}` | First service category |
| `{SVC_CAT_1_SCHEMA}` | Log schema/format |
| `{SVC_CAT_1_RETENTION}` | Log retention period |
| `{SVC_CAT_1_SAMPLING}` | Sampling rate |
| `{SVC_CAT_2_*}` | Second service category (same pattern) |

### Section 04: Data Freshness SLOs

| Token | Description |
|-------|-------------|
| `{FRESHNESS_1_NAME}` | First data pipeline name |
| `{FRESHNESS_1_SLI}` | Service level indicator |
| `{FRESHNESS_1_TARGET}` | SLO target |
| `{FRESHNESS_1_VOLUME}` | Data volume |
| `{FRESHNESS_2_*}` | Second pipeline (same pattern) |

### Section 05: Per-Service Domain Metrics

| Token | Description |
|-------|-------------|
| `{DOMAIN_METRIC_SVC_1_NAME}` | First service name |
| `{DOMAIN_METRIC_SVC_1_METRICS}` | Comma-separated metric names (e.g. "contracts_ingested_total, dedup_hits_total") |
| `{DOMAIN_METRIC_SVC_2_NAME}` | Second service name |
| `{DOMAIN_METRIC_SVC_2_METRICS}` | Second service metrics |
| `{DOMAIN_METRIC_SVC_3_NAME}` | Third service name |
| `{DOMAIN_METRIC_SVC_3_METRICS}` | Third service metrics |

> Repeat for each service.

### Section 06: Per-Service Data Classification

| Token | Description |
|-------|-------------|
| `{DATA_CLASS_SVC_1_NAME}` | First service name |
| `{DATA_CLASS_SVC_1_LEVEL}` | Classification level (e.g. "CONFIDENTIAL") |
| `{DATA_CLASS_SVC_1_RATIONALE}` | Why this classification |
| `{DATA_CLASS_SVC_2_*}` | Second service (same pattern) |
| `{DATA_CLASS_SVC_3_*}` | Third service (same pattern) |

> Repeat for each service.

### Section 07: Environment Observability Matrix

Each environment uses a table with Component / Status / Notes columns. Environment-specific tokens:

**Development:**
`{ENV_DEV_PURPOSE}`, `{ENV_DEV_OTEL_NOTES}`, `{ENV_DEV_LOG_NOTES}`, `{ENV_DEV_TRACE_NOTES}`, `{ENV_DEV_METRIC_NOTES}`

**CI:**
`{ENV_CI_PURPOSE}`, `{ENV_CI_OTEL_NOTES}`, `{ENV_CI_LOG_NOTES}`, `{ENV_CI_HEALTH_NOTES}`

**Test (Integration):**
`{ENV_TEST_PURPOSE}`, `{ENV_TEST_LOG_NOTES}`, `{ENV_TEST_TRACE_NOTES}`, `{ENV_TEST_METRIC_NOTES}`, `{ENV_TEST_HEALTH_NOTES}`, `{ENV_TEST_AUDIT_NOTES}`

**Pre-Production:**
`{ENV_PREPROD_PURPOSE}`, `{ENV_PREPROD_OTEL_NOTES}`, `{ENV_PREPROD_LOG_NOTES}`, `{ENV_PREPROD_TRACE_NOTES}`, `{ENV_PREPROD_METRIC_NOTES}`, `{ENV_PREPROD_PII_NOTES}`, `{ENV_PREPROD_AUDIT_NOTES}`, `{ENV_PREPROD_DASHBOARD_NOTES}`, `{ENV_PREPROD_REPLICA_NOTES}`

**Production:**
`{ENV_PROD_PURPOSE}`, `{ENV_PROD_OTEL_NOTES}`, `{ENV_PROD_LOG_NOTES}`, `{ENV_PROD_AUDIT_NOTES}`, `{ENV_PROD_METRIC_NOTES}`

### Section 08: Audit & Compliance

| Token | Description |
|-------|-------------|
| `{AUDIT_PIPELINE_DESCRIPTION}` | Audit pipeline overview |
| `{AUDIT_STORAGE_TYPE}` | Storage type (e.g. "WORM S3 Object Lock") |
| `{AUDIT_RETENTION_PERIOD}` | Retention (e.g. "7 years") |
| `{AUDIT_ISOLATION_DESC}` | How audit is isolated from operational telemetry |
| `{AUDIT_WRITE_BEHAVIOUR}` | Write semantics (e.g. "Synchronous — before API response") |
| `{AUDIT_DB_PERMISSIONS}` | DB permission model (e.g. "INSERT only; separate audit-reader role") |
| `{AUDIT_COMPLIANCE_BASIS}` | Regulatory basis (e.g. "UK GDPR Art.30, SRA AI accountability") |
| `{SECRET_TYPE_1_NAME}` | First secret type (e.g. "API keys") |
| `{SECRET_TYPE_1_ROTATION}` | Rotation period (e.g. "90 days") |
| `{SECRET_TYPE_2_NAME}` | Second secret type |
| `{SECRET_TYPE_2_ROTATION}` | Second rotation period |
| `{SECRET_TYPE_3_NAME}` | Third secret type |
| `{SECRET_TYPE_3_ROTATION}` | Third rotation period |

---

## Tab 9: Delivery

### Initiatives

| Token | Description |
|-------|-------------|
| `{INIT_01_ID}` | Initiative ID (e.g. "I1") |
| `{INIT_01_NAME}` | Initiative name |
| `{INIT_01_JOURNEYS}` | Journeys it enables |
| `{INIT_01_CAPABILITIES}` | Capabilities delivered |
| `{INIT_01_SERVICES}` | Services involved |
| `{INIT_01_SIZE}` | Effort estimate (S/M/L/XL) |
| `{INIT_02_*}` | Second initiative (same pattern) |

---

## Tab 10: Cost Estimate (JavaScript)

### Calculator Controls

| Token | Description |
|-------|-------------|
| `{SCALE_OPTION_1}` | First scale label (e.g. "Startup") |
| `{SCALE_OPTION_2}` | Second scale label |
| `{SCALE_OPTION_3}` | Third scale label |
| `{REGION_OPTION_1}` | First region label |
| `{REGION_OPTION_2}` | Second region label |
| `{REGION_OPTION_3}` | Third region label |

### Cost Items

| Token | Description |
|-------|-------------|
| `{COST_CATEGORY_1}` | First cost category (e.g. "Compute") |
| `{COST_CATEGORY_2}` | Second cost category |
| `{COST_ITEM_1_NAME}` | First item name |
| `{COST_ITEM_1_LOW}` | First item low estimate (number) |
| `{COST_ITEM_1_HIGH}` | First item high estimate (number) |
| `{COST_ITEM_2_NAME}` | Second item name |
| `{COST_ITEM_2_LOW}` / `{COST_ITEM_2_HIGH}` | Second item range |
| `{COST_ITEM_3_NAME}` | Third item name |
| `{COST_ITEM_3_LOW}` / `{COST_ITEM_3_HIGH}` | Third item range |

---

## Notes

1. **Repeat comments** — `<!-- Repeat for each X -->` and `// Add more` indicate expansion points.
2. **Token naming** — `{SECTION_INDEX_PROPERTY}`, e.g. `{SVC_01_NAME}`, `{OBJ_1_KR_2_TARGET}`.
3. **JS data structures** — `useCases`, `services`, `costData` power interactive features.
4. **OKR direction classes** — Use `up` (green ↑), `down` (red ↓), or `absolute` (blue ≥/≤).
5. **Total unique tokens** — ~273 across all 10 tabs.
