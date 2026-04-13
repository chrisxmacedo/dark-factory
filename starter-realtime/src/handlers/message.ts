import { logger } from "../lib/logger";
import {
  type ClientConnection,
  joinRoom,
  leaveRoom,
  publishToRoom,
  getRoomMembers,
} from "../rooms/manager";
import { getRoomPresence } from "../rooms/presence";

/**
 * Expected shape of every incoming client message.
 */
interface ClientMessage {
  type: string;
  payload?: Record<string, unknown>;
}

/**
 * Validate that raw data parses as a valid client message.
 */
function parseMessage(data: string): ClientMessage | null {
  try {
    const parsed = JSON.parse(data) as unknown;

    if (
      typeof parsed !== "object" ||
      parsed === null ||
      !("type" in parsed) ||
      typeof (parsed as Record<string, unknown>).type !== "string"
    ) {
      return null;
    }

    return parsed as ClientMessage;
  } catch {
    return null;
  }
}

/**
 * Handle an incoming WebSocket message from a client.
 * Validates the schema and routes to the appropriate action.
 */
export async function handleMessage(conn: ClientConnection, raw: string): Promise<void> {
  const msg = parseMessage(raw);

  if (!msg) {
    logger.warn({ connId: conn.connId }, "Malformed message received");
    conn.ws.send(JSON.stringify({ type: "error", payload: { message: "Invalid message format" } }));
    return;
  }

  switch (msg.type) {
    case "join": {
      const roomId = msg.payload?.roomId;
      if (typeof roomId !== "string" || roomId.length === 0) {
        conn.ws.send(JSON.stringify({ type: "error", payload: { message: "Missing roomId" } }));
        return;
      }
      joinRoom(conn, roomId);
      conn.ws.send(JSON.stringify({ type: "joined", payload: { roomId } }));
      break;
    }

    case "leave": {
      const roomId = msg.payload?.roomId;
      if (typeof roomId !== "string" || roomId.length === 0) {
        conn.ws.send(JSON.stringify({ type: "error", payload: { message: "Missing roomId" } }));
        return;
      }
      leaveRoom(conn, roomId);
      conn.ws.send(JSON.stringify({ type: "left", payload: { roomId } }));
      break;
    }

    case "broadcast": {
      const roomId = msg.payload?.roomId;
      const data = msg.payload?.data;
      if (typeof roomId !== "string" || roomId.length === 0) {
        conn.ws.send(JSON.stringify({ type: "error", payload: { message: "Missing roomId" } }));
        return;
      }
      if (!conn.rooms.has(roomId)) {
        conn.ws.send(JSON.stringify({ type: "error", payload: { message: "Not in room" } }));
        return;
      }

      const outbound = JSON.stringify({
        type: "message",
        payload: { roomId, userId: conn.userId, data },
      });

      // Publish to Redis so all instances (including this one) deliver it
      await publishToRoom(roomId, outbound);
      break;
    }

    case "presence": {
      const roomId = msg.payload?.roomId;
      if (typeof roomId !== "string" || roomId.length === 0) {
        conn.ws.send(JSON.stringify({ type: "error", payload: { message: "Missing roomId" } }));
        return;
      }
      const members = await getRoomPresence(roomId);
      conn.ws.send(JSON.stringify({ type: "presence:list", payload: { roomId, members } }));
      break;
    }

    default:
      logger.warn({ connId: conn.connId, type: msg.type }, "Unknown message type");
      conn.ws.send(JSON.stringify({ type: "error", payload: { message: `Unknown type: ${msg.type}` } }));
  }
}
