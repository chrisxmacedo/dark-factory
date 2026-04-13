# Coding Conventions — {project-name}-batch

## Project structure

```
src/
  index.ts          — Entry point: parse job name from args/env, run it, exit
  jobs/             — Individual batch jobs (one file per job)
  lib/              — Shared utilities (logger, prisma, checkpoint, storage)
  reports/          — Output generators (CSV, PDF, JSON formatters)
```

## TypeScript

- Strict mode enabled (`"strict": true` in tsconfig.json)
- No `any` — use `unknown` and narrow
- All functions have explicit return types
- Prefer `interface` over `type` for object shapes

## Job design

Each job is a standalone async function exported from `src/jobs/`. Jobs:

- **Can be run independently** — `npm run job:reconcile`, `npm run job:report`
- **Are idempotent** — running the same job twice for the same period produces
  the same result without side effects (use upserts, check-before-write)
- **Are resumable** — checkpoint progress to Redis or database so interrupted
  runs pick up where they left off instead of restarting
- **Report progress** — log at regular intervals (every N records, every 10s)
  using structured logging with `jobName`, `runId`, `progress`
- **Have a maximum runtime** — enforce a timeout; exit with code 1 if exceeded
- **Exit cleanly** — code 0 on success, code 1 on failure. No hanging processes.

## Output

- File outputs (reports, exports, CSVs) go to S3/MinIO via `src/lib/storage.ts`
- Record-level results go to the database via Prisma
- Never write output to the local filesystem in production

## Logging

Use Pino via `src/lib/logger.ts`. Every log line includes:

```json
{ "jobName": "reconcile", "runId": "abc-123", "progress": "1500/8000" }
```

Use `createJobLogger(jobName, runId)` to get a child logger with these fields
bound. Log levels: `info` for progress, `warn` for recoverable issues,
`error` for failures, `debug` for row-level detail.

## Checkpointing

Use `src/lib/checkpoint.ts` for resumability:

```ts
await saveCheckpoint(runId, { lastProcessedId: 1500, total: 8000 });
const cp = await loadCheckpoint(runId);
```

Store checkpoints in Redis (fast, ephemeral) or database (durable). Clear
checkpoints on successful completion.

## Testing

- Jest for unit and integration tests
- Each job has a test file in `__tests__/` or `tests/`
- Test idempotency: run the job twice, assert same outcome
- Test resumability: save a checkpoint, run job, assert it resumes
- Mock external services (S3, database) in unit tests

## Process lifecycle

```
[scheduler] → starts container / invokes function
           → src/index.ts parses JOB_NAME from args or env
           → calls the matching job function
           → job logs progress, checkpoints, writes output
           → exits 0 (success) or 1 (failure)
[scheduler] ← reads exit code, logs result
```

No health check endpoint. No HTTP server. No process manager.
The scheduler (cron, QStash, ECS Scheduled Task) is responsible for
invoking the job and monitoring its exit code.

## Before writing code

- Read existing files in the area being modified before generating any code
- If modifying an existing module, read the current implementation first
- Verify you are in the correct repo: `pwd && git remote get-url origin`

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
npm run lint && npm run format:check && npm test
```
