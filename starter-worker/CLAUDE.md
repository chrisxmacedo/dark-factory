# CLAUDE.md — {project-name}-worker

This file covers coding conventions for this worker service. For project-wide
architecture, service providers, and secrets, see `../CLAUDE.md` and
`../.secrets.md` in the parent project directory.

---

## Stack

- **Node.js 22**, TypeScript (strict), Prisma, ioredis, Pino
- **Package manager:** npm
- **Linting/formatting:** eslint + prettier
- **Type checking:** tsc --noEmit
- **Testing:** Jest + ts-jest

---

## Project structure

```
src/
├── index.ts              # Entry point: init OTel, start health server,
│                         #   start consumers, register shutdown handlers
├── health.ts             # HTTP health endpoint at /healthz
├── lib/
│   ├── prisma.ts         # Prisma client singleton with lazy connect
│   ├── redis.ts          # ioredis singleton with retry strategy
│   ├── logger.ts         # Pino logger + createJobLogger(jobId, userId?)
│   ├── retry.ts          # withRetry(fn, maxAttempts, backoff) utility
│   └── circuit-breaker.ts # Circuit breaker (closed/open/half-open)
├── workers/              # Job handler functions (one file per job type)
│   └── example-worker.ts # Skeleton: idempotency check, process, mark done
└── consumers/            # Queue/topic consumer loops
    └── (consumer files)
```

---

## Conventions

### General
- All functions must have full type annotations
- TypeScript strict mode — no `any`, no implicit returns
- Never use `console.log` — use the Pino logger from `src/lib/logger.ts`
- Never hardcode secrets or URLs — read from environment variables
- Never commit `.env` — use `.env.example` as the reference

### Job handlers (src/workers/)
- One file per job type in `src/workers/`
- Every handler MUST be idempotent — safe to run multiple times with the
  same input. Check for existing results before processing.
- Handlers receive a typed payload and return a typed result
- Handlers must not manage their own queue consumption — that belongs in
  `src/consumers/`

### External API calls
- All outbound HTTP/API calls MUST use `withRetry()` from `src/lib/retry.ts`
- Wrap unreliable external services with the circuit breaker from
  `src/lib/circuit-breaker.ts`
- Never call external APIs without a timeout

### Error handling and dead-letter queue
- Failed jobs are retried up to N times (configurable per worker)
- After max retries, the job is moved to a dead-letter queue (DLQ)
- DLQ entries include: original payload, error message, attempt count, timestamps
- Never silently swallow errors — log at error level with full context

### Logging
- Use structured logging with Pino
- Every log line inside a job handler must include `jobId` and `userId`
  (when available) — use `createJobLogger()` for this
- Log at these levels:
  - `info` — job started, job completed, consumer connected
  - `warn` — retry attempt, circuit breaker state change
  - `error` — job failed permanently, DLQ'd, connection lost

### Graceful shutdown
- On SIGTERM/SIGINT: stop accepting new jobs, finish the current job,
  close DB and Redis connections, then exit
- Shutdown timeout: if current job does not finish within N seconds,
  force exit with a non-zero code
- The health endpoint must return unhealthy during shutdown

### Health endpoint
- Serve `/healthz` on a configurable port (default 8080)
- Check: database connectivity, Redis connectivity, consumer status
- Return 200 with `{"status": "ok"}` when all checks pass
- Return 503 with `{"status": "unhealthy", "checks": {...}}` on failure

### Observability
- Initialise OpenTelemetry BEFORE any other imports in `src/index.ts`
- Traces should span from producer to consumer (propagate trace context
  through job payloads)
- Add span attributes: `job.type`, `job.id`, `job.user_id`

### Testing
- Every worker needs at least one test for the happy path and one for
  idempotency (running the same job twice produces the same result)
- Mock external services — never call real APIs in tests
- Tests must not depend on each other or on execution order

---

## Common commands

```bash
npm install                    # Install dependencies
npm run dev                    # Start with tsx watch (hot reload)
npm run build                  # Compile TypeScript
npm start                      # Run compiled output
npm test                       # Run tests
npm run lint                   # Lint
npm run format                 # Format
npx tsc --noEmit               # Type check
npx prisma generate            # Regenerate Prisma client
npx prisma db push             # Push schema to database
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
npx tsc --noEmit && npm run lint && npm test
```
