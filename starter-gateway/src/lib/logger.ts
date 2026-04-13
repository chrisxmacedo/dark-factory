import pino from "pino";
import { config } from "../config";

export const logger = pino({
  level: config.logLevel,
  formatters: {
    level(label: string) {
      return { level: label };
    },
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  base: {
    service: config.otelServiceName,
    env: config.nodeEnv,
  },
});
