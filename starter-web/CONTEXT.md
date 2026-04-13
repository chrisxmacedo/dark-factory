# starter-web/

Next.js web frontend service template. Copy this directory to bootstrap a new
Next.js 14 application with TypeScript, Tailwind CSS, Prisma, and NextAuth.js.

## Contents

- **CLAUDE.md** -- Coding conventions and project structure reference
- **Dockerfile** -- Multi-stage build (deps, builder, migrate, runner)
- **package.json** -- Scripts and dependency placeholders
- **jest.config.ts** -- Test configuration with ts-jest, dual environments (node + jsdom)
- **tsconfig.json** -- Strict TypeScript with Next.js plugin and @/* path alias
- **.env.example** -- All common environment variables with placeholder values
- **.gitignore** -- Node.js + Next.js + environment files
- **src/app/** -- App Router pages, layouts, and API routes
- **src/lib/** -- Shared utilities (Prisma, Redis, logger, encryption)
- **src/middleware.ts** -- Correlation ID middleware (x-request-id)

## For agents

- Replace all `{PLACEHOLDER}` values with project-specific configuration before use.
- Run `npm install` after replacing placeholder values in package.json.
- Copy `prisma/schema.prisma` from the project's database schema or create one.
- The Dockerfile expects `output: "standalone"` in next.config.js -- add it.
- See `CLAUDE.md` for coding conventions and common commands.
