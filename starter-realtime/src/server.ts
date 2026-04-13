import http from "node:http";
import crypto from "node:crypto";
import { WebSocketServer, WebSocket } from "ws";
import { logger, createConnectionLogger } from "./lib/logger";
import { extractToken, validateToken, type UserContext } from "./lib/auth";
import {
  type ClientConnection,
  registerConnection,
  removeConnection,
} from "./rooms/manager";
import { handleMessage } from "./handlers/message";

const HEARTBEAT_INTERVAL_MS = parseInt(
  process.env.HEARTBEAT_INTERVAL_MS ?? "30000",
  10,
);
const HEARTBEAT_TIMEOUT_MS = parseInt(
  process.env.HEARTBEAT_TIMEOUT_MS ?? "10000",
  10,
);

interface ExtendedWebSocket extends WebSocket {
  isAlive: boolean;
  connId: string;
}

/**
 * Create an HTTP server with WebSocket upgrade support.
 * Authentication happens during the upgrade handshake.
 */
export function createServer(): { httpServer: http.Server; wss: WebSocketServer } {
  const httpServer = http.createServer();
  const wss = new WebSocketServer({ noServer: true });

  // Handle WebSocket upgrade with JWT authentication
  httpServer.on("upgrade", (req, socket, head) => {
    const token = extractToken(req.url ?? "", req.headers as Record<string, string | string[] | undefined>);

    if (!token) {
      logger.warn({ url: req.url }, "WebSocket upgrade rejected — no token");
      socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
      socket.destroy();
      return;
    }

    const user = validateToken(token);
    if (!user) {
      logger.warn({ url: req.url }, "WebSocket upgrade rejected — invalid token");
      socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
      socket.destroy();
      return;
    }

    wss.handleUpgrade(req, socket, head, (ws) => {
      wss.emit("connection", ws, user);
    });
  });

  // Handle new WebSocket connections
  wss.on("connection", (ws: WebSocket, user: UserContext) => {
    const extWs = ws as ExtendedWebSocket;
    const connId = crypto.randomUUID();
    extWs.isAlive = true;
    extWs.connId = connId;

    const connLog = createConnectionLogger(connId, user.userId);
    connLog.info("WebSocket connection established");

    const conn: ClientConnection = {
      ws,
      connId,
      userId: user.userId,
      rooms: new Set(),
    };

    registerConnection(conn);

    // Heartbeat — mark alive on pong
    extWs.on("pong", () => {
      extWs.isAlive = true;
    });

    // Incoming messages
    extWs.on("message", (data) => {
      const raw = data.toString();
      handleMessage(conn, raw).catch((err) => {
        connLog.error({ err }, "Error handling message");
      });
    });

    // Connection closed
    extWs.on("close", () => {
      connLog.info("WebSocket connection closed");
      removeConnection(connId);
    });

    // Connection error
    extWs.on("error", (err) => {
      connLog.error({ err }, "WebSocket error");
      removeConnection(connId);
    });
  });

  // Heartbeat interval — ping all clients, close dead ones
  const heartbeatInterval = setInterval(() => {
    for (const client of wss.clients) {
      const extClient = client as ExtendedWebSocket;
      if (!extClient.isAlive) {
        logger.warn({ connId: extClient.connId }, "Heartbeat timeout — terminating connection");
        removeConnection(extClient.connId);
        extClient.terminate();
        continue;
      }
      extClient.isAlive = false;
      extClient.ping();
    }
  }, HEARTBEAT_INTERVAL_MS);

  wss.on("close", () => {
    clearInterval(heartbeatInterval);
  });

  return { httpServer, wss };
}
