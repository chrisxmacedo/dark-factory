# Next.js best practices

Read by: teams working on starter-web projects. Extends typescript.md.

## Routing

- App Router only (not Pages Router) — all routes under `src/app/`
- Route groups `(group)` for layout organisation without URL segments
- Dynamic routes: `[id]` for single params, `[...slug]` for catch-all
- Route handlers: `src/app/api/{resource}/route.ts` exporting GET/POST/PATCH/DELETE

## Server vs Client components

- Server Components by default — no directive needed
- Add `"use client"` ONLY when the component needs: browser APIs, event handlers, React hooks (useState, useEffect), or third-party client libraries
- Never add `"use client"` to a page.tsx unless it truly needs client interactivity
- Data fetching: do it in Server Components, pass data down as props

## API route patterns

- Auth middleware wrapper: extract session check into shared `withAuth()` — never copy-paste per route
- JSON parsing helper: shared `parseRequestBody<T>()` — never duplicate try-catch
- Error handling wrapper: shared `withErrorHandling()` — catches domain errors, returns consistent shapes
- Schema validation: Zod schema on every POST/PATCH/DELETE — validate before processing
- The first API route must establish these patterns. The second route reuses them.

NEVER:
- Copy-paste auth check / JSON parsing / error handling across routes
- Return different error shapes from different endpoints
- Access `process.env` in client components (except `NEXT_PUBLIC_*`)

## Response envelopes

- Success: `{ data: T }` or `{ data: T[], meta: { total, limit, offset } }`
- Error: `{ error: { code: "not_found", message: "Resource not found" } }`
- Consistent across ALL endpoints — no exceptions

## Environment variables

- `NEXT_PUBLIC_*` variables: inlined at build time by Next.js
- Must be Docker build args, NOT runtime env vars
- Never put `NEXT_PUBLIC_*` in `.env` files for Docker — they're ignored at runtime
- Server-side env vars (DATABASE_URL, etc.): available at runtime via `process.env`

## Database

- Prisma singleton: cache in `globalThis` for dev hot reload
- `prisma.$transaction()` for multi-step writes
- Lazy connection: don't connect during build or module import

## Redis

- Lazy connection via `getRedis()` — don't connect on import
- Singleton with retry strategy (exponential backoff, max 2s)
- Throws if `REDIS_URL` not set — fail fast

## Middleware

- `src/middleware.ts`: correlation ID injection (`x-request-id`)
- Keep middleware lightweight — no database calls, no heavy logic
- Matcher: exclude static files and Next.js internals

## Static assets

- `public/` directory: ensure it exists even if empty (`mkdir -p public` in Dockerfile)
- Use `next/image` for image optimisation
- Use `next/font` for self-hosted fonts

## Page patterns

- `loading.tsx` for route-level suspense
- `error.tsx` for error boundaries per route segment
- `not-found.tsx` for custom 404 pages
- `generateMetadata()` for dynamic page titles

## Build

- `next build` produces standalone output
- Enable `instrumentationHook` for OTel
- Suppress noisy OTel webpack warnings via `externals` in `next.config.js`

## Auth

- NextAuth.js with Prisma adapter
- Encrypt OAuth tokens before storing (AES-256-GCM)
- Session strategy: database (30-day max age)
- Dev-login bypass: available when `NEXT_PUBLIC_ENVIRONMENT=ci|test`
