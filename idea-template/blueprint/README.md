# Product Blueprint Template

A production-ready, single-file HTML template for creating comprehensive product and architecture blueprints. Features a 10-tab layout with interactive elements including OKR metrics, use-case sidebar, C4 level toggle, dependency matrix, and cost calculator.

## Files

- **template-blueprint.html** — Complete single-file blueprint (~2,055 lines) with all styling and JavaScript inline
- **TOKENS.md** — Reference guide for all placeholder tokens
- **README.md** — This file

## Architecture

### 10-Tab Layout

| # | Tab | Purpose |
|---|-----|---------|
| 1 | **Problems & Problem Statement** | Individual problems, personas, cost of inaction, and a synthesised problem statement narrative |
| 2 | **Vision & Core Concepts** | Vision statement, product principles, business categories |
| 3 | **Strategy** | Target market & segments, competitive analysis, strategy options with pros/cons, chosen strategy |
| 4 | **Metrics** | OKR-style objectives & key results with indicator legend, color-coded targets, and direction arrows |
| 5 | **Capabilities** | Capability matrix with regulatory tags, regulations table |
| 6 | **Use Cases** | Sidebar + detail panel for all use cases with process flows, regulation tags, service tags, and sequence diagram placeholders |
| 7 | **Architecture** | C4 model (L1/L2/L3 toggle), service catalogue with SLOs, service dependency matrix, Structurizr DSL mapping |
| 8 | **Observability & Security** | 8 sections: log routing, mandatory instrumentation (6 requirements), security posture, logging schema, data freshness SLOs, per-service domain metrics, per-service data classification, environment observability matrix (Dev→Prod), audit & compliance pipeline |
| 9 | **Delivery** | Initiatives with capability/service mapping and effort sizing |
| 10 | **Cost Estimate** | Interactive calculator with scale/region dropdowns and per-category breakdown |

### Interactive Features

- **Tab switching** — `setTab()` manages panel visibility and triggers tab-specific renders
- **C4 level toggle** — L1 Context / L2 Container / L3 Component pills via `setLevel()`
- **Use-case sidebar** — Categorised list with click-to-expand detail panel via `selectUC()` / `renderUC()`
- **Collapsible sections** — Every section within a tab can collapse/expand via `toggleSection()`
- **Dependency matrix** — Auto-generated from the `services` JS array via `renderDependencies()`
- **Cost calculator** — Reads scale/region dropdowns and recalculates live via `renderCost()`

### Design System

- **Dark theme** — GitHub-inspired (`--bg: #0a0c10`, `--surface: #111318`, gold accent `#c9a84c`)
- **Typography** — Georgia serif for headings, system sans-serif for body, SF Mono for labels
- **Responsive** — Sidebar hides below 900px, tab bar scrolls horizontally

## How to Use

1. **Open** `template-blueprint.html` in any modern browser — no build step required
2. **Replace tokens** — Find-and-replace `{UPPER_SNAKE_CASE}` placeholders with your product data
3. **Expand repeatable sections** — Look for `<!-- Repeat for each X -->` and `// Add more` comments
4. **Populate JS data structures** — Add entries to the `useCases`, `services`, and `costData` objects in `<script>`

### JavaScript Data Structures

The template includes three JS objects that drive interactive features:

```javascript
// Use cases — each entry powers the sidebar + detail panel
const useCases = {
  '{UC_1_SLUG}': {
    icon: '🏢', title: '...', category: '...',
    description: '...', painPoints: [...],
    processFlow: [...], regulations: [...],
    services: [...], sequenceDiagram: '...'
  }
};

// Services — powers the dependency matrix
const services = [
  { id: '...', name: '...', category: '...', description: '...', dependsOn: [...] }
];

// Cost data — powers the interactive calculator (keyed by scale)
const costData = {
  small: { 'Category': [{ item: '...', low: 0, high: 0 }] },
  medium: { ... },
  large: { ... }
};
```

## Observability & Security (Tab 8) — Design Notes

Tab 8 is the most detailed tab, with 8 collapsible sections. It encodes a complete observability contract:

**Mandatory Service Instrumentation** — Six non-negotiable requirements enforced at startup: structured logging (JSON to stdout with mandatory schema), distributed tracing (OTel SDK with message bus propagation), Prometheus metrics (/metrics with required histograms), health endpoints (/healthz, /readyz, /infoz — three distinct, never conflated), event envelope standard (CloudEvents-style headers on all messages), and service.yaml manifest (machine-readable dependency and classification declarations).

**Per-Service Domain Metrics** — Beyond the platform baseline, each service declares its own domain-specific metrics (e.g. extraction counts by confidence band, webhook DLQ depth).

**Per-Service Data Classification** — Every service declares its data classification (CONFIDENTIAL / INTERNAL / PUBLIC / INFRASTRUCTURE) in `service.yaml`. This drives log routing decisions and WORM audit requirements.

**Environment Observability Matrix** — A table per environment (Development, CI, Test, Pre-Production, Production) specifying what is deployed, what is explicitly excluded, and why. Key principle: observability infrastructure must not be a prerequisite for local development; full pipeline validation is required before production deploy.

**Audit & Compliance** — WORM pipeline specification, retention periods, DB permission model (INSERT-only for services, separate auditor-read role), synchronous write behaviour (before API response returns), and secret rotation schedule.

## Token Reference

See **TOKENS.md** for the complete list of all tokens organised by tab.

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (responsive below 900px)

## Original Source

Based on "UK Commercial Bank for SMEs" product blueprint and C4 architecture documents, with OKR structure inspired by ClauseHub Energy API metrics page.

---

Template version: 3.1 — 2026-04-06
