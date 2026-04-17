# Queue and event best practices

Read by: all teams using queues or events (worker, notification, orchestrator, audit, realtime)

## Event schema design

- Every event uses a shared envelope type: `type` (string), `payload` (object), `metadata` (object)
- Metadata always includes: `timestamp`, `correlationId`, `source`, `version`
- Define a shared `EventEnvelope` type — all producers and consumers import it
- Payloads are typed per event — no `any`, no untyped objects

TypeScript:

```typescript
interface EventMetadata {
  timestamp: string;       // ISO 8601
  correlationId: string;   // Propagated from the originating request
  source: string;          // Service that produced the event
  version: number;         // Schema version (start at 1)
}

interface EventEnvelope<T = unknown> {
  id: string;              // Unique event ID (UUID)
  type: string;            // e.g. "user.created", "send.notification"
  payload: T;
  metadata: EventMetadata;
}
```

Python:

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class EventMetadata:
    timestamp: str            # ISO 8601
    correlation_id: str       # Propagated from the originating request
    source: str               # Service that produced the event
    version: int              # Schema version (start at 1)

@dataclass
class EventEnvelope:
    id: str                   # Unique event ID (UUID)
    type: str                 # e.g. "user.created", "send.notification"
    payload: dict[str, Any]
    metadata: EventMetadata
```

NEVER:
- Send events without metadata (correlation and traceability are mandatory)
- Use raw strings or untyped dicts as event payloads
- Omit the event ID (required for idempotency and debugging)

## Event naming

- Past tense for facts (things that happened): `user.created`, `order.completed`, `payment.failed`
- Imperative for commands (things to do): `send.notification`, `process.payment`, `generate.report`
- Namespace with dot notation: `{domain}.{action}`
- Lowercase, no spaces, no special characters beyond dots

Examples:

```
# Facts (past tense)
user.created
user.updated
order.completed
payment.refunded

# Commands (imperative)
send.notification
process.payment
generate.invoice
sync.inventory
```

NEVER:
- Mix tenses within a category (don't use `user.create` for a fact)
- Use slashes, camelCase, or underscores in event type names
- Use generic names like `event`, `message`, or `update` without a domain prefix

## Producer patterns

- Publish events AFTER the database transaction commits — never inside it
- Include the correlation ID from the incoming request (propagate through the chain)
- Include enough data in the payload for consumers to act without querying back
- Keep payloads lean — include IDs and the changed fields, not entire database rows

TypeScript (BullMQ):

```typescript
import { Queue } from "bullmq";
import { randomUUID } from "crypto";

const orderQueue = new Queue("myapp:worker:order-events", {
  connection: { url: process.env.REDIS_URL },
});

async function completeOrder(orderId: string, correlationId: string): Promise<void> {
  // 1. Commit the DB transaction first
  const order = await prisma.$transaction(async (tx) => {
    const updated = await tx.order.update({
      where: { id: orderId },
      data: { status: "completed", completedAt: new Date() },
    });
    await tx.orderItem.updateMany({
      where: { orderId },
      data: { status: "fulfilled" },
    });
    return updated;
  });

  // 2. Publish the event AFTER the transaction succeeds
  await orderQueue.add("order.completed", {
    id: randomUUID(),
    type: "order.completed",
    payload: { orderId: order.id, userId: order.userId, total: order.total },
    metadata: {
      timestamp: new Date().toISOString(),
      correlationId,
      source: "order-service",
      version: 1,
    },
  });
}
```

Python (rq):

```python
from rq import Queue
from uuid import uuid4
from datetime import datetime, timezone

order_queue = Queue("myapp:worker:order-events", connection=get_redis())

def complete_order(order_id: str, correlation_id: str) -> None:
    # 1. Commit the DB transaction first
    with db.session.begin():
        order = Order.query.get(order_id)
        order.status = "completed"
        order.completed_at = datetime.now(timezone.utc)

    # 2. Publish the event AFTER the transaction succeeds
    order_queue.enqueue(
        process_order_event,
        {
            "id": str(uuid4()),
            "type": "order.completed",
            "payload": {"order_id": order.id, "user_id": order.user_id, "total": order.total},
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "correlation_id": correlation_id,
                "source": "order-service",
                "version": 1,
            },
        },
    )
```

NEVER:
- Publish events inside a database transaction (if the publish succeeds but the transaction rolls back, consumers act on phantom data)
- Publish events without a correlation ID (breaks traceability across services)
- Include entire database rows in event payloads (couples consumers to the producer's schema)

## Consumer patterns

- Idempotent handlers — use event ID + consumer group for deduplication
- Process one event at a time per partition/queue (unless you explicitly handle concurrency)
- Acknowledge AFTER processing completes, not before
- Log event receipt and completion with the event ID and type

TypeScript (BullMQ):

```typescript
import { Worker } from "bullmq";

const worker = new Worker(
  "myapp:worker:order-events",
  async (job) => {
    const event: EventEnvelope = job.data;
    const logger = createJobLogger(event.id, event.metadata.correlationId);

    // Idempotency check
    const alreadyProcessed = await prisma.processedEvent.findUnique({
      where: { eventId_consumerGroup: { eventId: event.id, consumerGroup: "notification" } },
    });
    if (alreadyProcessed) {
      logger.info("Event already processed, skipping");
      return;
    }

    // Process the event
    await handleOrderCompleted(event.payload);

    // Mark as processed
    await prisma.processedEvent.create({
      data: { eventId: event.id, consumerGroup: "notification", processedAt: new Date() },
    });

    logger.info({ type: event.type }, "Event processed successfully");
  },
  {
    connection: { url: process.env.REDIS_URL },
    concurrency: 5,
  },
);
```

Python (rq):

```python
def process_order_event(event: dict) -> None:
    event_id = event["id"]
    logger = create_job_logger(event_id, event["metadata"]["correlation_id"])

    # Idempotency check
    if ProcessedEvent.query.filter_by(event_id=event_id, consumer_group="notification").first():
        logger.info("Event already processed, skipping")
        return

    # Process the event
    handle_order_completed(event["payload"])

    # Mark as processed
    db.session.add(ProcessedEvent(event_id=event_id, consumer_group="notification"))
    db.session.commit()

    logger.info(f"Event {event['type']} processed successfully")
```

NEVER:
- Acknowledge a message before processing it (if the consumer crashes, the event is lost)
- Skip idempotency checks ("it probably won't happen" is not a strategy)
- Query the producer's database from the consumer (use the event payload or a local cache)

## Dead-letter queues

- Failed events go to DLQ after max retries (default: 3)
- DLQ entries must include: original event, error message, attempt count, timestamps for each attempt
- DLQ events must be inspectable — log event ID, error, and attempt count at `error` level
- Human reviews DLQ periodically — provide tooling to inspect and replay
- Alert on DLQ growth (monitor queue depth)

TypeScript (BullMQ):

```typescript
// BullMQ handles DLQ automatically when attempts are exhausted.
// Listen for the "failed" event to log and alert.

worker.on("failed", (job, err) => {
  if (job && job.attemptsMade >= (job.opts.attempts ?? 3)) {
    logger.error({
      eventId: job.data.id,
      type: job.data.type,
      error: err.message,
      attempts: job.attemptsMade,
    }, "Event moved to dead-letter queue");
    // Trigger alert (e.g. Slack, PagerDuty)
  }
});
```

Python (rq):

```python
from rq import Queue

failed_queue = Queue("myapp:worker:order-events:dlq", connection=get_redis())

def handle_failure(job, exc_type, exc_value, traceback):
    logger.error(
        "Event moved to dead-letter queue",
        extra={
            "event_id": job.args[0]["id"],
            "error": str(exc_value),
            "attempts": job.retries_left,
        },
    )
    failed_queue.enqueue(inspect_failed_event, job.args[0], str(exc_value))
```

NEVER:
- Silently discard failed events
- Retry infinitely without a dead-letter limit
- Automatically replay DLQ events without investigation (the same bug will fail the same way)

## Retry strategy

- Exponential backoff: 1s, 4s, 16s (base 1s, multiplier 4x)
- Distinguish retryable errors from non-retryable errors
- Log each retry attempt with attempt number and delay
- After max retries, move to DLQ

Retryable: network timeout, HTTP 503, connection refused, Redis timeout
Non-retryable: HTTP 400, schema validation failure, missing required field, deserialization error

TypeScript (BullMQ):

```typescript
await queue.add("order.completed", eventData, {
  attempts: 3,
  backoff: {
    type: "exponential",
    delay: 1000,  // 1s base — BullMQ applies 1s, 4s, 16s with default multiplier
  },
  removeOnComplete: 1000,
  removeOnFail: 5000,
});

// Inside the worker, throw for retryable errors, use UnrecoverableError for non-retryable
import { UnrecoverableError } from "bullmq";

async function processEvent(event: EventEnvelope): Promise<void> {
  try {
    await callExternalService(event.payload);
  } catch (err) {
    if (isNonRetryable(err)) {
      throw new UnrecoverableError(`Non-retryable: ${err.message}`);
    }
    throw err; // BullMQ will retry
  }
}

function isNonRetryable(err: unknown): boolean {
  if (err instanceof HttpError) {
    return [400, 401, 403, 404, 409, 422].includes(err.status);
  }
  return false;
}
```

Python (rq):

```python
from rq import Retry

order_queue.enqueue(
    process_order_event,
    event_data,
    retry=Retry(max=3, interval=[1, 4, 16]),
)
```

NEVER:
- Retry non-retryable errors (wastes resources, same result every time)
- Use fixed delays instead of exponential backoff (thundering herd on recovery)
- Retry without logging (invisible failures are the worst kind)

## Ordering guarantees

- Partition by entity ID for ordered processing within an entity
- Accept out-of-order delivery across different entities
- Use sequence numbers when strict ordering within an entity is required
- If ordering matters, process one event at a time per partition

TypeScript (BullMQ):

```typescript
// Use the entity ID as the job's group ID for FIFO within that entity
await queue.add("user.updated", eventData, {
  // BullMQ Pro: group by entity for ordered processing
  group: { id: eventData.payload.userId },
});

// Without BullMQ Pro: use a dedicated queue per entity (only for high-value entities)
// Or include a sequence number and handle reordering in the consumer
```

Python:

```python
# Include sequence number in the event for ordering
event = {
    "id": str(uuid4()),
    "type": "user.updated",
    "payload": {"user_id": user_id, "name": new_name, "sequence": 42},
    "metadata": { ... },
}

# Consumer checks sequence before processing
def process_user_event(event: dict) -> None:
    user_id = event["payload"]["user_id"]
    sequence = event["payload"]["sequence"]

    last_processed = get_last_processed_sequence(user_id)
    if sequence <= last_processed:
        logger.info(f"Skipping out-of-order event (seq {sequence} <= {last_processed})")
        return

    handle_user_update(event["payload"])
    set_last_processed_sequence(user_id, sequence)
```

NEVER:
- Assume global ordering across all events (queues don't guarantee it)
- Process events in parallel when ordering within an entity matters
- Ignore sequence gaps without investigation (may indicate lost events)

## Backpressure

- Consumer must not pull faster than it can process
- Use concurrency limits to control throughput
- Monitor queue depth as a health signal — alert when depth exceeds threshold
- Reject or defer new events when the queue is full

TypeScript (BullMQ):

```typescript
const worker = new Worker("myapp:worker:order-events", handler, {
  connection: { url: process.env.REDIS_URL },
  concurrency: 5,           // Process at most 5 jobs simultaneously
  limiter: {
    max: 100,               // Max 100 jobs
    duration: 60_000,       // Per 60 seconds
  },
});

// Monitor queue depth
async function checkQueueHealth(queue: Queue): Promise<void> {
  const waiting = await queue.getWaitingCount();
  const active = await queue.getActiveCount();

  if (waiting > 10_000) {
    logger.warn({ waiting, active }, "Queue depth exceeds threshold");
    // Trigger alert
  }
}
```

Python (rq):

```python
from rq import Worker

# rq workers process one job at a time by default.
# Scale horizontally by running multiple worker processes.

# Monitor queue depth
def check_queue_health(queue: Queue) -> None:
    depth = len(queue)
    if depth > 10_000:
        logger.warning(f"Queue depth exceeds threshold: {depth}")
```

NEVER:
- Buffer indefinitely — memory will eventually exhaust
- Set concurrency higher than the downstream can handle
- Ignore growing queue depth (it signals a problem — slow consumer, broken dependency, or traffic spike)

## Schema evolution

- Adding fields is always safe (backward compatible)
- Consumers must tolerate unknown fields (forward compatible) — never fail on extra fields
- Removing or renaming a field requires a version bump in `metadata.version`
- When introducing a breaking change: publish both old and new versions during a transition period, then deprecate the old version
- Consumer reads `metadata.version` and dispatches to the appropriate handler

TypeScript:

```typescript
async function handleEvent(event: EventEnvelope): Promise<void> {
  switch (event.metadata.version) {
    case 1:
      return handleOrderCompletedV1(event.payload as OrderCompletedV1);
    case 2:
      return handleOrderCompletedV2(event.payload as OrderCompletedV2);
    default:
      logger.warn({ version: event.metadata.version, type: event.type }, "Unknown event version");
      // Tolerate unknown versions — log and skip, don't crash
  }
}
```

Python:

```python
def handle_event(event: dict) -> None:
    version = event["metadata"]["version"]

    handlers = {
        1: handle_order_completed_v1,
        2: handle_order_completed_v2,
    }

    handler = handlers.get(version)
    if handler:
        handler(event["payload"])
    else:
        logger.warning(f"Unknown event version {version} for {event['type']}")
```

NEVER:
- Remove or rename a field without bumping the version number
- Assume all consumers will update simultaneously (they won't)
- Fail hard on unknown fields — deserializers must ignore extras
- Change the meaning of an existing field (add a new field instead)
