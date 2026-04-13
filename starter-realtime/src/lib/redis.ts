import Redis from "ioredis";
import { logger } from "./logger";

const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";

/**
 * General-purpose Redis client for presence state, room metadata, etc.
 */
export const redis = new Redis(REDIS_URL, {
  maxRetriesPerRequest: null,
  retryStrategy(times: number): number | null {
    if (times > 10) {
      logger.error("Redis retry limit reached — giving up");
      return null;
    }
    const delay = Math.min(times * 200, 5000);
    logger.warn({ attempt: times, delayMs: delay }, "Redis reconnecting");
    return delay;
  },
  lazyConnect: true,
});

redis.on("error", (err) => {
  logger.error({ err }, "Redis connection error");
});

redis.on("connect", () => {
  logger.info("Redis connected");
});

/**
 * Dedicated Redis client for pub/sub subscriptions.
 * A pub/sub client cannot run regular commands — it must be separate.
 */
export const redisSub = new Redis(REDIS_URL, {
  maxRetriesPerRequest: null,
  retryStrategy(times: number): number | null {
    if (times > 10) {
      logger.error("Redis sub retry limit reached — giving up");
      return null;
    }
    const delay = Math.min(times * 200, 5000);
    logger.warn({ attempt: times, delayMs: delay }, "Redis sub reconnecting");
    return delay;
  },
  lazyConnect: true,
});

redisSub.on("error", (err) => {
  logger.error({ err }, "Redis sub connection error");
});

redisSub.on("connect", () => {
  logger.info("Redis sub connected");
});

/**
 * Dedicated Redis client for publishing messages.
 * Kept separate for clarity — could reuse `redis` but this makes
 * the pub/sub pattern explicit.
 */
export const redisPub = new Redis(REDIS_URL, {
  maxRetriesPerRequest: null,
  retryStrategy(times: number): number | null {
    if (times > 10) {
      logger.error("Redis pub retry limit reached — giving up");
      return null;
    }
    const delay = Math.min(times * 200, 5000);
    logger.warn({ attempt: times, delayMs: delay }, "Redis pub reconnecting");
    return delay;
  },
  lazyConnect: true,
});

redisPub.on("error", (err) => {
  logger.error({ err }, "Redis pub connection error");
});

redisPub.on("connect", () => {
  logger.info("Redis pub connected");
});
