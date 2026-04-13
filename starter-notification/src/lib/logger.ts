import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  transport:
    process.env.NODE_ENV === "development"
      ? { target: "pino-pretty" }
      : undefined,
});

/**
 * Create a child logger with job context bound to every log line.
 */
export function createJobLogger(
  jobId: string,
  userId?: string,
): pino.Logger {
  return logger.child({
    jobId,
    ...(userId ? { userId } : {}),
  });
}
