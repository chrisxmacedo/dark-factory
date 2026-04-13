# CLAUDE.md -- {PROJECT_NAME}-extension

This file covers coding conventions for this browser extension. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack

- **Language:** TypeScript 5.3+ (strict mode)
- **Manifest:** v3 (Chrome primary, Firefox via webextension-polyfill)
- **UI:** React 18+ for popup and sidebar, Tailwind CSS for styling
- **Build:** Vite with CRXJS or custom Vite plugin for extension bundling
- **Storage:** chrome.storage.local / chrome.storage.sync for persistent data
- **Auth:** chrome.identity for OAuth flows, token stored in chrome.storage
- **Messaging:** Typed message passing between service worker, content scripts, and popup
- **Testing:** Vitest for unit tests, Puppeteer for E2E extension testing
- **CI:** GitHub Actions, Chrome Web Store API for automated publishing
- **Compatibility:** webextension-polyfill for Firefox support

---

## Project structure (planned)

```
{project-name}/
├── src/
│   ├── background/
│   │   ├── index.ts               # Service worker entry point
│   │   ├── handlers/              # Message handlers by type
│   │   │   └── {feature}.ts
│   │   └── alarms.ts              # chrome.alarms for periodic tasks
│   ├── content/
│   │   ├── index.ts               # Content script entry point
│   │   ├── inject.ts              # DOM manipulation utilities
│   │   └── overlay/               # Injected UI components (shadow DOM)
│   ├── popup/
│   │   ├── index.html             # Popup HTML shell
│   │   ├── main.tsx               # React entry point
│   │   ├── App.tsx                # Root popup component
│   │   └── components/            # Popup-specific React components
│   ├── sidebar/                   # (optional) Side panel UI
│   │   ├── index.html
│   │   ├── main.tsx
│   │   └── App.tsx
│   ├── shared/
│   │   ├── messaging/
│   │   │   ├── types.ts           # Message type definitions (discriminated union)
│   │   │   ├── send.ts            # Type-safe sendMessage wrappers
│   │   │   └── handlers.ts        # Message handler registration
│   │   ├── storage/
│   │   │   ├── types.ts           # Storage schema types
│   │   │   └── store.ts           # Type-safe chrome.storage wrapper
│   │   ├── api/
│   │   │   ├── client.ts          # HTTP client with auth headers
│   │   │   └── endpoints.ts       # Typed API endpoint definitions
│   │   └── auth/
│   │       └── identity.ts        # chrome.identity OAuth wrapper
│   └── lib/
│       └── utils.ts               # Shared utilities
├── tests/
│   ├── unit/                      # Vitest unit tests
│   └── e2e/                       # Puppeteer E2E tests
├── public/
│   └── icons/                     # Extension icons (16, 32, 48, 128)
├── manifest.json                  # Manifest v3 definition
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.ts
```

---

## Conventions

### General
- TypeScript strict mode enabled, no `any` types
- All public functions must have JSDoc comments
- No `console.log()` in production code -- use a logging utility that respects a debug flag
- Never hardcode secrets, API keys, or URLs -- read from chrome.storage or environment
- Never commit signing keys or API credentials

### Manifest v3
- Minimal permissions -- only request what the extension actually uses
- Use `activeTab` instead of broad host permissions where possible
- Service worker is ephemeral -- never assume persistent state in background
- Use chrome.alarms for periodic tasks, not setInterval
- Declare content_scripts with narrow match patterns

### Service worker (background)
- Stateless design -- persist everything to chrome.storage
- Register all message listeners at top level (before any async work)
- Use chrome.alarms for scheduled work (minimum 1 minute interval)
- Handle chrome.runtime.onInstalled for first-run setup and migrations
- Graceful handling of service worker wake-up and shutdown

### Content scripts
- Isolate injected UI in Shadow DOM to prevent style conflicts
- Minimise DOM queries -- cache references, use MutationObserver sparingly
- Never modify page behaviour in ways the user did not request
- Clean up all injected elements and listeners on extension disable/uninstall
- Use `chrome.runtime.sendMessage` for background communication, never direct API calls

### Popup / sidebar UI
- React components should be small and composable -- extract at ~50 lines
- Load data from chrome.storage first, refresh from API in background
- Handle the popup closing mid-operation gracefully (save state to storage)
- Keep popup lightweight -- heavy processing belongs in the service worker
- Support keyboard navigation and screen reader accessibility

### Messaging
- Define all message types as a TypeScript discriminated union
- Every message has a `type` field used for routing
- Type-safe send/receive wrappers -- no raw `chrome.runtime.sendMessage`
- Content script to background: `chrome.runtime.sendMessage`
- Background to content script: `chrome.tabs.sendMessage` with tab ID
- Popup to background: `chrome.runtime.sendMessage`

### Storage
- Define a typed schema for all chrome.storage keys
- Use a typed wrapper -- never access chrome.storage.local.get/set directly
- Use chrome.storage.sync for small user preferences (max 8KB per item)
- Use chrome.storage.local for larger data (max 10MB total)
- Handle storage quota errors gracefully

### Authentication
- Use chrome.identity.launchWebAuthFlow for OAuth
- Store tokens in chrome.storage.local (encrypted at rest by Chrome)
- Implement token refresh in the service worker
- Clear stored tokens on user sign-out
- Handle token expiry across all extension contexts

### Security
- Content Security Policy in manifest -- no inline scripts, no eval
- Sanitise all data injected into page DOM (prevent XSS)
- Validate all messages received in each context (type-check before processing)
- Never execute code from external sources
- HTTPS only for all API communication

### Testing
- Vitest for messaging logic, storage wrappers, and utility functions
- Mock chrome API using a test helper (chrome.storage, chrome.runtime, etc.)
- Puppeteer with `--load-extension` flag for E2E extension testing
- E2E tests cover: install, popup interaction, content script injection, messaging
- Tests must not depend on each other or on execution order

---

## Common commands (planned)

```bash
# Development (hot-reload extension build)
npx vite build --watch

# Build for production
npx vite build

# Unit tests
npx vitest run

# E2E tests (requires Chrome)
npx jest --config jest.e2e.config.ts

# Lint
npx eslint src/ --ext .ts,.tsx
npx prettier --check src/

# Package for Chrome Web Store
cd dist && zip -r ../extension.zip .
```

---

## CI/CD approach

- **GitHub Actions** for PR checks (build, test, lint)
- Build produces a dist/ folder loadable as an unpacked extension
- Release builds create a signed .zip for Chrome Web Store submission
- **Chrome Web Store API** for automated publishing on tag push
- **Firefox Add-ons** -- separate build target with webextension-polyfill, submitted via AMO API
- Extension version sourced from package.json, auto-incremented in CI

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npx eslint src/ --ext .ts,.tsx && npx prettier --check src/ && npx vitest run
```
