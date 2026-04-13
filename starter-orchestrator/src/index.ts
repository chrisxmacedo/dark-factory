// Initialise OpenTelemetry BEFORE any other imports
import "./lib/otel";

import { startHealthServer } from "./health";
import { startApiServer } from "./api/workflows";
import { prisma } from "./lib/prisma";
import { redis } from "./lib/redis";
import { logger } from "./lib/logger";
import { registerWorkflow } from "./engine/executor";
import { exampleWorkflow } from "./workflows/example-workflow";

const SHUTDOWN_TIMEOUT_MS = parseInt(
  process.env.SHUTDOWN_TIMEOUT_MS ?? "30000",
  10,
);

let isShuttingDown = false;

async function main(): Promise<void> {
  logger.info("Starting orchestrator service");

  // Connect to dependencies
  await prisma.$connect();
  logger.info("Database connected");

  await redis.ping();
  logger.info("Redis connected");

  // Register workflow definitions
  registerWorkflow(exampleWorkflow);
  logger.info("Workflow definitions registered");

  // Start health endpoint
  const healthServer = startHealthServer();

  // Start API server (trigger, status, signal endpoints)
  const apiServer = startApiServer();

  // TODO: Start workflow trigger consumer
  // e.g. consume from Redis queue WORKFLOW_TRIGGER_QUEUE and call startWorkflow()

  logger.info("Orchestrator service started");

  // Graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    if (isShuttingDown) return;
    isShuttingDown = true;
    logger.info({ signal }, "Shutdown signal received — completing current step");

    const forceExit = setTimeout(() => {
      logger.error("Shutdown timeout exceeded — forcing exit");
      process.exit(1);
    }, SHUTDOWN_TIMEOUT_MS);

    try {
      // Stop accepting new workflows — close API server
      apiServer.close();

      // TODO: Stop workflow trigger consumer
      // TODO: Wait for current step to complete (do not start new steps)

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
  logger.fatal({ err }, "Orchestrator failed to start");
  process.exit(1);
});
