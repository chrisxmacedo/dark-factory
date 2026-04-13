// Initialise OpenTelemetry BEFORE any other imports
import "./lib/otel";

import { startHealthServer } from "./health";
import { prisma } from "./lib/prisma";
import { redis } from "./lib/redis";
import { logger } from "./lib/logger";

const SHUTDOWN_TIMEOUT_MS = parseInt(
  process.env.SHUTDOWN_TIMEOUT_MS ?? "30000",
  10,
);

let isShuttingDown = false;

async function main(): Promise<void> {
  logger.info("Starting worker service");

  // Connect to dependencies
  await prisma.$connect();
  logger.info("Database connected");

  // Verify Redis connectivity
  await redis.ping();
  logger.info("Redis connected");

  // Start health endpoint
  const healthServer = startHealthServer();

  // TODO: Start your consumers here
  // e.g. startExampleConsumer();

  logger.info("Worker service started");

  // Graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    if (isShuttingDown) return;
    isShuttingDown = true;
    logger.info({ signal }, "Shutdown signal received — draining");

    const forceExit = setTimeout(() => {
      logger.error("Shutdown timeout exceeded — forcing exit");
      process.exit(1);
    }, SHUTDOWN_TIMEOUT_MS);

    try {
      // TODO: Stop consumers — stop accepting new jobs, await current job

      healthServer.close();
      await redis.quit();
      await prisma.$disconnect();
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

export { isShuttingDown };

main().catch((err) => {
  logger.fatal({ err }, "Worker failed to start");
  process.exit(1);
});
