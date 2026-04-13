import Redis from "ioredis";

const CHECKPOINT_PREFIX = "batch:checkpoint:";
const CHECKPOINT_TTL_SECONDS = 86_400; // 24 hours

let redis: Redis | null = null;

function getRedis(): Redis {
  if (!redis) {
    redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");
  }
  return redis;
}

/**
 * Save a checkpoint for the given run. The checkpoint is an arbitrary
 * JSON-serialisable object that records where the job left off.
 */
export async function saveCheckpoint<T>(runId: string, data: T): Promise<void> {
  const r = getRedis();
  await r.set(
    `${CHECKPOINT_PREFIX}${runId}`,
    JSON.stringify(data),
    "EX",
    CHECKPOINT_TTL_SECONDS
  );
}

/**
 * Load the checkpoint for a run. Returns null if no checkpoint exists
 * (first run or checkpoint expired/cleared).
 */
export async function loadCheckpoint<T>(runId: string): Promise<T | null> {
  const r = getRedis();
  const raw = await r.get(`${CHECKPOINT_PREFIX}${runId}`);
  if (!raw) return null;
  return JSON.parse(raw) as T;
}

/**
 * Clear the checkpoint after a successful run. This ensures the next
 * invocation starts fresh.
 */
export async function clearCheckpoint(runId: string): Promise<void> {
  const r = getRedis();
  await r.del(`${CHECKPOINT_PREFIX}${runId}`);
}

/**
 * Disconnect Redis. Call this during shutdown.
 */
export async function disconnectCheckpointStore(): Promise<void> {
  if (redis) {
    await redis.quit();
    redis = null;
  }
}
