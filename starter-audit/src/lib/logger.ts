import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  transport:
    process.env.NODE_ENV === "development"
      ? { target: "pino-pretty" }
      : undefined,
});

/**
 * Create a child logger with audit event context bound to every log line.
 */
export function createEventLogger(
  eventId?: string,
  actor?: string,
): pino.Logger {
  return logger.child({
    ...(eventId ? { eventId } : {}),
    ...(actor ? { actor } : {}),
  });
}
