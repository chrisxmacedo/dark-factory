# starter-chrome-extension

Starter template for browser extensions (Chrome/Firefox, Manifest v3).

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Browser extensions that overlay functionality onto existing web pages or provide
standalone popup/sidebar UIs. Connects to APIs (starter-api, starter-gateway)
for backend data, uses chrome.identity for OAuth, and communicates between
background service workers, content scripts, and popup UI via typed messaging.

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Browser extension / overlay | **starter-chrome-extension** |
| Standalone web app | starter-web |
| Cross-platform desktop app | starter-desktop |
| Mobile companion | starter-ios / starter-android |
| Extension + backend API | **starter-chrome-extension** + starter-api |

## Compatible starters

- **starter-api** -- backend REST API consumed by the extension
- **starter-gateway** -- API gateway/BFF for extension-optimised endpoints
- **starter-web** -- companion web app for full-featured dashboard
- **starter-realtime** -- WebSocket connection for live updates in background worker
- **starter-audit** -- user actions forwarded as audit events via API
- **starter-observability** -- extension telemetry forwarded to the collector

## Key characteristics

- **Manifest v3** -- service worker background, no persistent background pages
- **Cross-browser** -- Chrome primary, Firefox compatibility via webextension-polyfill
- **React popup/sidebar** -- shared component patterns with starter-web
- **Typed messaging** -- type-safe message passing between extension contexts
- **Content script injection** -- DOM manipulation and page augmentation
- **Offline-capable** -- chrome.storage for local data, sync when connected

## Tech stack

TypeScript, React, Vite, Manifest v3, chrome.storage, webextension-polyfill,
Puppeteer, GitHub Actions

## Market applications

### Banking overlays
- Account balance widget on banking websites
- Transaction categorisation overlay on statement pages
- Fraud alert notifications while browsing financial sites
- Auto-fill for payment forms with saved card selection

### Legal annotation
- Highlight and annotate clauses in online contracts
- Cross-reference legal terms across multiple tabs
- Sidebar with case law citations for selected text
- Export annotated documents to starter-docs

### Productivity
- Web clipper for saving pages and highlights to a knowledge base
- Time tracking overlay for project management sites
- Tab grouping and session management
- Quick-capture popup for notes and tasks

### E-commerce
- Price comparison overlay on product pages
- Price history charts and drop alerts
- Coupon/discount code auto-apply
- Wishlist aggregation across multiple retailers

### SaaS widgets
- Customer support widget injection into client sites
- Analytics dashboard overlay on any webpage
- A/B test preview and variant switching
- Feature flag toggle panel for developers
