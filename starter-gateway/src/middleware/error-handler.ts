import type { Request, Response, NextFunction } from "express";
import { logger } from "../lib/logger";

/**
 * Centralised error handler. Must be registered last in the middleware chain.
 * Catches all unhandled errors and returns a consistent JSON response.
 * Never leaks internal details (stack traces, service URLs) to clients.
 */
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  logger.error(
    {
      err,
      request_id: req.requestId,
      method: req.method,
      path: req.path,
    },
    "Unhandled error"
  );

  const status = "statusCode" in err ? (err as { statusCode: number }).statusCode : 500;

  res.status(status).json({
    error: {
      code: status === 500 ? "internal_error" : "request_error",
      message: status === 500 ? "Internal server error" : err.message,
    },
    meta: { request_id: req.requestId },
  });
}
