# CLAUDE.md -- {PROJECT_NAME}-desktop

This file covers coding conventions for this desktop application. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack

- **Framework:** Tauri 2.x (Rust backend, web frontend) -- Electron only if Tauri cannot meet a hard requirement
- **Frontend:** React 18+, TypeScript 5.3+, Vite
- **Styling:** Tailwind CSS (consistent with starter-web)
- **State management:** Zustand for global state, React Query for server state
- **Networking:** fetch API via Tauri HTTP plugin, retry with exponential backoff
- **Auth:** OS keychain via Tauri keychain plugin, OAuth device flow
- **Persistence:** SQLite via Tauri SQL plugin for local data
- **Logging:** Tauri log plugin (Rust side), structured JSON logs (frontend)
- **Observability:** OpenTelemetry JS SDK for frontend traces, Rust tracing crate for backend
- **Testing:** Vitest for unit tests, WebdriverIO for E2E
- **CI:** GitHub Actions with matrix builds (macOS, Windows, Linux)
- **Distribution:** Auto-update with signature verification, platform-specific installers

---

## Project structure (planned)

```
{project-name}/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs                # Tauri entry point, plugin registration
│   │   ├── commands/              # Tauri IPC command handlers
│   │   │   ├── mod.rs
│   │   │   └── {feature}.rs       # Feature-specific commands
│   │   ├── state.rs               # Managed state (DB pool, config)
│   │   └── db.rs                  # SQLite migrations and queries
│   ├── Cargo.toml
│   ├── tauri.conf.json            # Tauri configuration (window, permissions, updater)
│   └── icons/                     # Platform-specific app icons
├── src/
│   ├── App.tsx                    # Root React component
│   ├── main.tsx                   # React entry point
│   ├── features/
│   │   └── {feature}/
│   │       ├── components/        # React components
│   │       ├── hooks/             # Feature-specific hooks
│   │       └── types.ts           # Feature types
│   ├── core/
│   │   ├── api/
│   │   │   ├── client.ts          # HTTP client with auth and retry
│   │   │   └── endpoints.ts       # Typed API endpoint definitions
│   │   ├── store/
│   │   │   └── index.ts           # Zustand store definitions
│   │   ├── ipc/
│   │   │   └── commands.ts        # Type-safe Tauri invoke wrappers
│   │   └── hooks/
│   │       └── useAuth.ts         # Auth state and token management
│   └── lib/
│       └── utils.ts               # Shared utilities
├── tests/
│   ├── unit/                      # Vitest unit tests
│   └── e2e/                       # WebdriverIO E2E tests
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.ts
```

---

## Conventions

### General
- TypeScript strict mode enabled, no `any` types
- Rust code follows `cargo clippy` recommendations with `#![deny(clippy::all)]`
- All public APIs (Rust commands, TypeScript functions) must have documentation
- No `console.log()` in production code -- use the logging utility
- Never hardcode secrets, API keys, or URLs -- read from Tauri config or environment
- Never commit signing certificates or keys

### Tauri / Rust backend
- Use Tauri's command system for all frontend-to-backend IPC
- Commands must be async where possible -- never block the main thread
- Use `tauri::State<>` for managed state (DB connections, config)
- Minimise Tauri permissions -- only request what the app needs
- Use Rust's `thiserror` for typed errors returned to the frontend

### React frontend
- Components should be small and composable -- extract at ~50 lines
- Use React Query for all server data fetching (caching, refetching, optimistic updates)
- Use Zustand for UI state that does not come from the server
- Prefer composition over prop drilling -- use context sparingly
- Support keyboard navigation and screen reader accessibility

### Networking
- All HTTP requests go through the typed API client -- never use fetch directly
- Use Tauri's HTTP plugin (not browser fetch) for CORS-free requests
- Implement retry with exponential backoff for transient failures (5xx, timeout)
- Handle offline gracefully -- read from local SQLite, queue writes for sync

### Authentication
- Store tokens in the OS keychain via Tauri keychain plugin
- Use OAuth device flow for desktop authentication
- Implement token refresh transparently in the API client
- Clear keychain entries on logout

### Persistence
- Use SQLite for structured local data (via Tauri SQL plugin)
- Run migrations on app startup -- schema versioning via migration files
- Design for offline-first: read from SQLite, sync with server
- Never block the UI thread with database operations

### Logging
- Rust: use `tracing` crate with structured spans and fields
- Frontend: use Tauri log plugin to route logs through Rust logging pipeline
- Log levels: `debug` for development, `info` for business events,
  `error` for failures
- Include correlation IDs from API responses in log entries
- Never log sensitive data (tokens, passwords, PII)

### Observability
- Initialise OTel SDK on app startup (both Rust and JS sides)
- Create spans for IPC calls, network requests, and key user flows
- Propagate trace context in HTTP headers to backend services
- Add span attributes: `user.id`, `feature.name`, `api.endpoint`

### Security
- Tauri allowlist must be minimal -- only permit required APIs and paths
- Code signing required for all release builds (macOS notarisation, Windows Authenticode)
- Auto-update must verify signatures before applying updates
- No secrets in source, config files, or bundled resources
- Content Security Policy (CSP) configured in tauri.conf.json

### Testing
- Vitest for all React component and utility unit tests
- Rust unit tests (`#[cfg(test)]`) for backend commands and logic
- WebdriverIO for critical E2E flows (login, main feature, error states, update)
- Tests must not depend on each other or on execution order
- Use test fixtures and mock IPC responses for consistent test data

---

## Common commands (planned)

```bash
# Development (starts both Rust backend and Vite dev server)
cargo tauri dev

# Build release binary
cargo tauri build

# Frontend unit tests
npx vitest run

# Rust tests
cd src-tauri && cargo test

# E2E tests
npx wdio run wdio.conf.ts

# Lint (frontend)
npx eslint src/ --ext .ts,.tsx
npx prettier --check src/

# Lint (Rust)
cd src-tauri && cargo clippy -- -D warnings
```

---

## CI/CD approach

- **GitHub Actions** with matrix strategy: `[macos-latest, windows-latest, ubuntu-latest]`
- PR checks: build, test (unit + E2E), lint on all three platforms
- Release builds triggered on tag push -- produces signed installers per platform
- **macOS:** .dmg with notarisation via `xcrun notarytool`
- **Windows:** .msi / .exe with Authenticode signing
- **Linux:** .deb, .rpm, .AppImage
- Auto-update server (Tauri updater endpoint or GitHub Releases with JSON manifest)

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npx eslint src/ --ext .ts,.tsx && npx prettier --check src/ && npx vitest run && cd src-tauri && cargo clippy -- -D warnings && cargo test
```
