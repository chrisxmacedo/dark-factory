import type WebSocket from "ws";
import { logger } from "../lib/logger";
import { redisPub } from "../lib/redis";
import { broadcastPresenceJoin, broadcastPresenceLeave } from "./presence";

export interface ClientConnection {
  ws: WebSocket;
  connId: string;
  userId: string;
  rooms: Set<string>;
}

/**
 * In-memory map of room ID -> set of connections in that room.
 * Each instance tracks only its own local connections. Redis pub/sub
 * distributes events across instances.
 */
const rooms = new Map<string, Set<ClientConnection>>();

/**
 * All active connections indexed by connId.
 */
const connections = new Map<string, ClientConnection>();

const MAX_BUFFERED_AMOUNT = parseInt(
  process.env.MAX_BUFFERED_AMOUNT ?? "65536",
  10,
);

export function registerConnection(conn: ClientConnection): void {
  connections.set(conn.connId, conn);
  logger.info({ connId: conn.connId, userId: conn.userId }, "Connection registered");
}

export function removeConnection(connId: string): void {
  const conn = connections.get(connId);
  if (!conn) return;

  // Leave all rooms
  for (const roomId of conn.rooms) {
    leaveRoom(conn, roomId);
  }

  connections.delete(connId);
  logger.info({ connId }, "Connection removed");
}

export function joinRoom(conn: ClientConnection, roomId: string): void {
  if (conn.rooms.has(roomId)) return;

  if (!rooms.has(roomId)) {
    rooms.set(roomId, new Set());
  }

  rooms.get(roomId)!.add(conn);
  conn.rooms.add(roomId);

  logger.info({ connId: conn.connId, userId: conn.userId, roomId }, "Joined room");

  // Broadcast presence join to room members and publish to Redis for other instances
  broadcastPresenceJoin(conn.userId, roomId);
}

export function leaveRoom(conn: ClientConnection, roomId: string): void {
  if (!conn.rooms.has(roomId)) return;

  const roomConns = rooms.get(roomId);
  if (roomConns) {
    roomConns.delete(conn);
    if (roomConns.size === 0) {
      rooms.delete(roomId);
    }
  }

  conn.rooms.delete(roomId);

  logger.info({ connId: conn.connId, userId: conn.userId, roomId }, "Left room");

  // Broadcast presence leave
  broadcastPresenceLeave(conn.userId, roomId);
}

/**
 * Broadcast a message to all local connections in a room.
 * Applies backpressure — drops messages for clients that cannot keep up.
 */
export function broadcastToRoom(roomId: string, message: string, excludeConnId?: string): void {
  const roomConns = rooms.get(roomId);
  if (!roomConns) return;

  for (const conn of roomConns) {
    if (excludeConnId && conn.connId === excludeConnId) continue;

    if (conn.ws.bufferedAmount > MAX_BUFFERED_AMOUNT) {
      logger.warn(
        { connId: conn.connId, userId: conn.userId, roomId, buffered: conn.ws.bufferedAmount },
        "Dropping message — client backpressure",
      );
      continue;
    }

    conn.ws.send(message);
  }
}

/**
 * Publish a message to a room via Redis so all instances deliver it.
 */
export async function publishToRoom(roomId: string, message: string): Promise<void> {
  await redisPub.publish(`room:${roomId}`, message);
}

export function getConnectionCount(): number {
  return connections.size;
}

export function getRoomCount(): number {
  return rooms.size;
}

export function getRoomMembers(roomId: string): string[] {
  const roomConns = rooms.get(roomId);
  if (!roomConns) return [];
  return Array.from(roomConns).map((c) => c.userId);
}

export function getConnection(connId: string): ClientConnection | undefined {
  return connections.get(connId);
}
