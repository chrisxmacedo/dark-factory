import express, { type Express } from "express";
import helmet from "helmet";
import cors from "cors";
import { correlationMiddleware } from "./middleware/correlation";
import { loggingMiddleware } from "./middleware/logging";
import { rateLimitMiddleware } from "./middleware/rate-limit";
import { authMiddleware } from "./middleware/auth";
import { errorHandler } from "./middleware/error-handler";
import { v1Router } from "./routes/v1";
import { config } from "./config";

export function createApp(): Express {
  const app = express();

  // --- Core middleware ---
  app.use(helmet());
  app.use(
    cors({
      origin: config.corsOrigins,
      credentials: true,
    })
  );
  app.use(express.json({ limit: "1mb" }));

  // --- Gateway middleware chain ---
  // Order matters: correlation > logging > rate-limit > auth
  app.use(correlationMiddleware);
  app.use(loggingMiddleware);
  app.use(rateLimitMiddleware);
  app.use(authMiddleware);

  // --- Versioned routes ---
  app.use("/v1", v1Router);

  // --- Error handler (must be last) ---
  app.use(errorHandler);

  return app;
}
