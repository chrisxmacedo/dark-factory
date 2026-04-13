import type { Request, Response, NextFunction } from "express";
import { v4 as uuidv4 } from "uuid";

declare global {
  namespace Express {
    interface Request {
      requestId: string;
    }
  }
}

/**
 * Injects or propagates x-request-id on every request.
 * If the incoming request has an x-request-id header, it is preserved.
 * Otherwise a new UUID is generated. The ID is attached to both the
 * request object and the response header.
 */
export function correlationMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const requestId =
    (req.headers["x-request-id"] as string | undefined) ?? uuidv4();

  req.requestId = requestId;
  res.setHeader("x-request-id", requestId);

  next();
}
