# Environment configuration rules

Read by: Team Lead, Development Team when configuring Docker or environment variables

## NEXT_PUBLIC_* variables (Next.js projects)

Next.js inlines `NEXT_PUBLIC_*` variables at **build time**. Runtime values
set in docker-compose environment blocks are ignored for client-side code.

**Rule:** `NEXT_PUBLIC_*` variables MUST be Docker build args, not runtime
env vars.

**In the Dockerfile:**
```dockerfile
ARG NEXT_PUBLIC_ENVIRONMENT=production
ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT
RUN npm run build
```

**In envctl rebuild:**
```bash
docker build -t "service-web:$env" \
  --build-arg "NEXT_PUBLIC_ENVIRONMENT=$next_env" \
  ../service-web
```

**Never put NEXT_PUBLIC_* in .env files** — they're build-time only.

## Docker image tagging per environment

Each environment has its own tagged images. Rebuilding one doesn't affect
the others. Only CI builds from source — RC and Prod use pre-built images.

| Environment | Image tags | Built from |
|---|---|---|
| CI | `service-web:ci`, `service-sync:ci` | ci branch source |
| RC | `service-web:rc`, `service-sync:rc` | release-rc-* branch source |
| Prod | `service-web:prod`, `service-sync:prod` | main branch source |

**Build:**
```bash
envctl rebuild ci    # checks out ci, builds :ci images
envctl rebuild rc    # checks out release-rc-*, builds :rc images
envctl rebuild prod  # checks out main, builds :prod images
```

**Start (no rebuild):**
```bash
envctl up ci    # uses existing :ci images (instant)
envctl up rc    # uses existing :rc images (instant)
envctl up prod  # uses existing :prod images (instant)
```

## Environment-specific build args

`envctl rebuild` maps environment names to build arg values:

| env | NEXT_PUBLIC_ENVIRONMENT | Notes |
|---|---|---|
| ci | ci | Dev-login bypass enabled |
| rc | test | Fixture mode, dev-login enabled |
| prod | prod-parity | Real APIs, no dev-login |

## .env files purpose

| File | Committed? | Contains |
|---|---|---|
| `.env.ci` | Yes | Throwaway CI values, port mappings |
| `.env.test` | Yes | Test/RC values, port offsets (+100) |
| `.env.prod-parity` | No (gitignored) | Real API keys, strong passwords |
| `.env.jira` | No (gitignored) | Jira API credentials for scripts |
| `.env.example` (per repo) | Yes | Documents all required vars with placeholders |
