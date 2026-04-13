// Initialise OpenTelemetry BEFORE any other imports
import "./lib/otel";

import http from "node:http";
import { handleGenerate } from "./api/generate";
import { handleDownload, handleMetadata } from "./api/download";
import { handleHealthCheck } from "./health";
import { prisma } from "./lib/prisma";
import { redis } from "./lib/redis";
import { logger } from "./lib/logger";
import { closeBrowser } from "./generators/pdf";

const PORT = parseInt(process.env.PORT ?? "8080", 10);
const SHUTDOWN_TIMEOUT_MS = parseInt(
  process.env.SHUTDOWN_TIMEOUT_MS ?? "30000",
  10,
);

let isShuttingDown = false;

/**
 * Minimal HTTP router.
 */
function createServer(): http.Server {
  return http.createServer(async (req, res) => {
    const url = req.url ?? "";

    if (url === "/healthz") {
      return handleHealthCheck(req, res);
    }

    if (url === "/generate" && req.method === "POST") {
      return handleGenerate(req, res);
    }

    // Match /documents/:id and /documents/:id/metadata
    const downloadMatch = url.match(/^\/documents\/([^/]+)$/);
    if (downloadMatch) {
      return handleDownload(req, res, downloadMatch[1]);
    }

    const metadataMatch = url.match(/^\/documents\/([^/]+)\/metadata$/);
    if (metadataMatch) {
      return handleMetadata(req, res, metadataMatch[1]);
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Not found" }));
  });
}

async function main(): Promise<void> {
  logger.info("Starting document generation service");

  // Connect to dependencies
  await prisma.$connect();
  logger.info("Database connected");

  await redis.ping();
  logger.info("Redis connected");

  // Start HTTP server
  const server = createServer();
  server.listen(PORT, () => {
    logger.info({ port: PORT }, "API server listening");
  });

  // TODO: Optionally start queue consumer for bulk generation
  // e.g. startBulkGenerationConsumer();

  logger.info("Document generation service started");

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
      server.close();
      await closeBrowser();
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
  logger.fatal({ err }, "Document generation service failed to start");
  process.exit(1);
});
