# CLAUDE.md -- {PROJECT_NAME}-web

This file covers coding conventions for this web frontend repo. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

<!-- When creating a new project from starter, you MUST also create the
     parent-level files. -->

---

## Stack

- **Next.js 14**, React, TypeScript, Tailwind CSS
- **Database:** Prisma ORM (PostgreSQL)
- **Auth:** NextAuth.js with Prisma adapter
- **Cache:** ioredis (Redis)
- **Logging:** Pino (structured JSON)
- **Observability:** OpenTelemetry (traces + metrics), Sentry (errors)
- **Validation:** Zod
- **Testing:** Jest (unit/component), Playwright (E2E)
- **Lint:** ESLint (eslint-config-next)
- **Format:** Prettier (with prettier-plugin-tailwindcss)

---

## Project structure

```
src/
├── app/                  # App Router
│   ├── layout.tsx        # Root layout (Tailwind, providers)
│   ├── page.tsx          # Home page
│   ├── globals.css       # Tailwind base imports
│   ├── (app)/            # Authenticated route group
│   │   ├── layout.tsx    # App shell (sidebar, nav)
│   │   └── {route}/
│   │       └── page.tsx
│   ├── auth/             # Auth pages (sign-in, error)
│   └── api/              # API routes
│       ├── health/route.ts
│       ├── auth/[...nextauth]/route.ts
│       └── {resource}/route.ts
├── components/           # React components
│   ├── ui/               # Generic UI primitives
│   └── {feature}/        # Feature-specific components
├── lib/                  # Shared utilities
│   ├── prisma.ts         # Prisma client singleton
│   ├── redis.ts          # Redis client singleton
│   ├── logger.ts         # Pino structured logger
│   ├── encryption.ts     # AES-256-GCM encrypt/decrypt
│   ├── auth.ts           # NextAuth config + helpers
│   └── otel.ts           # OpenTelemetry setup
├── middleware.ts          # Correlation ID middleware
└── types/                # Shared TypeScript types

prisma/
├── schema.prisma         # Database schema
└── migrations/           # Prisma migrations (never edit manually)

tests/
├── e2e/                  # Playwright E2E tests
└── fixtures/             # Test data and helpers
```

---

## Conventions

### General
- TypeScript strict mode -- all functions must have full type annotations
- All module-level code must be importable without side effects
- Never use `console.log` in production code -- use `logger` from `@/lib/logger`
- Never hardcode secrets or URLs -- always read from environment variables
- Never commit `.env` -- use `.env.example` as the reference

### React / Next.js
- **Server Components by default** -- only add `"use client"` when the
  component needs browser APIs, event handlers, or React hooks
- Use App Router conventions: `layout.tsx`, `page.tsx`, `route.ts`
- Route groups with `(parentheses)` for layout grouping without URL segments
- Colocate loading.tsx, error.tsx, not-found.tsx with their page when needed
- Use `next/image` for all images, `next/link` for all navigation

### Styling
- Tailwind CSS for all styling -- no CSS modules, no styled-components
- Use `globals.css` only for Tailwind directives and CSS custom properties
- Use `prettier-plugin-tailwindcss` to auto-sort class names
- Extract repeated class patterns into components, not utility classes
- **Always read the existing component library** (`src/components/ui/`) before
  creating new UI elements -- reuse existing patterns, never guess class names
- If a design system or theme config exists (`tailwind.config.ts`), read it
  before applying colours, spacing, or typography

### API routes
- All API routes live in `src/app/api/{resource}/route.ts`
- Use standard response envelopes:
  ```typescript
  // Success
  { data: T, meta?: { ... } }
  // Error
  { error: { code: string, message: string } }
  ```
- Validate request bodies with Zod schemas
- Use auth middleware to protect endpoints -- never trust client-supplied IDs
- Standard error codes: `not_found`, `validation_error`, `unauthorized`,
  `forbidden`, `conflict`, `rate_limited`, `internal_error`
- Always return appropriate HTTP status codes

### Authentication
- NextAuth.js with Prisma adapter
- Use `getServerSession()` in Server Components and API routes
- Protect client pages with middleware or session checks
- Never expose tokens or secrets to the client

### Database
- Prisma ORM for all database access
- One model per table in `prisma/schema.prisma`
- Always include `id`, `createdAt`, `updatedAt` on every model
- Use UUID primary keys
- Generate migrations with `npx prisma migrate dev -m "description"`
- Never edit migration files after they have been applied

### Logging
- Use Pino logger from `@/lib/logger`
- Create child loggers with request context (correlation ID, path)
- Log levels: `error` for failures, `warn` for degraded state, `info` for
  business events, `debug` for development tracing
- Structured fields, not string interpolation

### Testing
- Jest for unit tests (`.test.ts`) and component tests (`.test.tsx`)
- Playwright for E2E tests in `tests/e2e/`
- Test files live next to their source in `__tests__/` directories
- Every new API route needs at least one test
- Test both success and error cases
- Tests must not depend on each other or on execution order

---

## Common commands

```bash
npm run dev              # Start dev server
npm run build            # Production build
npm run start            # Start production server
npm run test             # Run Jest tests
npm run test:watch       # Run Jest in watch mode
npm run test:coverage    # Run Jest with coverage
npm run lint             # ESLint
npm run format           # Prettier write
npm run format:check     # Prettier check
npx prisma generate      # Generate Prisma client
npx prisma migrate dev   # Create and apply migration
npx prisma db push       # Push schema without migration (dev only)
```

---

## Before writing code

- Read existing files in the area being modified before generating any code
- If modifying UI: read `src/components/ui/` and `tailwind.config.ts` first
- If the ticket references a page or component, read the current implementation
- Verify you are in the correct repo: `pwd && git remote get-url origin`

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npm run lint && npm run format:check && npm run test
```

---

## PRD and PLAN

If `PRD.md` and `PLAN.md` exist in the repo root, read them before starting
any ticket. They are the source of truth for what this service does and how it
should behave.
