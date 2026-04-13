# starter-worker

Starter template for background job processing and event consumer services.

## What this is for

Services that run continuously in the background to:
- Consume jobs from Redis queues (BullMQ, custom)
- Consume events from Kafka/Redpanda topics
- Process tasks asynchronously (transaction processing, notification sending,
  email sync, report generation, data pipelines)
- Write results back to a database or downstream service

## When to use this vs starter-api

| Use case | Template |
|----------|----------|
| HTTP endpoints serving requests | starter-api |
| Background job processing | **starter-worker** |
| Event-driven consumers | **starter-worker** |
| Scheduled cron tasks | **starter-worker** |
| Mixed HTTP + background work | starter-api for the HTTP surface, **starter-worker** for the job processor |

## Key characteristics

- **Long-running process** — not request/response, runs until stopped
- **Idempotent handlers** — every job can be safely retried
- **Graceful shutdown** — drains queues, finishes current job, closes connections
- **Dead-letter queue** — failed jobs (after N retries) are moved aside, not lost
- **Observability** — structured logging, OpenTelemetry traces, health endpoint
- **Circuit breakers** — external API calls degrade gracefully under failure

## Tech stack

Node.js 22, TypeScript (strict), Prisma, ioredis, Pino, OpenTelemetry, Jest
