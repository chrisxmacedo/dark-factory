import jwt from "jsonwebtoken";
import { logger } from "./logger";

const JWT_SECRET = process.env.JWT_SECRET ?? "{JWT_SECRET}";

export interface UserContext {
  userId: string;
  [key: string]: unknown;
}

/**
 * Validate a JWT token and return the decoded user context.
 * Used during WebSocket upgrade to authenticate the connection.
 *
 * Token may come from:
 * - Query parameter: ?token=xxx
 * - Authorization header: Bearer xxx
 */
export function validateToken(token: string): UserContext | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as jwt.JwtPayload;

    if (!decoded.sub) {
      logger.warn("JWT missing sub claim");
      return null;
    }

    return {
      userId: decoded.sub,
      ...decoded,
    };
  } catch (err) {
    logger.warn({ err }, "JWT validation failed");
    return null;
  }
}

/**
 * Extract token from an HTTP upgrade request.
 * Checks query parameter first, then Authorization header.
 */
export function extractToken(url: string, headers: Record<string, string | string[] | undefined>): string | null {
  // Check query parameter
  try {
    const parsed = new URL(url, "http://localhost");
    const token = parsed.searchParams.get("token");
    if (token) return token;
  } catch {
    // URL parse failed — fall through to header check
  }

  // Check Authorization header
  const authHeader = headers["authorization"];
  if (typeof authHeader === "string" && authHeader.startsWith("Bearer ")) {
    return authHeader.slice(7);
  }

  return null;
}
