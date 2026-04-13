# CLAUDE.md — {project-name}-notification

This file covers coding conventions for this notification service. For
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
├── index.ts                # Entry point: init OTel, start health server,
│                           #   start notification consumer, register shutdown handlers
├── health.ts               # HTTP health endpoint at /healthz
├── channels/
│   ├── email.ts            # Email delivery via Resend/SES with retry + circuit breaker
│   ├── sms.ts              # SMS delivery via Twilio with retry + circuit breaker
│   ├── push.ts             # Push notification via FCM/APNS with retry + circuit breaker
│   └── in-app.ts           # In-app notification (DB write + optional WebSocket push)
├── templates/
│   └── (handlebars files)  # .hbs template files loaded at startup
├── lib/
│   ├── prisma.ts           # Prisma client singleton with lazy connect
│   ├── redis.ts            # ioredis singleton with retry strategy
│   ├── logger.ts           # Pino logger + createJobLogger(jobId, userId?)
│   ├── retry.ts            # withRetry(fn, maxAttempts, backoff) utility
│   ├── circuit-breaker.ts  # Circuit breaker (closed/open/half-open)
│   ├── otel.ts             # OpenTelemetry initialisation (imported first)
│   ├── preferences.ts      # User preference resolution (channels, quiet hours, frequency caps)
│   ├── templates.ts        # Template loading and Handlebars rendering
│   └── delivery-tracker.ts # Track delivery status per notification per channel
└── api/
    └── (preference endpoint files)  # Optional HTTP API for user preference management
```

---

## Conventions

### General
- All functions must have full type annotations
- TypeScript strict mode — no `any`, no implicit returns
- Never use `console.log` — use the Pino logger from `src/lib/logger.ts`
- Never hardcode secrets or URLs — read from environment variables
- Never commit `.env` — use `.env.example` as the reference

### Channel modules (src/channels/)
- One file per delivery channel
- Every channel module exports `send(notification, channelConfig)` and
  `getStatus(externalId)` functions
- All provider calls MUST use `withRetry()` from `src/lib/retry.ts`
- Each channel has its own circuit breaker instance
- Channels return a standardised `DeliveryResult` type:
  `{ externalId, status: 'sent' | 'failed', errorMessage? }`

### No business logic
- This service receives "send notification" events and delivers them
- It does NOT decide when to send notifications — that is the
  responsibility of the producing service
- The only logic here: preference resolution, template rendering,
  delivery, tracking, retry

### Template rendering (src/lib/templates.ts)
- Templates are Handlebars `.hbs` files in `src/templates/`
- Templates are loaded once at startup and cached in memory
- Variable substitution uses the notification payload's `data` field
- Every template must have a plain-text fallback (no HTML-only templates)

### User preferences (src/lib/preferences.ts)
- Preferences are stored per user in the database
- Resolution checks: channel opt-in, quiet hours (timezone-aware),
  frequency caps (max N notifications per channel per time window)
- If all channels are suppressed, log and track as "suppressed" — do not
  silently drop

### Delivery tracking (src/lib/delivery-tracker.ts)
- Every send attempt is recorded: notification ID, channel, status,
  timestamp, external provider ID, error message
- Statuses: `pending`, `sent`, `delivered`, `failed`, `bounced`, `suppressed`
- Webhook callbacks from providers (Resend, Twilio) update status asynchronously

### Idempotency
- Every notification has a unique `notificationId`
- Before processing, check if this ID has already been handled
- Duplicate requests are logged and skipped — never double-deliver

### Per-channel retry
- Each channel retries independently — email failure does not block SMS
- Retry configuration is per-channel (email may retry 3x, SMS 2x)
- After max retries, mark as `failed` in the delivery tracker
- Never retry in-app notifications — they are local writes

### Logging
- Use structured logging with Pino
- Every log line inside a notification handler must include
  `notificationId` and `userId` — use `createJobLogger()` for this
- Log at these levels:
  - `info` — notification received, channel delivery sent, delivery confirmed
  - `warn` — retry attempt, preference suppression, circuit breaker state change
  - `error` — delivery failed permanently, provider error

### Graceful shutdown
- On SIGTERM/SIGINT: stop accepting new notifications, finish current
  delivery, close DB and Redis connections, then exit
- Shutdown timeout: if current delivery does not finish within N seconds,
  force exit with a non-zero code
- The health endpoint must return unhealthy during shutdown

### Health endpoint
- Serve `/healthz` on a configurable port (default 8080)
- Check: database connectivity, Redis connectivity, channel provider
  connectivity (circuit breaker states)
- Return 200 with `{"status": "ok"}` when all checks pass
- Return 503 with `{"status": "unhealthy", "checks": {...}}` on failure

### Observability
- Initialise OpenTelemetry BEFORE any other imports in `src/index.ts`
- Traces should span from producer to consumer (propagate trace context
  through notification payloads)
- Add span attributes: `notification.id`, `notification.type`,
  `notification.channel`, `notification.user_id`

### Testing
- Every channel needs at least one test for the happy path and one for
  retry/failure behaviour
- Mock all external providers — never call real APIs in tests
- Test preference resolution: quiet hours, frequency caps, channel opt-out
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
