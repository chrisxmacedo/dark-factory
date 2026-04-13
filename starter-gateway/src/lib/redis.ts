import Redis from "ioredis";
import { config } from "../config";
import { logger } from "./logger";

export const redis = new Redis(config.redisUrl, {
  maxRetriesPerRequest: 3,
  lazyConnect: false,
  enableReadyCheck: true,
  retryStrategy(times: number): number | null {
    if (times > 10) {
      logger.error("Redis: max reconnection attempts reached");
      return null; // stop retrying
    }
    return Math.min(times * 200, 5_000);
  },
});

redis.on("connect", () => {
  logger.info("Redis connected");
});

redis.on("error", (err: Error) => {
  logger.error({ err }, "Redis error");
});
