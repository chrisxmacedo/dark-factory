# Performance best practices

Read by: all teams. Cross-cutting concerns for database queries, caching, HTTP responses, builds, workers, and monitoring.

## Database query optimisation

### Avoid N+1 queries

Use eager loading to fetch related data in a single query. See database.md for full examples.

```typescript
// Prisma -- include or select related data
const orders = await prisma.order.findMany({
  include: { items: true, customer: true },
});

// Select only needed fields to reduce payload
const orders = await prisma.order.findMany({
  select: {
    id: true,
    status: true,
    items: { select: { id: true, productId: true, quantity: true } },
  },
});
```

```python
# SQLAlchemy -- joinedload for small relations, subqueryload for large
from sqlalchemy.orm import joinedload, subqueryload

stmt = (
    select(Order)
    .options(joinedload(Order.customer))
    .options(subqueryload(Order.items))
)
orders = (await session.execute(stmt)).unique().scalars().all()
```

### Add indexes on filtered and sorted columns

```prisma
model Order {
  status    String
  createdAt DateTime @default(now())
  userId    String

  @@index([status])
  @@index([userId, createdAt])
}
```

```python
from sqlalchemy import Index

class Order(Base):
    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_user_created", "user_id", "created_at"),
    )
```

### Verify query plans

Run `EXPLAIN ANALYZE` on any query that touches more than a few hundred rows or runs in a hot path:

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE status = 'active' ORDER BY created_at DESC LIMIT 20;
```

Look for sequential scans on large tables, nested loops where hash joins are expected, and sort operations without index support.

### Paginate all list endpoints

Never return unbounded result sets. Every list endpoint must accept `limit` and `offset` (or cursor) parameters. See database.md for pagination patterns.

## Connection pooling

### Prisma

Configure in the connection string:

```
DATABASE_URL="postgresql://user:pass@host:5432/db?connection_limit=5&pool_timeout=30"
```

Default to `connection_limit=5` per service. For serverless, use `connection_limit=1` with PgBouncer or Prisma Accelerate.

### SQLAlchemy

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

### PgBouncer for production

Use PgBouncer in `transaction` mode between application and Postgres. This multiplexes many application connections over fewer database connections. Disable prepared statements when using PgBouncer (see database.md).

## Caching strategy

### Cache-aside pattern

The standard read path: check Redis, fall back to database on miss, populate cache.

```typescript
async function getProduct(id: string): Promise<Product> {
  const redis = getRedis();
  const key = `myapp:web:cache:product:${id}`;

  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached) as Product;

  const product = await prisma.product.findUniqueOrThrow({
    where: { id },
    include: { category: true },
  });

  // Cache the response envelope, not the raw DB row
  const envelope = { id: product.id, name: product.name, category: product.category.name };
  await redis.set(key, JSON.stringify(envelope), "EX", 3600);

  return product;
}
```

```python
import json
from myapp.redis import get_redis

async def get_product(product_id: str, session: AsyncSession) -> Product:
    r = get_redis()
    key = f"myapp:web:cache:product:{product_id}"

    cached = r.get(key)
    if cached:
        return json.loads(cached)

    stmt = select(Product).options(joinedload(Product.category)).where(Product.id == product_id)
    product = (await session.execute(stmt)).unique().scalar_one()

    envelope = {"id": str(product.id), "name": product.name, "category": product.category.name}
    r.setex(key, 3600, json.dumps(envelope))

    return product
```

### Cache invalidation on mutations

Explicitly delete cache keys when the underlying data changes. Never rely on TTL alone for consistency.

```typescript
async function updateProduct(id: string, data: UpdateProductInput): Promise<Product> {
  const product = await prisma.product.update({ where: { id }, data });
  await getRedis().del(`myapp:web:cache:product:${id}`);
  // Also invalidate list caches that include this product
  await getRedis().del("myapp:web:cache:products:featured");
  return product;
}
```

### Cache response envelopes

Cache the shaped response, not the raw database row. This avoids re-serialising on every cache hit and decouples the cache format from the database schema.

### Set TTLs on all cache keys

Every cache key must have a TTL. No exceptions. See redis.md for TTL guidelines.

## HTTP response optimisation

### ETags for conditional requests

```typescript
// Next.js API route
export async function GET(req: NextRequest) {
  const data = await getProducts();
  const etag = createHash("md5").update(JSON.stringify(data)).digest("hex");

  if (req.headers.get("if-none-match") === `"${etag}"`) {
    return new Response(null, { status: 304 });
  }

  return NextResponse.json({ data }, {
    headers: {
      ETag: `"${etag}"`,
      "Cache-Control": "private, max-age=0, must-revalidate",
    },
  });
}
```

### Cache-Control headers for static assets

```typescript
// next.config.js -- static assets
const nextConfig = {
  async headers() {
    return [
      {
        source: "/_next/static/:path*",
        headers: [{ key: "Cache-Control", value: "public, max-age=31536000, immutable" }],
      },
    ];
  },
};
```

### Compress responses

Enable gzip and brotli compression. Next.js compresses by default in production. For custom API servers:

```python
# FastAPI with gzip middleware
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Paginate collections

Every collection endpoint returns paginated results with metadata:

```json
{ "data": [...], "meta": { "total": 142, "limit": 20, "offset": 0 } }
```

## Next.js build optimisation

### Server Components by default

Server Components ship zero client JavaScript. Only add `"use client"` when the component needs browser APIs, event handlers, or React hooks.

### Dynamic imports for heavy client components

```typescript
import dynamic from "next/dynamic";

const HeavyChart = dynamic(() => import("@/components/Chart"), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

### Image component for automatic optimisation

Always use `next/image` -- it handles lazy loading, responsive sizing, and format conversion (WebP/AVIF).

```typescript
import Image from "next/image";

<Image src="/hero.jpg" alt="Hero" width={1200} height={600} priority />
```

### Static generation where possible

Use `generateStaticParams` for pages with known paths at build time. Use ISR (`revalidate`) for pages that change infrequently.

### Standalone output for Docker

```typescript
// next.config.js
const nextConfig = {
  output: "standalone",
};
```

This produces a self-contained build that doesn't need `node_modules` in the runner stage.

## Bundle size

### Tree-shake imports

```typescript
// BAD -- imports the entire library
import _ from "lodash";
_.debounce(fn, 300);

// GOOD -- imports only the function
import debounce from "lodash/debounce";
debounce(fn, 300);

// GOOD -- named imports from tree-shakeable libraries
import { format } from "date-fns";
```

### Analyse with bundle analyser

```bash
# Install
npm install --save-dev @next/bundle-analyzer

# next.config.js
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});
module.exports = withBundleAnalyzer(nextConfig);

# Run
ANALYZE=true npm run build
```

### Lazy load below-the-fold components

Use `dynamic()` with `ssr: false` for components that are not visible on initial load (modals, tabs, charts below the fold).

### Code split by route

App Router handles this automatically -- each route segment is a separate chunk. Do not import heavy page-specific dependencies in shared layouts.

## Worker throughput

### Batch processing

Process items in batches, not one at a time:

```typescript
// BAD -- one DB call per item
for (const item of items) {
  await prisma.event.update({ where: { id: item.id }, data: { processed: true } });
}

// GOOD -- batch update
await prisma.event.updateMany({
  where: { id: { in: items.map((i) => i.id) } },
  data: { processed: true },
});
```

```python
# BAD -- one query per item
for item in items:
    stmt = update(Event).where(Event.id == item.id).values(processed=True)
    await session.execute(stmt)

# GOOD -- batch update
ids = [item.id for item in items]
stmt = update(Event).where(Event.id.in_(ids)).values(processed=True)
await session.execute(stmt)
await session.commit()
```

### Connection reuse for external APIs

Reuse HTTP clients across requests. Creating a new connection per request adds TLS handshake overhead.

```typescript
// Singleton HTTP client with keep-alive
const httpClient = new undici.Pool("https://api.example.com", {
  connections: 10,
  pipelining: 1,
  keepAliveTimeout: 60_000,
});
```

```python
import httpx

# Reuse a single async client
client = httpx.AsyncClient(timeout=30, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
```

### Concurrency limits

```typescript
// BullMQ -- limit concurrent jobs to prevent resource exhaustion
const worker = new Worker("myapp:worker:sync", processFn, {
  connection,
  concurrency: 5,        // max 5 jobs running simultaneously
  limiter: {
    max: 100,            // max 100 jobs per duration
    duration: 60_000,    // per minute
  },
});
```

### Monitor event loop lag

```typescript
import { monitorEventLoopDelay } from "node:perf_hooks";

const histogram = monitorEventLoopDelay({ resolution: 20 });
histogram.enable();

// Expose in health check or metrics
function getEventLoopStats() {
  return {
    p50: histogram.percentile(50) / 1e6,  // convert ns to ms
    p99: histogram.percentile(99) / 1e6,
    max: histogram.max / 1e6,
  };
}
```

## Docker build performance

### Layer ordering

Copy dependency manifests first, install, then copy source:

```dockerfile
# 1. Dependencies (cached unless package.json changes)
COPY package.json package-lock.json ./
RUN npm ci

# 2. Source (changes frequently, doesn't bust dep cache)
COPY src/ ./src/
COPY prisma/ ./prisma/

# 3. Build
RUN npx prisma generate && npm run build
```

### Use .dockerignore

Exclude everything the build doesn't need:

```
node_modules
.git
.env*
coverage
tests
docs
*.md
.next
```

### Multi-stage builds

See docker.md for the full multi-stage pattern (deps, builder, migrate, runner).

### Cache mounts for package managers

```dockerfile
# npm cache mount -- persists across builds
RUN --mount=type=cache,target=/root/.npm npm ci

# pip cache mount
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
```

## Monitoring

### Latency tracking

Track p50, p95, and p99 latency per endpoint. Alert when p95 exceeds the endpoint's SLO.

```typescript
// Middleware to record request duration
const start = performance.now();
const response = await next(request);
const duration = performance.now() - start;

metrics.histogram("http_request_duration_ms", duration, {
  method: request.method,
  route: matchedRoute,
  status: response.status,
});
```

```python
import time

@app.middleware("http")
async def track_latency(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    metrics.histogram(
        "http_request_duration_ms",
        duration_ms,
        tags={"method": request.method, "route": request.url.path, "status": response.status_code},
    )
    return response
```

### Connection pool utilisation

Monitor active and idle connections. Alert when pool utilisation exceeds 80%.

```python
# SQLAlchemy pool stats
pool = engine.pool
metrics.gauge("db_pool_checked_out", pool.checkedout())
metrics.gauge("db_pool_checked_in", pool.checkedin())
metrics.gauge("db_pool_overflow", pool.overflow())
```

### Slow query alerting

Log and alert on queries exceeding 100ms:

```typescript
// Prisma middleware for slow query logging
prisma.$use(async (params, next) => {
  const start = performance.now();
  const result = await next(params);
  const duration = performance.now() - start;

  if (duration > 100) {
    logger.warn({ model: params.model, action: params.action, duration }, "Slow query detected");
  }

  return result;
});
```

```python
import logging
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info["query_start"] = time.perf_counter()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_execute(conn, cursor, statement, parameters, context, executemany):
    duration_ms = (time.perf_counter() - conn.info["query_start"]) * 1000
    if duration_ms > 100:
        logging.warning("Slow query (%.1fms): %s", duration_ms, statement[:200])
```

### Cache hit rate

Track cache hits and misses. A healthy cache-aside setup should see 80%+ hit rate for read-heavy data.

```typescript
const cached = await redis.get(key);
if (cached) {
  metrics.increment("cache_hit", { key_prefix: "product" });
  return JSON.parse(cached);
}
metrics.increment("cache_miss", { key_prefix: "product" });
```

### Event loop delay (Node.js)

Alert when p99 event loop delay exceeds 100ms -- it means the process is spending too much time in synchronous operations and request latency is degraded.

NEVER:
- Ship a list endpoint without pagination -- unbounded queries cause OOM and slow responses
- Open a new database connection per request -- use connection pooling
- Cache raw database rows -- cache shaped response envelopes
- Rely on TTL alone for cache consistency -- always invalidate on mutation
- Skip slow query monitoring -- a single unindexed query can take down the service
- Import entire libraries when you only need one function -- tree-shake aggressively
- Process queue items one at a time when batch operations are available
- Ignore event loop lag in Node.js workers -- synchronous bottlenecks silently degrade throughput
- Use `npm install` instead of `npm ci` in Docker builds -- it invalidates the layer cache
- Deploy without latency percentile monitoring -- averages hide tail latency problems
