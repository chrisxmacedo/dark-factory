import Redis from "ioredis";

const globalForRedis = globalThis as unknown as {
  redis: Redis | undefined;
};

function createRedisClient(): Redis {
  const url = process.env.REDIS_URL;
  if (!url) {
    throw new Error("REDIS_URL environment variable is not set");
  }

  return new Redis(url, {
    maxRetriesPerRequest: 3,
    retryStrategy(times) {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    lazyConnect: true,
  });
}

/**
 * Get the Redis client singleton.
 * Lazily created on first access to avoid errors during Next.js build.
 */
export function getRedis(): Redis {
  if (!globalForRedis.redis) {
    globalForRedis.redis = createRedisClient();
  }
  return globalForRedis.redis;
}

export default getRedis;
