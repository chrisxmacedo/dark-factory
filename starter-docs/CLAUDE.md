# CLAUDE.md — {project-name}-docs

This file covers coding conventions for this document generation service.
For project-wide architecture, service providers, and secrets, see
`../CLAUDE.md` and `../.secrets.md` in the parent project directory.

---

## Stack

- **Node.js 22**, TypeScript (strict), Prisma, ioredis, Pino
- **Document generation:** Puppeteer (PDF from HTML), docx (DOCX)
- **Templating:** Handlebars (HTML templates with variable substitution)
- **Storage:** AWS SDK v3 (S3/MinIO)
- **Package manager:** npm
- **Linting/formatting:** eslint + prettier
- **Type checking:** tsc --noEmit
- **Testing:** Jest + ts-jest

---

## Project structure

```
src/
├── index.ts              # Entry point: init OTel, start API server,
│                         #   optionally start queue consumer, register
│                         #   shutdown handlers
├── health.ts             # HTTP health endpoint at /healthz
│                         #   checks DB + S3 connectivity
├── generators/
│   ├── pdf.ts            # PDF generation from HTML via Puppeteer
│   └── docx.ts           # DOCX generation placeholder
├── templates/
│   └── manager.ts        # Template loading, caching, Handlebars
│                         #   compilation, variable substitution
├── storage/
│   └── s3.ts             # S3/MinIO client: upload, download,
│                         #   signed URL generation
├── api/
│   ├── generate.ts       # POST /generate — accepts template + data,
│   │                     #   produces document, stores it, returns metadata
│   └── download.ts       # GET /documents/:id — returns signed URL
│                         #   for secure time-limited download
└── lib/
    ├── prisma.ts         # Prisma client singleton with lazy connect
    ├── redis.ts          # ioredis singleton with retry strategy
    ├── logger.ts         # Pino logger + createDocLogger(docId, ownerId?)
    └── otel.ts           # OpenTelemetry SDK initialisation
```

---

## Conventions

### General
- All functions must have full type annotations
- TypeScript strict mode — no `any`, no implicit returns
- Never use `console.log` — use the Pino logger from `src/lib/logger.ts`
- Never hardcode secrets or URLs — read from environment variables
- Never commit `.env` — use `.env.example` as the reference

### Document generation
- This service has **no business logic** — it receives "generate document"
  requests with template ID + data, and produces files
- Templates live in `src/templates/` as `.hbs` files (Handlebars)
- Template variables use `{{variableName}}` syntax
- PDF generation compiles Handlebars to HTML, then renders via Puppeteer
- DOCX generation uses the `docx` library for programmatic construction
- Every generated document gets a metadata record in the database:
  `id`, `type`, `owner_id`, `template_id`, `generated_at`, `storage_key`,
  `version`, `content_type`, `size_bytes`

### Versioning
- When a document is regenerated (same owner + template + logical key),
  the version number increments
- Previous versions are retained in storage — never overwrite
- Storage keys include the version: `{owner}/{template}/{id}/v{n}.pdf`

### Bulk generation
- Bulk requests are enqueued to Redis, one job per document
- The queue consumer picks jobs and calls the same generation logic
- Bulk endpoints return a batch ID for tracking progress

### Storage
- All storage operations go through `src/storage/s3.ts`
- Upload returns the storage key; download returns a Buffer
- Signed URLs have a configurable expiry (default 15 minutes)
- `forcePathStyle: true` is required for MinIO compatibility

### API endpoints
- `POST /generate` — synchronous single-document generation
- `POST /generate/bulk` — enqueue bulk generation, return batch ID
- `GET /documents/:id` — return signed download URL
- `GET /documents/:id/metadata` — return document metadata
- `GET /healthz` — health check

### Logging
- Use structured logging with Pino
- Every log line in generation must include `docId` and `ownerId`
  (when available) — use `createDocLogger()` for this
- Log at these levels:
  - `info` — generation started, generation completed, upload complete
  - `warn` — template cache miss, retry attempt
  - `error` — generation failed, storage upload failed, S3 unreachable

### Graceful shutdown
- On SIGTERM/SIGINT: stop accepting new requests, finish in-flight
  generations, close browser instance, close DB and Redis connections
- Shutdown timeout: force exit after N seconds (configurable)
- Health endpoint returns unhealthy during shutdown

### Health endpoint
- Serve `/healthz` on the API port
- Check: database connectivity, S3 connectivity (HeadBucket)
- Return 200 with `{"status": "ok"}` when all checks pass
- Return 503 with `{"status": "unhealthy", "checks": {...}}` on failure

### Observability
- Initialise OpenTelemetry BEFORE any other imports in `src/index.ts`
- Add span attributes: `doc.type`, `doc.id`, `doc.template_id`, `doc.owner_id`

### Testing
- Mock Puppeteer and S3 in tests — never launch a real browser or hit
  real storage in unit tests
- Test template rendering separately from PDF generation
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
