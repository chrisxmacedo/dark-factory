# CLAUDE.md -- {PROJECT_NAME}-serverless

This file covers coding conventions for this serverless service. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack (Lambda variant)

- **Node.js 20**, TypeScript (strict)
- **Framework:** SST v3 (Ion) or AWS SAM
- **Middleware:** middy (input validation, error handling, warmup)
- **AWS SDK:** v3 (modular imports only -- never import all of @aws-sdk)
- **Secrets:** AWS Secrets Manager (cached via middy middleware)
- **Logging:** Powertools for AWS Lambda (structured JSON)
- **Observability:** OTel Lambda layer + Powertools tracer
- **Testing:** Jest + aws-sdk-client-mock
- **Local dev:** SAM local invoke / SST dev

## Stack (Workers variant)

- **V8 isolate**, TypeScript
- **Framework:** Hono (lightweight, Workers-native)
- **Storage:** Workers KV (key-value), D1 (SQLite), R2 (objects)
- **Secrets:** Wrangler secrets (encrypted at rest)
- **Logging:** console (Workers runtime captures structured logs)
- **Testing:** Vitest + miniflare
- **Local dev:** Wrangler dev

---

## Project structure (planned)

### Lambda (SST)

```
sst.config.ts                  # SST stack definition (functions, events, permissions)
src/
├── functions/                 # One file per Lambda function
│   ├── webhook-stripe.ts      # Example: Stripe webhook handler
│   ├── process-image.ts       # Example: S3 trigger image processor
│   └── scheduled-cleanup.ts   # Example: EventBridge scheduled task
├── lib/
│   ├── secrets.ts             # Secrets Manager client with caching
│   ├── validation.ts          # Zod schemas for event payloads
│   ├── responses.ts           # Standard API Gateway response helpers
│   └── idempotency.ts         # DynamoDB-backed idempotency check
└── __tests__/
    └── functions/             # Per-function test files
```

### Workers (Hono)

```
wrangler.toml                  # Workers config (routes, KV bindings, cron triggers)
src/
├── index.ts                   # Hono app entry, route registration
├── routes/                    # Route handlers
│   ├── webhook.ts             # Webhook receiver
│   └── api.ts                 # Lightweight API endpoints
├── scheduled/                 # Cron trigger handlers
│   └── cleanup.ts
├── lib/
│   ├── validation.ts          # Zod schemas
│   └── kv.ts                  # KV/D1 helpers
└── __tests__/
    └── routes/
```

---

## Conventions

### General
- All functions must have full type annotations
- TypeScript strict mode -- no `any`, no implicit returns
- Never hardcode secrets or URLs -- use Secrets Manager (Lambda) or Wrangler secrets (Workers)
- Never commit `.env` -- use `.env.example` as the reference
- Keep dependencies minimal -- every extra dependency increases cold start time

### Cold start optimisation
- Import only what you need (`import { S3Client } from '@aws-sdk/client-s3'`, never `import AWS from 'aws-sdk'`)
- Initialise clients outside the handler (module scope) so they persist across warm invocations
- Use lazy initialisation for expensive resources (DB connections, secret fetches)
- Prefer lightweight alternatives (Hono over Express, zod over joi)
- Bundle with esbuild -- tree-shake aggressively

### Stateless design
- No in-memory state between invocations -- every invocation starts fresh
- Store state in DynamoDB, KV, D1, or Redis -- never in local variables
- Idempotency keys for any operation that has side effects (payments, writes)
- Assume the function may run concurrently with itself

### Runtime limits
- **Lambda:** 15 min max, 10 GB memory, 512 MB /tmp, 6 MB payload (API Gateway)
- **Workers:** 30s CPU time, 128 MB memory, 30s wall clock (paid plan)
- **Edge:** 30s execution, limited APIs (no Node.js built-ins)
- Design for fast execution -- offload heavy work to queues or workers

### Event handling
- Validate every incoming event/payload with Zod before processing
- Webhook handlers must verify signatures (Stripe: stripe-signature, GitHub: X-Hub-Signature-256)
- Return 200/202 quickly, process asynchronously if the work is heavy
- Log the event type and a correlation ID on every invocation

### Error handling
- Return appropriate HTTP status codes (400 for bad input, 500 for internal errors)
- Never expose internal error details to callers
- Use structured error responses: `{ "error": "...", "code": "...", "requestId": "..." }`
- Lambda: let unhandled errors propagate to trigger retry (for async invocations)
- Workers: catch all errors and return a clean response (no retry mechanism)

### Secrets management
- **Lambda:** AWS Secrets Manager with caching (middy secrets-manager middleware)
  -- secrets are fetched once per cold start and cached in memory
- **Workers:** Wrangler secrets (`wrangler secret put KEY`) bound as env vars
- Never log secret values, even at debug level
- Rotate secrets without redeploying -- use dynamic fetching

### Observability
- **Lambda:** Enable OTel Lambda layer + Powertools tracer. Every function
  invocation gets a trace with `function.name`, `event.type`, `request_id`
- **Workers:** Use `console.log` with structured JSON -- Workers runtime captures
  and forwards to configured log destinations
- Include correlation/request IDs in all log lines
- Track cold start vs warm start in metrics

### Security
- Validate webhook signatures on every request -- reject unsigned payloads
- Use least-privilege IAM roles (Lambda) or scoped bindings (Workers)
- Enable encryption at rest for all storage (DynamoDB, KV, S3)
- Set CORS headers explicitly -- never use `*` in production
- API Gateway: use request validation and throttling

### Testing
- Every function needs at least one happy-path test and one error-path test
- Mock AWS services with aws-sdk-client-mock (Lambda) or miniflare (Workers)
- Test webhook signature verification (valid and invalid signatures)
- Test idempotency (same event processed twice produces same result)
- Tests must not depend on each other or on execution order

---

## Common commands (planned)

### Lambda (SST)

```bash
npx sst dev                    # Local development with live reload
npx sst deploy --stage dev     # Deploy to dev stage
npx sst remove --stage dev     # Tear down dev stage
npm test                       # Run tests
npm run lint                   # Lint
npx tsc --noEmit               # Type check
```

### Lambda (SAM)

```bash
sam build                      # Build functions
sam local invoke FunctionName  # Invoke locally
sam deploy --guided            # Deploy with prompts
npm test                       # Run tests
```

### Workers (Wrangler)

```bash
wrangler dev                   # Local development
wrangler deploy                # Deploy to production
wrangler tail                  # Stream live logs
npm test                       # Run tests (vitest)
npm run lint                   # Lint
```

---

## CI/CD approach

- **GitHub Actions** for PR checks (build, test, lint, type check)
- **Lambda:** deploy on merge to main via SST/SAM (`sst deploy --stage prod`)
- **Workers:** deploy on merge to main via Wrangler (`wrangler deploy`)
- Separate stages/environments: dev, staging, prod
- Canary deployments where supported (Lambda aliases, Workers gradual rollout)

---

## Before opening a PR

```bash
npx tsc --noEmit && npm run lint && npm test
```
