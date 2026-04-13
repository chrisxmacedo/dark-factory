import type { Request, Response, NextFunction } from "express";
import { logger } from "../lib/logger";

/**
 * Structured request/response logging.
 * Logs request start and completion with method, path, status,
 * duration, user ID, and correlation ID.
 */
export function loggingMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const start = Date.now();

  const requestLog = {
    request_id: req.requestId,
    method: req.method,
    path: req.path,
    user_agent: req.headers["user-agent"],
    ip: req.ip,
  };

  logger.info(requestLog, "Request started");

  res.on("finish", () => {
    const duration = Date.now() - start;

    logger.info(
      {
        ...requestLog,
        status: res.statusCode,
        duration_ms: duration,
        user_id: req.user?.sub,
        content_length: res.getHeader("content-length"),
      },
      "Request completed"
    );
  });

  next();
}
