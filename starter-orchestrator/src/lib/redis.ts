import Redis from "ioredis";
import { logger } from "./logger";

const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";

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
