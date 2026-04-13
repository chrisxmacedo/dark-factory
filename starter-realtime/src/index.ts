// Initialise OpenTelemetry BEFORE any other imports
import "./lib/otel";

import { createServer } from "./server";
import { registerHealthHandler } from "./health";
import { redis, redisSub, redisPub } from "./lib/redis";
import { broadcastToRoom } from "./rooms/manager";
import { logger } from "./lib/logger";

const PORT = parseInt(process.env.PORT ?? "8080", 10);
const SHUTDOWN_TIMEOUT_MS = parseInt(
  process.env.SHUTDOWN_TIMEOUT_MS ?? "30000",
  10,
);

export let isShuttingDown = false;

async function main(): Promise<void> {
  logger.info("Starting realtime service");

  // Connect to Redis instances
  await redis.connect();
  logger.info("Redis connected");

  await redisSub.connect();
  logger.info("Redis subscriber connected");

  await redisPub.connect();
  logger.info("Redis publisher connected");

  // Create HTTP + WebSocket server
  const { httpServer, wss } = createServer();

  // Register health endpoint on the same HTTP server
  registerHealthHandler(httpServer);

  // Subscribe to Redis messages and broadcast to local room connections.
  // When another instance publishes to a room channel, this instance
  // delivers the message to its local connections in that room.
  redisSub.on("message", (channel: string, message: string) => {
    // Channels are formatted as "room:{roomId}"
    const roomId = channel.replace(/^room:/, "");
    broadcastToRoom(roomId, message);
  });

  // Subscribe to room channels as rooms are created.
  // For simplicity, use pattern subscription to catch all room channels.
  await redisSub.psubscribe("room:*");
  logger.info("Subscribed to room:* channels");

  // Start listening
  httpServer.listen(PORT, () => {
    logger.info({ port: PORT }, "Realtime service listening");
  });

  // Graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    if (isShuttingDown) return;
    isShuttingDown = true;
    logger.info({ signal }, "Shutdown signal received — draining connections");

    const forceExit = setTimeout(() => {
      logger.error("Shutdown timeout exceeded — forcing exit");
      process.exit(1);
    }, SHUTDOWN_TIMEOUT_MS);

    try {
      // Close WebSocket server — stops accepting new connections
      wss.close();

      // Send close frame to all connected clients
      for (const client of wss.clients) {
        client.close(1001, "Server shutting down");
      }

      // Unsubscribe and close Redis connections
      await redisSub.punsubscribe("room:*");
      await redisSub.quit();
      await redisPub.quit();
      await redis.quit();

      // Close HTTP server
      httpServer.close();

      logger.info("Shutdown complete");
      clearTimeout(forceExit);
      process.exit(0);
    } catch (err) {
      logger.error({ err }, "Error during shutdown");
      clearTimeout(forceExit);
      process.exit(1);
    }
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

main().catch((err) => {
  logger.fatal({ err }, "Realtime service failed to start");
  process.exit(1);
});
