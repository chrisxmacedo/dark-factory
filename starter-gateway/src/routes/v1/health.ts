import { Router, type Request, type Response } from "express";
import { logger } from "../../lib/logger";

export const healthRouter = Router();

/**
 * Downstream service health check definition.
 * Add one entry per internal service the gateway depends on.
 */
interface ServiceCheck {
  name: string;
  url: string;
  critical: boolean;
}

// {DOWNSTREAM_SERVICES} — add your internal services here
const SERVICES: ServiceCheck[] = [
  // { name: "user-service", url: "http://user-service:8080/health", critical: true },
  // { name: "order-service", url: "http://order-service:8080/health", critical: true },
  // { name: "notification-service", url: "http://notification-service:8080/health", critical: false },
];

interface ServiceStatus {
  name: string;
  status: "healthy" | "unhealthy";
  latency_ms: number;
  critical: boolean;
  error?: string;
}

async function checkService(service: ServiceCheck): Promise<ServiceStatus> {
  const start = Date.now();
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3_000);

    const response = await fetch(service.url, { signal: controller.signal });
    clearTimeout(timeout);

    const latency = Date.now() - start;
    return {
      name: service.name,
      status: response.ok ? "healthy" : "unhealthy",
      latency_ms: latency,
      critical: service.critical,
      error: response.ok ? undefined : `HTTP ${response.status}`,
    };
  } catch (err) {
    return {
      name: service.name,
      status: "unhealthy",
      latency_ms: Date.now() - start,
      critical: service.critical,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

healthRouter.get("/", async (req: Request, res: Response): Promise<void> => {
  const results = await Promise.all(SERVICES.map(checkService));

  const criticalDown = results.some(
    (r) => r.critical && r.status === "unhealthy"
  );
  const overallStatus = criticalDown ? "unhealthy" : "healthy";
  const httpStatus = criticalDown ? 503 : 200;

  if (criticalDown) {
    logger.warn(
      { request_id: req.requestId, services: results },
      "Health check: critical service(s) down"
    );
  }

  res.status(httpStatus).json({
    data: {
      status: overallStatus,
      services: results,
    },
    meta: { request_id: req.requestId },
  });
});
