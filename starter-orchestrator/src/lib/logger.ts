import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  transport:
    process.env.NODE_ENV === "development"
      ? { target: "pino-pretty" }
      : undefined,
});

/**
 * Create a child logger with workflow context bound to every log line.
 */
export function createWorkflowLogger(
  workflowId: string,
  stepName?: string,
): pino.Logger {
  return logger.child({
    workflowId,
    ...(stepName ? { stepName } : {}),
  });
}
