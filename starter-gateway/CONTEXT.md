# starter-gateway/

API Gateway / Backend-for-Frontend (BFF) template. Copy this directory to create a new gateway service that sits in front of internal microservices.

## What this is

A single entry point for mobile apps and web clients. The gateway handles cross-cutting concerns (auth, rate limiting, logging, tracing) and aggregates responses from multiple internal services into client-friendly shapes. It contains no business logic.

## When to use this vs direct API

**Use starter-gateway when:**
- Multiple clients (web, mobile, third-party) need a unified API surface
- You need response aggregation — one client request fans out to multiple internal services
- Auth, rate limiting, and CORS must be enforced in one place before reaching internal services
- You want API versioning (/v1/, /v2/) decoupled from internal service versions
- Internal services use protocols or schemas that clients should not see directly

**Use starter-api (direct API) when:**
- There is only one service and one consumer
- The service IS the product API (no internal/external boundary)
- You need full CRUD with database access and business logic
- Adding a gateway would be pure overhead with no aggregation or routing benefit

## Contents

- **CLAUDE.md** — Coding conventions for gateway services
- **Dockerfile** — Multi-stage Node.js production build
- **package.json** — Dependencies and scripts
- **tsconfig.json** — TypeScript strict configuration
- **jest.config.ts** — Test configuration
- **.env.example** — Environment variable reference
- **.gitignore** — Node.js ignores
- **src/app.ts** — Express app with middleware chain
- **src/middleware/** — Auth, rate limiting, correlation ID, logging
- **src/clients/** — HTTP clients for internal services with circuit breaker
- **src/routes/v1/** — Versioned route handlers
- **src/lib/** — Shared utilities (logger, Redis)

## For agents

- Replace all `{PLACEHOLDER}` values with project-specific configuration before use.
- The gateway must never contain business logic. If you find yourself writing domain models or database queries, that belongs in an internal service.
- All internal service calls go through `base-client.ts` to get retry, circuit breaker, and correlation ID propagation for free.
- Add new API versions by creating `src/routes/v2/` directories. Never modify v1 routes to avoid breaking existing clients.
