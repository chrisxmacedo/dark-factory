import http from "node:http";
import { prisma } from "./lib/prisma";
import { redis } from "./lib/redis";
import { logger } from "./lib/logger";
import { emailCircuitBreaker } from "./channels/email";
import { smsCircuitBreaker } from "./channels/sms";
import { pushCircuitBreaker } from "./channels/push";
import { isShuttingDown } from "./index";

const HEALTH_PORT = parseInt(process.env.HEALTH_PORT ?? "8080", 10);

interface HealthCheck {
  status: "ok" | "unhealthy";
  checks: {
    database: "ok" | "fail";
    redis: "ok" | "fail";
    channels: {
      email: string;
      sms: string;
      push: string;
    };
    shutting_down: boolean;
  };
}

async function checkHealth(): Promise<HealthCheck> {
  const checks: HealthCheck["checks"] = {
    database: "fail",
    redis: "fail",
    channels: {
      email: emailCircuitBreaker.getState(),
      sms: smsCircuitBreaker.getState(),
      push: pushCircuitBreaker.getState(),
    },
    shutting_down: isShuttingDown,
  };

  try {
    await prisma.$queryRaw`SELECT 1`;
    checks.database = "ok";
  } catch {
    // database check failed
  }

  try {
    await redis.ping();
    checks.redis = "ok";
  } catch {
    // redis check failed
  }

  const allOk =
    checks.database === "ok" && checks.redis === "ok" && !isShuttingDown;

  return {
    status: allOk ? "ok" : "unhealthy",
    checks,
  };
}

export function startHealthServer(): http.Server {
  const server = http.createServer(async (_req, res) => {
    if (_req.url !== "/healthz") {
      res.writeHead(404);
      res.end();
      return;
    }

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
  });

  server.listen(HEALTH_PORT, () => {
    logger.info({ port: HEALTH_PORT }, "Health server listening");
  });

  return server;
}
