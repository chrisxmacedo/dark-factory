import pino from "pino";

const isProduction = process.env.NODE_ENV === "production";
const logLevel = process.env.LOG_LEVEL ?? (isProduction ? "info" : "debug");

export const logger = pino({
  level: logLevel,
  formatters: {
    level(label) {
      return { level: label };
    },
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  base: {
    service: process.env.OTEL_SERVICE_NAME ?? "{PROJECT_NAME}-web",
    environment: process.env.ENVIRONMENT ?? "development",
    version: process.env.OTEL_SERVICE_VERSION ?? "dev",
  },
  ...(process.env.LOG_FORMAT !== "json" && !isProduction
    ? {
        transport: {
          target: "pino-pretty",
          options: {
            colorize: true,
            translateTime: "SYS:standard",
          },
        },
      }
    : {}),
});

/**
 * Create a child logger with request context (correlation ID, path, etc.)
 */
export function createRequestLogger(requestId: string, path?: string) {
  return logger.child({
    requestId,
    ...(path ? { path } : {}),
  });
}

export default logger;
