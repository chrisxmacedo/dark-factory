# Async TypeScript best practices

Read by: all teams working on TypeScript starters (web, worker, gateway, batch, notification, docs, orchestrator, realtime, audit)

## Promise fundamentals

- Always `async`/`await` — never `.then()` chains
- Every Promise must be awaited, returned, or explicitly discarded with `void`
- Use the `void` prefix when fire-and-forget is intentional:
  ```ts
  void sendAnalyticsEvent({ action: "page_view", userId });
  ```
- Never create a Promise you don't handle — unhandled rejections crash Node.js

NEVER:
- Use `.then().catch()` chains — use async/await with try/catch
- Ignore a returned Promise without `void` or `await`
- Mix `.then()` and `await` in the same function

## Error handling in async code

- Wrap `await` calls in try/catch at the boundary where you can meaningfully handle the error
- Catch at the right level — don't wrap every single await, wrap logical units of work:
  ```ts
  async function createOrder(input: OrderInput): Promise<Order> {
    try {
      const order = await prisma.order.create({ data: input });
      await sendConfirmationEmail(order);
      return order;
    } catch (error) {
      logger.error({ error, input }, "Failed to create order");
      throw new OrderError("Order creation failed", { cause: error });
    }
  }
  ```
- Register a global safety net — this should never fire in production, but prevents silent crashes:
  ```ts
  process.on("unhandledRejection", (reason, promise) => {
    logger.fatal({ reason, promise }, "Unhandled rejection — this is a bug");
    process.exit(1);
  });
  ```
- Re-throw with context — wrap caught errors in domain errors that carry the original cause

NEVER:
- Catch and ignore: `catch (e) {}` — always log or re-throw
- Let unhandled rejections crash the process silently — always register the safety net
- Catch errors you can't handle — let them propagate to a handler that can

## Concurrent operations

- Use `Promise.all()` for independent I/O that must all succeed:
  ```ts
  const [user, permissions, preferences] = await Promise.all([
    fetchUser(userId),
    fetchPermissions(userId),
    fetchPreferences(userId),
  ]);
  ```
- Use `Promise.allSettled()` when partial failure is acceptable:
  ```ts
  const results = await Promise.allSettled([
    notifySlack(event),
    notifyEmail(event),
    notifyWebhook(event),
  ]);

  const failures = results.filter(
    (r): r is PromiseRejectedResult => r.status === "rejected",
  );
  if (failures.length > 0) {
    logger.warn({ failures }, "Some notifications failed");
  }
  ```
- Use `Promise.race()` sparingly — mainly for timeout patterns
- Control concurrency for large batches — don't fire 10,000 Promises at once:
  ```ts
  // Process in batches of 50
  for (let i = 0; i < items.length; i += 50) {
    const batch = items.slice(i, i + 50);
    await Promise.all(batch.map((item) => processItem(item)));
  }
  ```

NEVER:
- Await independent operations sequentially — use `Promise.all()`:
  ```ts
  // BAD — sequential, 2x slower
  const user = await fetchUser(id);
  const prefs = await fetchPreferences(id);

  // GOOD — concurrent
  const [user, prefs] = await Promise.all([
    fetchUser(id),
    fetchPreferences(id),
  ]);
  ```
- Fire unbounded concurrent Promises — always limit batch size
- Use `Promise.all()` when you need partial results on failure — use `Promise.allSettled()`

## Timeouts

- Every external call MUST have a timeout — no exceptions
- Use `AbortController` for cancellable operations:
  ```ts
  async function fetchWithTimeout(
    url: string,
    timeoutMs: number,
  ): Promise<Response> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
      return await fetch(url, { signal: controller.signal });
    } finally {
      clearTimeout(timeout);
    }
  }
  ```
- Standard timeouts:
  - **HTTP requests**: 10s default, 5s for health checks
  - **Redis operations**: 5s
  - **Database queries**: 10s (set in Prisma connection string or query options)
  - **Long-running jobs**: 30s default, configurable per job type
  - **WebSocket heartbeat**: 30s interval, disconnect after 3 missed pongs
- Always clean up the timer in `finally` — leaked timers prevent graceful shutdown

NEVER:
- Make an external call without a timeout
- Set timeout to 0 or Infinity
- Catch timeout errors and retry without backoff (see resilience.md)

## Stream processing

- Use async iterators for large datasets — process row by row, not all at once:
  ```ts
  async function processLargeExport(cursor: AsyncIterable<Row>): Promise<void> {
    for await (const row of cursor) {
      await writeToOutput(row);
    }
  }
  ```
- Handle backpressure — if the consumer is slower than the producer, pause the source:
  ```ts
  import { pipeline } from "node:stream/promises";

  await pipeline(readableStream, transformStream, writableStream);
  ```
- Use `node:stream/promises` `pipeline()` — it handles error propagation and cleanup
- For HTTP response streams, check `res.writableEnded` before writing

NEVER:
- Load an entire stream into memory: `const all = await stream.toArray()`
- Ignore stream errors — always handle `"error"` events or use `pipeline()`
- Create streams without a cleanup path — leaked streams leak file descriptors and memory

## Worker patterns

- Keep the event loop healthy — no synchronous work over 10ms:
  ```ts
  // Check event loop lag
  const start = performance.now();
  setImmediate(() => {
    const lag = performance.now() - start;
    if (lag > 100) {
      logger.warn({ lagMs: lag }, "Event loop lag detected");
    }
  });
  ```
- Use `worker_threads` for CPU-bound work (image processing, compression, hashing):
  ```ts
  import { Worker } from "node:worker_threads";

  function runInWorker<T>(script: string, data: unknown): Promise<T> {
    return new Promise((resolve, reject) => {
      const worker = new Worker(script, { workerData: data });
      worker.on("message", resolve);
      worker.on("error", reject);
    });
  }
  ```
- Graceful shutdown — drain in-flight work before exiting:
  ```ts
  let isShuttingDown = false;

  async function shutdown(signal: string): Promise<void> {
    logger.info({ signal }, "Shutdown signal received");
    isShuttingDown = true;

    // Stop accepting new work
    server.close();

    // Wait for in-flight work to complete (max 30s)
    await drainInFlight({ timeoutMs: 30_000 });

    // Close connections
    await prisma.$disconnect();
    await redis.quit();

    process.exit(0);
  }

  process.on("SIGTERM", () => void shutdown("SIGTERM"));
  process.on("SIGINT", () => void shutdown("SIGINT"));
  ```
- Check `isShuttingDown` before starting new work in queue consumers

NEVER:
- Block the event loop with synchronous computation — use worker_threads
- Call `process.exit()` without draining in-flight work
- Start new work after receiving a shutdown signal
- Ignore SIGTERM — Kubernetes sends it before SIGKILL (30s grace period)

## Database async

- All Prisma operations are async — always `await` them:
  ```ts
  // Every query must be awaited
  const user = await prisma.user.findUnique({ where: { id } });
  ```
- Use `$transaction()` for multi-step writes:
  ```ts
  const [order, payment] = await prisma.$transaction(async (tx) => {
    const order = await tx.order.create({ data: orderData });
    const payment = await tx.payment.create({
      data: { ...paymentData, orderId: order.id },
    });
    return [order, payment] as const;
  });
  ```
- Un-awaited queries silently check out a connection and never return it — this exhausts the pool
- Keep transactions short — do validation and external calls BEFORE entering the transaction
- Set query timeouts in the connection string: `?connect_timeout=10&pool_timeout=10`

NEVER:
- Forget to `await` a Prisma call — the query fires but the connection never returns to the pool
- Call external APIs inside a `$transaction()` — holds a DB connection while waiting on the network
- Open multiple transactions concurrently from the same request — deadlock risk

## Testing async code

- Mark test functions as `async` and `await` the code under test:
  ```ts
  it("creates an order", async () => {
    const order = await createOrder(validInput);
    expect(order.status).toBe("pending");
  });
  ```
- Test rejections with `.rejects`:
  ```ts
  await expect(createOrder(invalidInput)).rejects.toThrow(OrderError);
  ```
- Clean up async resources in `afterEach` / `afterAll`:
  ```ts
  afterAll(async () => {
    await prisma.$disconnect();
    await redis.quit();
  });
  ```
- Use `jest.useFakeTimers()` for timeout-dependent tests — but call `jest.useRealTimers()` in afterEach
- For tests with concurrent operations, ensure test isolation — parallel tests sharing mutable state will flake

NEVER:
- Forget `await` in tests — the test passes before the assertion runs
- Leave async resources open after tests — leaked connections cause test hangs
- Use real timers in tests that verify timeout behaviour — tests become slow and flaky
- Ignore `act()` warnings in React async tests — they indicate a real timing bug
