import { createApp } from "./app";
import { config } from "./config";
import { logger } from "./lib/logger";
import { redis } from "./lib/redis";

const app = createApp();

const server = app.listen(config.port, () => {
  logger.info({ port: config.port, env: config.nodeEnv }, "Gateway started");
});

// --- Graceful shutdown ---
function shutdown(signal: string): void {
  logger.info({ signal }, "Shutdown signal received");
  server.close(() => {
    redis
      .quit()
      .then(() => {
        logger.info("Shutdown complete");
        process.exit(0);
      })
      .catch((err: unknown) => {
        logger.error({ err }, "Error during shutdown");
        process.exit(1);
      });
  });
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
