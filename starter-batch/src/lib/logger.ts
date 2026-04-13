import pino, { Logger } from "pino";

const rootLogger: Logger = pino({
  level: process.env.LOG_LEVEL || "info",
  transport:
    process.env.NODE_ENV === "development"
      ? { target: "pino-pretty", options: { colorize: true } }
      : undefined,
});

/**
 * Create a child logger with jobName and runId bound to every log line.
 *
 * Usage:
 *   const logger = createJobLogger("reconcile", "abc-123");
 *   logger.info({ progress: "500/2000" }, "Processing records");
 *   // => { jobName: "reconcile", runId: "abc-123", progress: "500/2000", msg: "Processing records" }
 */
export function createJobLogger(jobName: string, runId: string): Logger {
  return rootLogger.child({ jobName, runId });
}

export { rootLogger as logger };
