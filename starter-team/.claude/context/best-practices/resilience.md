# Resilience best practices

Read by: all teams working with external services, queues, or multi-step operations

## Retry with exponential backoff

- For transient failures: network timeouts, HTTP 503, connection refused
- Max 3 attempts, base delay 1s, multiplier 2x, jitter ±25%
- Log each retry: attempt number, delay, error message
- Only retry on retryable errors

NEVER retry:
- 400 Bad Request (client error, won't change on retry)
- 401/403 (auth failure, won't change on retry)
- 404 Not Found (resource doesn't exist)
- 409 Conflict (state conflict, needs different resolution)

## Circuit breaker

- Three states: **closed** (normal), **open** (fast-fail), **half-open** (probe)
- Open after N consecutive failures (default: 5)
- Half-open after timeout (default: 60s) — allow one probe request
- Close on successful probe, re-open on failed probe
- Separate circuit breaker per downstream service
- Health endpoint should report circuit breaker states
- Fail open on non-critical services (log degradation, don't block request)

## Dead-letter queue

- For messages/jobs that fail repeatedly
- After N processing attempts (default: 3), move to dead-letter queue
- Log the failure with full message context and all attempt errors
- Alert on dead-letter queue growth
- Provide tooling to inspect and replay dead-letter messages

NEVER:
- Silently discard failed messages
- Retry infinitely without a dead-letter limit
- Process dead-letter messages automatically without investigation

## Idempotency

- Every operation must be safe to re-execute
- API endpoints: Idempotency-Key header, cache response for 24h
- Queue processing: check "already processed" before executing (by job ID)
- Database writes: use ON CONFLICT for upserts, check existence before insert
- File operations: overwrite is acceptable, partial writes are not

## Graceful shutdown

On SIGTERM / SIGINT:
1. Set shutdown flag — health endpoint returns 503
2. Stop accepting new requests/jobs
3. Finish current request/job (with timeout — default 30s)
4. Close connections: database, Redis, HTTP server, WebSocket
5. Exit with code 0

NEVER:
- Kill in-progress requests (data corruption risk)
- Start new work during shutdown
- Wait forever — enforce a maximum shutdown timeout

## Timeouts

- Every external call MUST have a timeout
- HTTP requests: 30s default, 5s for health checks
- Database queries: 10s default
- Queue job processing: configurable per job type, with maximum
- WebSocket connections: heartbeat every 30s, disconnect after 3 missed pongs

NEVER:
- Make an external call without a timeout
- Set timeout to 0 or infinity
- Catch timeout errors and retry without backoff

## Database transactions

- Multi-step writes MUST be wrapped in a transaction
- Prisma: `prisma.$transaction(async (tx) => { ... })`
- SQLAlchemy: `async with session.begin(): ...`
- Partial state is a bug — either all writes succeed or none do
- Keep transactions short — don't hold locks while calling external services

NEVER:
- Perform multiple related writes without a transaction
- Call external APIs inside a transaction (holds DB lock)
- Catch transaction rollback and continue as if it succeeded

## Bulkhead isolation

- Separate connection pools per downstream service
- Separate circuit breakers per downstream service
- One failing dependency should not exhaust connections for others
- Monitor pool utilisation — alert when consistently above 80%

## Backpressure

- Queues: set maximum queue depth, reject new messages when full
- WebSocket: drop messages when client `bufferedAmount` exceeds threshold
- API: rate limiting is a form of backpressure — enforce it

NEVER:
- Buffer indefinitely — memory will eventually exhaust
- Process faster than downstream can handle without monitoring
