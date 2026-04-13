import http from "node:http";
import { redis } from "./lib/redis";
import { logger } from "./lib/logger";
import { getConnectionCount, getRoomCount } from "./rooms/manager";
import { isShuttingDown } from "./index";

interface HealthCheck {
  status: "ok" | "unhealthy";
  checks: {
    redis: "ok" | "fail";
    shutting_down: boolean;
  };
  stats: {
    connections: number;
    rooms: number;
  };
}

async function checkHealth(): Promise<HealthCheck> {
  const checks: HealthCheck["checks"] = {
    redis: "fail",
    shutting_down: isShuttingDown,
  };

  try {
    await redis.ping();
    checks.redis = "ok";
  } catch {
    // redis check failed
  }

  const stats = {
    connections: getConnectionCount(),
    rooms: getRoomCount(),
  };

  const allOk = checks.redis === "ok" && !isShuttingDown;

  return {
    status: allOk ? "ok" : "unhealthy",
    checks,
    stats,
  };
}

/**
 * Register the /healthz handler on an existing HTTP server.
 */
export function registerHealthHandler(server: http.Server): void {
  server.on("request", async (req, res) => {
    if (req.url !== "/healthz") {
      // Let other handlers deal with non-health requests (e.g. SSE)
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
}
