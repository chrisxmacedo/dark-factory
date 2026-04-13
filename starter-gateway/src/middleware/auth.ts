import type { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import jwksClient from "jwks-rsa";
import { config } from "../config";
import { logger } from "../lib/logger";

export interface AuthUser {
  sub: string;
  email?: string;
  [key: string]: unknown;
}

declare global {
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

const client = jwksClient({
  jwksUri: config.jwksUri,
  cache: true,
  cacheMaxAge: 600_000, // 10 minutes
  rateLimit: true,
});

function getSigningKey(
  header: jwt.JwtHeader,
  callback: jwt.SigningKeyCallback
): void {
  client.getSigningKey(header.kid, (err, key) => {
    if (err || !key) {
      callback(err ?? new Error("Signing key not found"));
      return;
    }
    callback(null, key.getPublicKey());
  });
}

// Routes that do not require authentication.
// Add paths here as needed (e.g. "/v1/health").
const PUBLIC_PATHS: ReadonlySet<string> = new Set(["/v1/health"]);

export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  if (PUBLIC_PATHS.has(req.path)) {
    next();
    return;
  }

  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    res.status(401).json({
      error: { code: "unauthorized", message: "Missing or invalid token" },
    });
    return;
  }

  const token = authHeader.slice(7);

  jwt.verify(
    token,
    getSigningKey,
    {
      issuer: config.jwtIssuer,
      audience: config.jwtAudience,
      algorithms: ["RS256"],
    },
    (err, decoded) => {
      if (err) {
        logger.warn({ err: err.message }, "JWT verification failed");
        res.status(401).json({
          error: { code: "unauthorized", message: "Invalid token" },
        });
        return;
      }

      req.user = decoded as AuthUser;
      next();
    }
  );
}
