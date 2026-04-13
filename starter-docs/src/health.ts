import type { IncomingMessage, ServerResponse } from "node:http";
import { prisma } from "./lib/prisma";
import { checkS3Connectivity } from "./storage/s3";
import { logger } from "./lib/logger";
import { isShuttingDown } from "./index";

interface HealthCheck {
  status: "ok" | "unhealthy";
  checks: {
    database: "ok" | "fail";
    s3: "ok" | "fail";
    shutting_down: boolean;
  };
}

async function checkHealth(): Promise<HealthCheck> {
  const checks: HealthCheck["checks"] = {
    database: "fail",
    s3: "fail",
    shutting_down: isShuttingDown,
  };

  try {
    await prisma.$queryRaw`SELECT 1`;
    checks.database = "ok";
  } catch {
    // database check failed
  }

  try {
    const s3Ok = await checkS3Connectivity();
    checks.s3 = s3Ok ? "ok" : "fail";
  } catch {
    // s3 check failed
  }

  const allOk =
    checks.database === "ok" && checks.s3 === "ok" && !isShuttingDown;

  return {
    status: allOk ? "ok" : "unhealthy",
    checks,
  };
}

export async function handleHealthCheck(
  _req: IncomingMessage,
  res: ServerResponse,
): Promise<void> {
  try {
    const health = await checkHealth();
    const statusCode = health.status === "ok" ? 200 : 503;
    res.writeHead(statusCode, { "Content-Type": "application/json" });
    res.end(JSON.stringify(health));
  } catch (err) {
    logger.error({ err }, "Health check error");
    res.writeHead(503, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "unhealthy" }));
  }
}
