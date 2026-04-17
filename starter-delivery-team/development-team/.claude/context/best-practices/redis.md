# Redis best practices

Read by: all teams using Redis (web, worker, gateway, batch, notification, realtime, orchestrator, audit)

## Connection management

- Singleton pattern — one client instance per process, reused everywhere
- Lazy connection — don't connect on module import, connect on first use
- Reconnect strategy: exponential backoff, base 500ms, max 2s, jitter
- Health check: `PING` on the health endpoint, report connection state
- Graceful shutdown: close the Redis connection during SIGTERM handling (after in-flight work drains)

TypeScript (ioredis):

```typescript
import Redis from "ioredis";

let client: Redis | undefined;

export function getRedis(): Redis {
  if (!client) {
    const url = process.env.REDIS_URL;
    if (!url) throw new Error("REDIS_URL is not set");

    client = new Redis(url, {
      maxRetriesPerRequest: 3,
      retryStrategy(times: number): number {
        return Math.min(times * 500, 2000);
      },
      lazyConnect: true,
    });

    client.on("error", (err) => {
      logger.error({ err }, "Redis connection error");
    });
  }
  return client;
}
```

Python (redis-py):

```python
import redis
from functools import lru_cache

@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    url = os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL is not set")

    return redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
```

NEVER:
- Create a new Redis client per request
- Connect at module import time (breaks builds, tests, and cold starts)
- Swallow connection errors silently

## Key naming

- Use colons as delimiters: `{project}:{service}:{entity}:{id}`
- Always prefix with the project slug to avoid collisions in shared Redis instances
- Use consistent, lowercase names — no spaces, no special characters
- Document every key pattern in the service's README or CLAUDE.md

Examples:

```
myapp:web:session:{sessionId}
myapp:web:cache:user:{userId}
myapp:worker:rate-limit:{ip}
myapp:gateway:circuit-breaker:{service}
myapp:realtime:channel:{channelId}:members
```

NEVER:
- Use keys without a project prefix (collisions across services)
- Use dynamic user input directly in key names (injection risk — sanitise first)
- Use `KEYS *` in production (blocks Redis — use `SCAN` for iteration)

## TTL strategy

- Every cache key MUST have a TTL — no unbounded growth
- Rate limit windows: TTL matches the window (e.g. 60s for per-minute limits)
- Session data: TTL matches session max age (e.g. 30 days)
- Cache data: TTL depends on staleness tolerance (seconds for hot data, hours for stable data)
- Use `EXPIREAT` for keys that must expire at a specific wall-clock time
- Monitor memory usage — alert when approaching `maxmemory`

```typescript
// Always set TTL when writing cache
await redis.set(key, value, "EX", 3600); // 1 hour

// Never set without TTL unless the data is permanent (rare)
```

```python
redis_client.setex(key, 3600, value)  # 1 hour TTL
```

NEVER:
- Write cache keys without a TTL
- Use TTLs longer than 24 hours for cache data without explicit justification
- Rely on `maxmemory-policy` eviction as your TTL strategy

## Caching patterns

### Cache-aside (read-through)

The primary pattern — check cache first, fall back to database, populate cache on miss.

```typescript
async function getUser(userId: string): Promise<User> {
  const redis = getRedis();
  const cacheKey = `myapp:web:cache:user:${userId}`;

  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached) as User;

  const user = await prisma.user.findUniqueOrThrow({ where: { id: userId } });
  await redis.set(cacheKey, JSON.stringify(user), "EX", 3600);

  return user;
}
```

### Cache invalidation

- On mutation (create, update, delete), explicitly delete the cache key
- Never rely on TTL alone for consistency — stale reads between mutation and TTL expiry are bugs for most use cases
- For list caches, invalidate the list key when any item changes

```typescript
async function updateUser(userId: string, data: UpdateUserInput): Promise<User> {
  const user = await prisma.user.update({ where: { id: userId }, data });
  await getRedis().del(`myapp:web:cache:user:${userId}`);
  return user;
}
```

### Write-through

Write to cache and database in the same operation. Use when read latency is critical and writes are infrequent.

```typescript
async function createSession(session: Session): Promise<void> {
  await prisma.session.create({ data: session });
  await getRedis().set(
    `myapp:web:session:${session.id}`,
    JSON.stringify(session),
    "EX", 86400 * 30, // 30 days
  );
}
```

NEVER:
- Cache database query results without a clear invalidation strategy
- Use cache as the source of truth — the database is always authoritative
- Cache errors or empty results with a long TTL (cache negative results briefly or not at all)

## Rate limiting

- Sliding window with `INCR` + `EXPIRE` — simple and effective for most cases
- Apply per-user (authenticated) and per-IP (anonymous) limits
- Return `429 Too Many Requests` with `Retry-After` header when exceeded
- Log rate limit hits at `warn` level with the identifier

```typescript
async function checkRateLimit(
  identifier: string,
  limit: number,
  windowSeconds: number,
): Promise<{ allowed: boolean; remaining: number }> {
  const redis = getRedis();
  const key = `myapp:gateway:rate-limit:${identifier}`;

  const current = await redis.incr(key);
  if (current === 1) {
    await redis.expire(key, windowSeconds);
  }

  return {
    allowed: current <= limit,
    remaining: Math.max(0, limit - current),
  };
}
```

```python
def check_rate_limit(identifier: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    r = get_redis()
    key = f"myapp:gateway:rate-limit:{identifier}"

    current = r.incr(key)
    if current == 1:
        r.expire(key, window_seconds)

    remaining = max(0, limit - current)
    return current <= limit, remaining
```

NEVER:
- Implement rate limiting without Redis (in-memory counters don't work across instances)
- Use a fixed window without understanding the boundary burst problem
- Forget to set EXPIRE on the rate limit key (leaks memory)

## Pub/sub

- For real-time features: live updates, notifications, cross-service events
- Channel naming follows the key naming convention: `{project}:{service}:{event-type}`
- Serialise messages as JSON — include `type`, `payload`, and `timestamp`
- Subscribers must handle errors without crashing — log and continue
- Use separate Redis connections for pub/sub (subscribers block the connection)

```typescript
// Publisher
const redis = getRedis();
await redis.publish(
  "myapp:realtime:user-update",
  JSON.stringify({ type: "user.updated", payload: { userId }, timestamp: Date.now() }),
);

// Subscriber (separate connection)
const subscriber = new Redis(process.env.REDIS_URL!);
subscriber.subscribe("myapp:realtime:user-update");
subscriber.on("message", (channel: string, message: string) => {
  try {
    const event = JSON.parse(message);
    handleEvent(event);
  } catch (err) {
    logger.error({ err, channel, message }, "Failed to process pub/sub message");
  }
});
```

NEVER:
- Use the main Redis client for subscriptions (it becomes subscriber-only)
- Publish messages without a serialisation format (raw strings break consumers)
- Assume message delivery — pub/sub is fire-and-forget, use queues for guaranteed delivery

## Job queues

- Use BullMQ (TypeScript) or rq (Python) — built on Redis, battle-tested
- Every job type gets its own queue with its own concurrency and retry config
- Serialise job data as JSON — keep payloads small (IDs, not full objects)
- Retry: 3 attempts, exponential backoff, then move to dead-letter queue
- Log job lifecycle: started, completed, failed, moved-to-dead-letter

```typescript
import { Queue, Worker } from "bullmq";

const connection = { url: process.env.REDIS_URL };

const emailQueue = new Queue("myapp:worker:email", { connection });

// Add a job
await emailQueue.add("send-welcome", { userId: "abc123" }, {
  attempts: 3,
  backoff: { type: "exponential", delay: 1000 },
  removeOnComplete: 1000,
  removeOnFail: 5000,
});

// Process jobs
const worker = new Worker("myapp:worker:email", async (job) => {
  const { userId } = job.data;
  await sendWelcomeEmail(userId);
}, { connection, concurrency: 5 });
```

```python
from rq import Queue
from redis import Redis

q = Queue("myapp:worker:email", connection=get_redis())
q.enqueue(send_welcome_email, user_id="abc123", retry=3)
```

NEVER:
- Put large payloads in job data (fetch from DB inside the worker instead)
- Process jobs without a dead-letter strategy (failed jobs must be recoverable)
- Share a single queue for unrelated job types (one slow job type blocks others)

## Distributed locks

- For idempotency: prevent duplicate processing of the same event
- For coordination: ensure only one instance runs a scheduled task
- Use `SET key value NX EX` — atomic acquire with expiry
- Lock value must be unique per holder (UUID) — required for safe unlock
- Always set a lock TTL — prevents deadlocks if the holder crashes
- Unlock: only delete if the lock value matches (Lua script for atomicity)

```typescript
async function acquireLock(
  lockKey: string,
  ttlSeconds: number,
): Promise<string | null> {
  const redis = getRedis();
  const lockValue = crypto.randomUUID();
  const acquired = await redis.set(lockKey, lockValue, "EX", ttlSeconds, "NX");
  return acquired === "OK" ? lockValue : null;
}

async function releaseLock(lockKey: string, lockValue: string): Promise<boolean> {
  const redis = getRedis();
  // Lua script: only delete if value matches (atomic check-and-delete)
  const script = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;
  const result = await redis.eval(script, 1, lockKey, lockValue);
  return result === 1;
}
```

```python
import uuid

def acquire_lock(lock_key: str, ttl_seconds: int) -> str | None:
    r = get_redis()
    lock_value = str(uuid.uuid4())
    acquired = r.set(lock_key, lock_value, ex=ttl_seconds, nx=True)
    return lock_value if acquired else None

def release_lock(lock_key: str, lock_value: str) -> bool:
    r = get_redis()
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    return r.eval(script, 1, lock_key, lock_value) == 1
```

NEVER:
- Acquire a lock without a TTL (deadlock if holder crashes)
- Delete the lock key without checking the value (releases someone else's lock)
- Use distributed locks for high-contention, low-latency paths (use database row locks instead)
- Assume lock renewal is safe without re-checking ownership
