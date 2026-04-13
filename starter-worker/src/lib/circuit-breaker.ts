import { logger } from "./logger";

type CircuitState = "closed" | "open" | "half-open";

export interface CircuitBreakerOptions {
  /** Number of consecutive failures before opening the circuit */
  failureThreshold: number;
  /** How long to wait (ms) before transitioning from open to half-open */
  resetTimeoutMs: number;
  /** Number of successes in half-open needed to close the circuit */
  halfOpenSuccessThreshold: number;
}

const DEFAULT_OPTIONS: CircuitBreakerOptions = {
  failureThreshold: 5,
  resetTimeoutMs: 30_000,
  halfOpenSuccessThreshold: 2,
};

export class CircuitBreaker {
  private state: CircuitState = "closed";
  private failureCount = 0;
  private halfOpenSuccessCount = 0;
  private lastFailureTime = 0;
  private readonly name: string;
  private readonly options: CircuitBreakerOptions;

  constructor(name: string, options: Partial<CircuitBreakerOptions> = {}) {
    this.name = name;
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailureTime >= this.options.resetTimeoutMs) {
        this.transitionTo("half-open");
      } else {
        throw new Error(`Circuit breaker "${this.name}" is open`);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      throw err;
    }
  }

  private onSuccess(): void {
    if (this.state === "half-open") {
      this.halfOpenSuccessCount++;
      if (
        this.halfOpenSuccessCount >= this.options.halfOpenSuccessThreshold
      ) {
        this.transitionTo("closed");
      }
    } else {
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === "half-open") {
      this.transitionTo("open");
    } else if (this.failureCount >= this.options.failureThreshold) {
      this.transitionTo("open");
    }
  }

  private transitionTo(newState: CircuitState): void {
    logger.warn(
      { circuitBreaker: this.name, from: this.state, to: newState },
      "Circuit breaker state change",
    );
    this.state = newState;
    if (newState === "closed") {
      this.failureCount = 0;
      this.halfOpenSuccessCount = 0;
    } else if (newState === "half-open") {
      this.halfOpenSuccessCount = 0;
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}
