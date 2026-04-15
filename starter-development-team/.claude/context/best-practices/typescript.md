# TypeScript best practices

Read by: all teams working on TypeScript starters (web, worker, gateway, batch, notification, docs, orchestrator, realtime, audit)

## Compiler

- `strict: true` always — includes strictNullChecks, noImplicitAny, etc.
- Enable `noUncheckedIndexedAccess` and `noImplicitReturns`
- Target: ES2022 minimum
- Module: ESNext (Next.js) or CommonJS (Node.js services)

## Types

- All functions typed — parameters AND return type
- No `any` except at system boundaries (external API responses) — immediately narrow with Zod
- Prefer `interface` for object shapes, `type` for unions and intersections
- Use `readonly` for data that shouldn't be mutated
- String enums or `as const` objects — never numeric enums
- Export types alongside their implementations

NEVER:
- Use `any` as a shortcut — use `unknown` and narrow
- Use `!` non-null assertion — handle the null case
- Use `@ts-ignore` or `@ts-expect-error` without a comment explaining why

## Variables and functions

- `const` by default, `let` only when reassignment is needed
- Never `var`
- Async/await over raw Promises — no `.then()` chains
- Prefer early returns over deep nesting
- Prefer named exports — no default exports (except where framework requires: Next.js pages)

## Error handling

- Never catch and ignore — always log or re-throw with context
- Typed error classes for domain errors (e.g. `GroupError`, `ThreadLinkError`)
- Domain errors carry `statusCode` and `message` — the error handler maps them to HTTP responses
- Unexpected errors: log full stack + context, return generic 500

## Naming

- `camelCase` for variables, functions, parameters
- `PascalCase` for types, interfaces, classes, enums, components
- `UPPER_SNAKE_CASE` for constants and environment variable references
- File names: `kebab-case.ts` for modules, `PascalCase.tsx` for React components

## Imports

- Named imports — not `import * as`
- Group: external packages → internal modules → relative imports
- No circular imports — if two modules import each other, extract shared code

## Null handling

- `??` for defaults (nullish coalescing)
- `?.` for optional chaining
- Explicit null checks over type assertions
- Prefer `undefined` over `null` for optional values (TypeScript convention)

## Strings and queries

- No string concatenation for SQL — use parameterised queries or ORM
- Template literals for string building (not `+` concatenation)
- No `eval()` or `Function()` constructor

## Logging

- Use the project's Pino logger — never `console.log` / `console.error`
- Structured logging: pass objects, not string interpolation
  - YES: `logger.info({ userId, action }, "User authenticated")`
  - NO: `logger.info("User " + userId + " authenticated")`

## Dependencies

- Pin versions via package-lock.json — `npm ci` for reproducible installs
- Review changelogs before major version upgrades
- Audit regularly: `npm audit`
- Separate devDependencies from dependencies
