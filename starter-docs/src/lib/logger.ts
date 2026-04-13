import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  transport:
    process.env.NODE_ENV === "development"
      ? { target: "pino-pretty" }
      : undefined,
});

/**
 * Create a child logger with document context bound to every log line.
 */
export function createDocLogger(
  docId: string,
  ownerId?: string,
): pino.Logger {
  return logger.child({
    docId,
    ...(ownerId ? { ownerId } : {}),
  });
}
