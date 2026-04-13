import { redis, redisPub } from "../lib/redis";
import { logger } from "../lib/logger";
import { broadcastToRoom } from "./manager";

const PRESENCE_TTL_SECONDS = 120;

/**
 * Record a user as present in a room. Uses a Redis sorted set with
 * the current timestamp as the score for expiry detection.
 */
export async function setPresence(userId: string, roomId: string): Promise<void> {
  const key = `presence:${roomId}`;
  const now = Date.now();
  await redis.zadd(key, now.toString(), userId);
  await redis.expire(key, PRESENCE_TTL_SECONDS);
}

/**
 * Remove a user from a room's presence set.
 */
export async function removePresence(userId: string, roomId: string): Promise<void> {
  const key = `presence:${roomId}`;
  await redis.zrem(key, userId);
}

/**
 * Get all users currently present in a room.
 */
export async function getRoomPresence(roomId: string): Promise<string[]> {
  const key = `presence:${roomId}`;
  return redis.zrange(key, 0, -1);
}

/**
 * Remove stale presence entries older than the TTL.
 */
export async function cleanStalePresence(roomId: string): Promise<void> {
  const key = `presence:${roomId}`;
  const cutoff = Date.now() - PRESENCE_TTL_SECONDS * 1000;
  const removed = await redis.zremrangebyscore(key, 0, cutoff);
  if (removed > 0) {
    logger.info({ roomId, removed }, "Cleaned stale presence entries");
  }
}

/**
 * Refresh a user's presence timestamp (called on heartbeat).
 */
export async function refreshPresence(userId: string, roomId: string): Promise<void> {
  const key = `presence:${roomId}`;
  const now = Date.now();
  await redis.zadd(key, now.toString(), userId);
}

/**
 * Broadcast a presence:join event to room members and publish via Redis.
 */
export function broadcastPresenceJoin(userId: string, roomId: string): void {
  const message = JSON.stringify({
    type: "presence:join",
    payload: { userId, roomId, timestamp: Date.now() },
  });

  broadcastToRoom(roomId, message);

  // Publish to Redis for cross-instance delivery
  redisPub.publish(`room:${roomId}`, message).catch((err) => {
    logger.error({ err, roomId, userId }, "Failed to publish presence:join");
  });

  // Update Redis presence state
  setPresence(userId, roomId).catch((err) => {
    logger.error({ err, roomId, userId }, "Failed to set presence");
  });
}

/**
 * Broadcast a presence:leave event to room members and publish via Redis.
 */
export function broadcastPresenceLeave(userId: string, roomId: string): void {
  const message = JSON.stringify({
    type: "presence:leave",
    payload: { userId, roomId, timestamp: Date.now() },
  });

  broadcastToRoom(roomId, message);

  redisPub.publish(`room:${roomId}`, message).catch((err) => {
    logger.error({ err, roomId, userId }, "Failed to publish presence:leave");
  });

  removePresence(userId, roomId).catch((err) => {
    logger.error({ err, roomId, userId }, "Failed to remove presence");
  });
}
