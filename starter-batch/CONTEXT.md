# starter-batch

Starter template for scheduled batch processing services.

## What this is for

Services that run on a schedule to process large data sets:
- End-of-day reconciliation (financial close, ledger balancing)
- Report generation (daily summaries, regulatory filings, analytics exports)
- Data migration and ETL (backfills, schema migrations, warehouse loads)
- Scheduled email campaigns (digest emails, renewal reminders)
- Regulatory reporting (compliance snapshots, audit trail generation)
- Periodic cleanup (archival, soft-delete purge, temp file removal)

## When to use this vs starter-worker

| Use case | Template |
|----------|----------|
| Runs on a schedule (cron, QStash, CloudWatch Events) | **starter-batch** |
| Processes a bounded data set per run, then exits | **starter-batch** |
| Event-driven, processes items as they arrive | starter-worker |
| Long-running process that stays alive between jobs | starter-worker |
| Real-time queue consumer (BullMQ, Kafka) | starter-worker |
| Mixed: HTTP triggers a one-off batch run | **starter-batch** (invoked by API) |

**Rule of thumb:** if the process starts, does work, and exits — use batch.
If the process stays alive waiting for the next event — use worker.

## Key characteristics

- **Run-and-exit** — starts, processes data, exits with code 0 or 1
- **Idempotent** — safe to re-run the same job for the same period
- **Resumable** — checkpoints progress so interrupted runs can continue
- **Bounded runtime** — every job has a maximum timeout
- **Progress reporting** — logs progress at regular intervals
- **Output to storage** — results go to S3/MinIO (files) or database (records)
- **No health endpoint** — batch jobs are not long-running services

## Tech stack

Node.js 22, TypeScript (strict), Prisma, ioredis, Pino, Jest
