# Docker best practices

Read by: all teams working with Dockerfiles and Docker Compose

## Multi-stage builds

Always use multi-stage builds:
1. **deps** — install dependencies (package.json/requirements.txt → install)
2. **builder** — copy source, compile/build
3. **migrate** (optional) — Prisma/Alembic migration runner
4. **runner** — minimal production image

## Layer ordering (cache optimisation)

1. Copy dependency manifest FIRST (package.json, package-lock.json, requirements.txt)
2. Install dependencies
3. THEN copy source code
4. Build

This means changing a source file doesn't re-download all dependencies.

## Base images

- Node.js: `node:22-alpine` (small, fast)
- Python: `python:3.12-slim` (glibc available for compiled packages)
- Exception: services needing Chromium (starter-docs) must use `slim` not `alpine`
- Always pin the version tag — `node:22-alpine`, not `node:alpine`

## Security

- Non-root user in runner stage: `addgroup --system`, `adduser --system`
- Never put secrets in build args or layers — use runtime env vars
- Use `.dockerignore` to exclude: node_modules, .git, .env*, tests, docs, coverage

## Build args

- Use `ARG` for values that must be inlined at build time
- Next.js: `NEXT_PUBLIC_*` MUST be build args (inlined during `next build`)
- Place `ARG` before the stage that uses it
- Set `ENV` from the `ARG` to make it available to `RUN`:
  ```dockerfile
  ARG NEXT_PUBLIC_ENVIRONMENT=production
  ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT
  RUN npm run build
  ```

## Image tagging

- Tag per environment: `:ci`, `:rc`, `:prod`
- Never use `:latest` in compose files — always explicit tags
- `envctl rebuild {env}` builds and tags for that environment
- `envctl up {env}` starts from pre-built tagged images (no rebuild)

## Dependency installation

- Node.js: `npm ci` (not `npm install`) for reproducible builds
- Python: `pip install --no-cache-dir -r requirements.txt`
- Copy lock files alongside manifests for deterministic installs

## Health checks

- Define in docker-compose, NOT in Dockerfile
- Compose health checks are environment-specific (different ports per env)
- Use `wget --spider` or `curl -f` for HTTP checks
- Use `test -f /tmp/ready` for services that write a ready file (grafana/otel-lgtm)

## Compose conventions

- `name:` per environment for concurrent running (project-ci, project-rc, project-prod)
- Port mappings via env vars: `${WEB_PORT:-3000}:3000`
- App services use `image:` tags — only CI has `build:` directives
- db-migrate as init container with `restart: "no"` and `service_completed_successfully`
- Use `depends_on` with `condition: service_healthy` for startup ordering

## Prisma in Docker

- Run `npx prisma generate` in the deps stage (generates client)
- Migrate stage: use `./node_modules/.bin/prisma` not `npx prisma` (avoids resolving wrong version)
- Copy prisma/ directory and node_modules/.prisma + node_modules/@prisma to runner
- Ensure `public/` directory exists before `npm run build`: `RUN mkdir -p public`

NEVER:
- Use `:latest` tag in production compose files
- Put secrets in Dockerfile (ARG or ENV with real values)
- Run as root in the runner stage
- Use `npm install` instead of `npm ci` in Docker builds
- Skip .dockerignore — it prevents accidentally copying node_modules into the build context
- Let build cache grow unbounded — `envctl rebuild` prunes automatically, but manual `docker system prune` may be needed if disk fills between rebuilds
- Ignore "no space left on device" errors — this means Docker volumes or build cache have filled the disk. Run `docker system prune` and `docker builder prune` to recover
