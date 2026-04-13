import { logger } from "./logger";

export interface RetryOptions {
  maxAttempts: number;
  backoffMs: number;
  /** Multiplier applied to backoff on each retry (default: 2) */
  backoffMultiplier?: number;
}

const DEFAULT_OPTIONS: RetryOptions = {
  maxAttempts: 3,
  backoffMs: 1000,
  backoffMultiplier: 2,
};

/**
 * Retry an async function with exponential backoff.
 * Throws the last error after all attempts are exhausted.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {},
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt === opts.maxAttempts) break;

      const delay =
        opts.backoffMs * Math.pow(opts.backoffMultiplier ?? 2, attempt - 1);
      logger.warn(
        { attempt, maxAttempts: opts.maxAttempts, delayMs: delay, err: lastError.message },
        "Retry attempt",
      );
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}
