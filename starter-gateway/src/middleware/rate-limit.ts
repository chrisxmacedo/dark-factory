import type { Request, Response, NextFunction } from "express";
import { redis } from "../lib/redis";
import { config } from "../config";
import { logger } from "../lib/logger";

/**
 * Redis-backed sliding window rate limiter.
 * Limits by user ID (authenticated) or IP (anonymous).
 */
export async function rateLimitMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const userId = req.user?.sub;
  const identifier = userId ? `user:${userId}` : `ip:${req.ip ?? "unknown"}`;
  const maxRequests = userId
    ? config.rateLimitMaxAuthenticated
    : config.rateLimitMaxAnonymous;
  const windowMs = config.rateLimitWindowMs;
  const key = `ratelimit:${identifier}`;

  try {
    const now = Date.now();
    const windowStart = now - windowMs;

    // Sliding window: remove expired entries, add current, count total
    const pipeline = redis.pipeline();
    pipeline.zremrangebyscore(key, 0, windowStart);
    pipeline.zadd(key, now, `${now}:${Math.random()}`);
    pipeline.zcard(key);
    pipeline.pexpire(key, windowMs);

    const results = await pipeline.exec();
    const count = (results?.[2]?.[1] as number) ?? 0;

    // Set rate limit headers on every response
    const remaining = Math.max(0, maxRequests - count);
    const resetAt = Math.ceil((now + windowMs) / 1000);

    res.set("X-RateLimit-Limit", String(maxRequests));
    res.set("X-RateLimit-Remaining", String(remaining));
    res.set("X-RateLimit-Reset", String(resetAt));

    if (count > maxRequests) {
      res.status(429).json({
        error: { code: "rate_limited", message: "Too many requests" },
      });
      return;
    }

    next();
  } catch (err) {
    // If Redis is down, allow the request but log the error.
    // Failing open prevents total outage when Redis is unavailable.
    logger.error({ err, key }, "Rate limit check failed — allowing request");
    next();
  }
}
