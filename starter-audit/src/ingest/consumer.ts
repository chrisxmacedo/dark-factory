import { redis } from "../lib/redis";
import { prisma } from "../lib/prisma";
import { logger, createEventLogger } from "../lib/logger";
import { auditEventInputSchema } from "./schema";
import { computeEventHash } from "./hash-chain";

const QUEUE_NAME =
  process.env.AUDIT_QUEUE_NAME ?? "{project-name}:audit-events";
const POLL_INTERVAL_MS = parseInt(process.env.POLL_INTERVAL_MS ?? "1000", 10);

let running = false;

/**
 * Start consuming audit events from the Redis queue.
 * Events are validated, hash-chained, and stored in the append-only log.
 */
export function startConsumer(): void {
  running = true;
  logger.info({ queue: QUEUE_NAME }, "Audit event consumer started");
  void pollLoop();
}

/**
 * Stop the consumer gracefully. Finishes processing the current event.
 */
export function stopConsumer(): void {
  running = false;
  logger.info("Audit event consumer stopping");
}

async function pollLoop(): Promise<void> {
  while (running) {
    try {
      // BRPOP blocks until an item is available or timeout expires
      const result = await redis.brpop(QUEUE_NAME, 1);

      if (!result) {
        continue;
      }

      const [, rawPayload] = result;
      await processEvent(rawPayload);
    } catch (err) {
      logger.error({ err }, "Error in consumer poll loop");
      // Back off before retrying on error
      await sleep(POLL_INTERVAL_MS);
    }
  }
}

async function processEvent(rawPayload: string): Promise<void> {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawPayload);
  } catch {
    logger.warn({ rawPayload }, "Malformed JSON — event rejected");
    return;
  }

  const validation = auditEventInputSchema.safeParse(parsed);
  if (!validation.success) {
    logger.warn(
      { errors: validation.error.issues, rawPayload },
      "Invalid audit event schema — event rejected",
    );
    return;
  }

  const eventInput = validation.data;
  const eventLogger = createEventLogger(eventInput.id, eventInput.actor);

  // Fetch the hash of the most recent stored event for chain continuity
  // TODO: Replace with actual Prisma query against your audit_events table
  const lastEvent = await prisma.$queryRaw<
    Array<{ hash: string }>
  >`SELECT hash FROM {AUDIT_EVENTS_TABLE} ORDER BY timestamp DESC LIMIT 1`;

  const previousHash = lastEvent.length > 0 ? lastEvent[0].hash : null;
  const { hash, previousHash: prevHash } = computeEventHash(
    eventInput,
    previousHash,
  );

  // APPEND ONLY — INSERT, never UPDATE or DELETE
  // TODO: Replace with actual Prisma create against your audit_events table
  await prisma.$executeRaw`
    INSERT INTO {AUDIT_EVENTS_TABLE} (
      id, timestamp, actor, action, resource, context, outcome,
      metadata, previous_hash, hash
    ) VALUES (
      ${eventInput.id}, ${eventInput.timestamp}, ${eventInput.actor},
      ${eventInput.action}, ${eventInput.resource}, ${eventInput.context},
      ${eventInput.outcome}, ${JSON.stringify(eventInput.metadata)},
      ${prevHash}, ${hash}
    )
  `;

  eventLogger.info({ action: eventInput.action }, "Audit event ingested");
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
