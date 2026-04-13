# CLAUDE.md — {PROJECT_NAME}-gateway

This file covers coding conventions for this gateway service. For
project-wide architecture, service providers, and secrets, see
`../CLAUDE.md` and `../.secrets.md` in the parent project directory.

---

## Stack

- **Node.js 20**, Express, TypeScript (strict mode)
- **Package manager:** npm
- **Linting/formatting:** eslint + prettier
- **Type checking:** tsc --noEmit
- **Testing:** jest + supertest
- **Observability:** pino (structured logging), OpenTelemetry (tracing)

---

## Project structure

```
src/
├── app.ts                # Express app factory, middleware chain, router mount
├── server.ts             # Server entrypoint (listen, graceful shutdown)
├── config.ts             # Environment config (reads .env, validates at startup)
├── routes/
│   └── v1/
│       ├── index.ts      # v1 router — mounts all v1 sub-routers
│       └── health.ts     # Health endpoint aggregating downstream checks
├── middleware/
│   ├── auth.ts           # JWT validation, session check
│   ├── rate-limit.ts     # Redis-backed per-user/IP rate limiter
│   ├── correlation.ts    # x-request-id injection + propagation
│   ├── logging.ts        # Request/response structured logging
│   └── error-handler.ts  # Centralised error response formatting
├── clients/
│   └── base-client.ts    # HTTP client with retry, circuit breaker, correlation ID
├── lib/
│   ├── logger.ts         # Pino structured logger singleton
│   └── redis.ts          # Singleton Redis client
└── types/
    └── index.ts          # Shared type definitions

tests/
├── setup.ts              # Jest global setup
├── middleware/            # Middleware unit tests
├── routes/               # Route integration tests (supertest)
└── clients/              # Client unit tests with nock
```

---

## Conventions

### General
- TypeScript strict mode — no `any`, no implicit returns, no unchecked index access
- All functions must have explicit return types
- Never use `console.log` — use `logger` from `src/lib/logger.ts`
- Never hardcode secrets or URLs — read from `src/config.ts`
- Never commit `.env` — use `.env.example` as the reference

### Gateway rules
- **No business logic.** The gateway routes requests, validates auth, enforces
  rate limits, and aggregates responses. Domain logic belongs in internal services.
- **No database access.** The gateway talks to Redis (cache, rate limits) and
  internal services only. If you need a database, that is a service, not a gateway.
- **No data transformation beyond aggregation.** Reshaping multiple service
  responses into one client response is fine. Computing derived values is not.

### Routes
- All routes are versioned: `/v1/...`, `/v2/...`
- Each version gets its own directory under `src/routes/`
- New versions copy from the previous version and modify — never change
  existing version routes after clients depend on them
- Route handlers are thin: validate input, call internal services via clients,
  assemble response
- Always return structured JSON with consistent envelope:
  ```json
  { "data": ..., "meta": { "request_id": "..." } }
  ```

### Middleware chain order
1. `correlation` — inject/propagate x-request-id (must be first)
2. `logging` — log request start (needs correlation ID)
3. `rate-limit` — reject before auth to save compute
4. `auth` — validate JWT/session
5. Route handlers
6. `error-handler` — catch-all error formatting (must be last)

### Auth
- Auth middleware validates JWT tokens before requests reach internal services
- The gateway forwards the validated user context (not the raw token) to
  internal services via headers
- Public endpoints must be explicitly marked in the route definition
- Never trust client-supplied user IDs — always extract from the validated token

### Internal service clients
- All internal HTTP calls go through `base-client.ts`
- The base client provides: retry with exponential backoff, circuit breaker,
  correlation ID forwarding, request/response logging, timeout enforcement
- Create one client instance per internal service, configured in `src/clients/`
- Circuit breaker thresholds: 5 failures in 30s opens the circuit for 60s

### Rate limiting
- Redis-backed sliding window per user ID (authenticated) or IP (unauthenticated)
- Default limits: 100 requests/minute per user, 20 requests/minute per IP
- Rate limit headers in every response: `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Override limits per route where needed

### Logging and tracing
- Structured JSON logs via pino — every log line includes `request_id`
- Request/response logging: method, path, status, duration, user_id
- OpenTelemetry traces span from gateway entry to internal service calls
- Correlation ID (`x-request-id`) propagated to all downstream services

### Health endpoint
- `GET /v1/health` checks all downstream services and returns aggregate status
- Response includes per-service status, latency, and overall health
- Returns 200 if all services healthy, 503 if any critical service is down
- Used by load balancers and monitoring

### Error handling
- Centralised error handler middleware catches all unhandled errors
- Internal service errors are translated to client-appropriate status codes
- Never leak internal service URLs, stack traces, or implementation details
- Standard error shape:
  ```json
  { "error": { "code": "rate_limited", "message": "Too many requests" } }
  ```

---

## Common commands

```bash
npm install                    # Install dependencies
npm run dev                    # Start dev server with hot reload
npm run build                  # Compile TypeScript
npm start                      # Start production server
npm test                       # Run tests
npm run lint                   # Lint
npm run format                 # Format
npm run typecheck              # Type check without emitting
```

---

## Before writing code

- Read existing files in the area being modified before generating any code
- If modifying an existing module, read the current implementation first
- Verify you are in the correct repo: `pwd && git remote get-url origin`

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npm run lint && npm run typecheck && npm test
```

---

## PRD and PLAN

If `PRD.md` and `PLAN.md` exist in the repo root, read them before starting
any ticket. They are the source of truth for what this gateway does, which
internal services it fronts, and how routes map to downstream calls.
