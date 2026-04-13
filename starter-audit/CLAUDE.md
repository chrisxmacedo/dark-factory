# CLAUDE.md -- {project-name}-audit

This file covers coding conventions for this audit log service. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

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
│                         #   start event consumer + query API, register
│                         #   shutdown handlers
├── health.ts             # HTTP health endpoint at /healthz
├── ingest/
│   ├── consumer.ts       # Consume audit events from queue, validate,
│   │                     #   compute hash chain, store
│   ├── schema.ts         # Zod schema for audit event validation
│   └── hash-chain.ts     # Compute event hash including previous event hash
├── query/
│   ├── search.ts         # Query API: filter by actor/action/resource/time,
│   │                     #   paginated results
│   └── export.ts         # Export filtered events as CSV or JSON
├── retention/
│   └── policy.ts         # Retention policy definitions per event type
└── lib/
    ├── prisma.ts         # Prisma client singleton with lazy connect
    ├── redis.ts          # ioredis singleton with retry strategy
    ├── logger.ts         # Pino logger + createEventLogger(eventId?)
    └── otel.ts           # OpenTelemetry initialisation
```

---

## Conventions

### Core invariant: APPEND ONLY

**No UPDATE, no DELETE on audit events. Ever.** This is the single most
important rule in this service. Every function, every query, every migration
must preserve this invariant. If you find yourself writing an UPDATE or
DELETE statement against the audit event table, stop -- you are violating
the fundamental contract of this service.

- INSERT is the only write operation permitted on the audit event table
- Retention enforcement (archival/purge of expired events) runs as a
  separate batch job via starter-batch, not within this service
- Soft deletes are not a workaround -- there are no deletes of any kind

### Event schema

Every audit event has this structure:

```typescript
{
  id: string;           // ULID or UUID, globally unique
  timestamp: Date;      // When the event occurred (source time)
  actor: string;        // Who performed the action (user ID, service name)
  action: string;       // What was done (e.g. "user.login", "record.view")
  resource: string;     // What was acted upon (e.g. "document:abc-123")
  context: string;      // From where (IP address, service name, session ID)
  outcome: string;      // "success" or "failure"
  metadata: object;     // Additional structured data (free-form JSON)
  previousHash: string; // Hash of the previous event (hash chain)
  hash: string;         // Hash of this event (including previousHash)
}
```

Validate all incoming events with the Zod schema in `src/ingest/schema.ts`.
Reject malformed events -- do not coerce or fill in defaults for required
fields.

### Tamper detection: hash chain

Each event includes a SHA-256 hash of the previous event. This creates an
unbroken chain -- if any event in the log is modified after the fact, the
hash chain breaks and the tampering is detectable.

- `src/ingest/hash-chain.ts` computes the hash for each new event
- The first event in the chain uses a well-known genesis hash
- Hash computation is deterministic: same inputs always produce the same hash
- Hash chain verification should be possible as a batch job (not on every read)

### Retention policies

Defined in `src/retention/policy.ts`. Each event type maps to a retention
duration (e.g. `"financial.transaction": "7y"`, `"access.login": "1y"`).

- This service does NOT enforce retention itself -- it only defines the policies
- Enforcement (archival to cold storage, eventual purge) is handled by
  starter-batch as a scheduled job
- Default retention for uncategorised events: configurable via environment variable

### Query API

`src/query/search.ts` provides filtered, paginated queries over audit events.

- Filter by: actor, action, resource, time range (from/to), outcome
- Pagination is cursor-based (not offset-based) -- use the event ID as cursor
- Maximum page size is configurable (default 100, max 1000)
- Results are ordered by timestamp descending (most recent first)
- Never return unbounded result sets

### Export

`src/query/export.ts` produces CSV or JSON exports of filtered event sets.

- Uses the same filter parameters as the query API
- Streams results to avoid loading entire data sets into memory
- CSV export includes a header row matching the event schema fields
- JSON export produces a JSON array (or newline-delimited JSON for large sets)
- Intended for regulatory and compliance requests

### General

- All functions must have full type annotations
- TypeScript strict mode -- no `any`, no implicit returns
- Never use `console.log` -- use the Pino logger from `src/lib/logger.ts`
- Never hardcode secrets or URLs -- read from environment variables
- Never commit `.env` -- use `.env.example` as the reference

### Logging

- Use structured logging with Pino
- Every log line inside event processing must include `eventId` when available
- Use `createEventLogger()` for contextual child loggers
- Log at these levels:
  - `info` -- event ingested, query served, export started/completed
  - `warn` -- malformed event rejected, hash chain gap detected
  - `error` -- storage failure, consumer connection lost, export failed

### Graceful shutdown

- On SIGTERM/SIGINT: stop accepting new events, finish processing current
  event, close DB and Redis connections, then exit
- Shutdown timeout: if current processing does not finish within N seconds,
  force exit with a non-zero code
- The health endpoint must return unhealthy during shutdown

### Health endpoint

- Serve `/healthz` on a configurable port (default 8080)
- Check: database connectivity, Redis connectivity, consumer status
- Return 200 with `{"status": "ok"}` when all checks pass
- Return 503 with `{"status": "unhealthy", "checks": {...}}` on failure

### Observability

- Initialise OpenTelemetry BEFORE any other imports in `src/index.ts`
- Add span attributes: `event.id`, `event.action`, `event.actor`
- Traces should span from producer to consumer (propagate trace context
  through event payloads)

### Testing

- Every ingest path needs tests: valid event, malformed event, hash chain
  continuity
- Query tests: filter combinations, pagination, empty results
- Export tests: CSV format correctness, JSON format correctness
- Mock external services -- never call real APIs in tests
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
