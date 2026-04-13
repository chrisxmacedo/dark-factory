import { logger } from "../lib/logger";

// --- Circuit breaker state ---

enum CircuitState {
  Closed = "CLOSED",
  Open = "OPEN",
  HalfOpen = "HALF_OPEN",
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeoutMs: number;
}

interface CircuitBreaker {
  state: CircuitState;
  failureCount: number;
  lastFailureTime: number;
}

// --- Client configuration ---

export interface BaseClientConfig {
  /** Base URL of the internal service (e.g. http://user-service:8080) */
  baseUrl: string;
  /** Service name for logging */
  serviceName: string;
  /** Request timeout in milliseconds. Default: 5000 */
  timeoutMs?: number;
  /** Max retry attempts on transient failures. Default: 2 */
  maxRetries?: number;
  /** Circuit breaker config. Default: 5 failures in 30s, 60s reset */
  circuitBreaker?: Partial<CircuitBreakerConfig>;
}

export interface RequestOptions {
  method?: string;
  path: string;
  body?: unknown;
  headers?: Record<string, string>;
  /** Correlation ID to propagate. Typically req.requestId. */
  requestId?: string;
}

interface ClientResponse<T = unknown> {
  status: number;
  data: T;
  headers: Headers;
}

// --- Base client ---

export class BaseClient {
  private readonly baseUrl: string;
  private readonly serviceName: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;
  private readonly cbConfig: CircuitBreakerConfig;
  private circuit: CircuitBreaker;

  constructor(config: BaseClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.serviceName = config.serviceName;
    this.timeoutMs = config.timeoutMs ?? 5_000;
    this.maxRetries = config.maxRetries ?? 2;
    this.cbConfig = {
      failureThreshold: config.circuitBreaker?.failureThreshold ?? 5,
      resetTimeoutMs: config.circuitBreaker?.resetTimeoutMs ?? 60_000,
    };
    this.circuit = {
      state: CircuitState.Closed,
      failureCount: 0,
      lastFailureTime: 0,
    };
  }

  async request<T = unknown>(options: RequestOptions): Promise<ClientResponse<T>> {
    this.checkCircuit();

    const method = options.method ?? "GET";
    const url = `${this.baseUrl}${options.path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (options.requestId) {
      headers["x-request-id"] = options.requestId;
    }

    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(
          () => controller.abort(),
          this.timeoutMs
        );

        const start = Date.now();

        const response = await fetch(url, {
          method,
          headers,
          body: options.body ? JSON.stringify(options.body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeout);

        const duration = Date.now() - start;
        const data = (await response.json()) as T;

        logger.info(
          {
            service: this.serviceName,
            method,
            path: options.path,
            status: response.status,
            duration_ms: duration,
            attempt,
            request_id: options.requestId,
          },
          "Downstream response"
        );

        if (response.ok) {
          this.onSuccess();
          return { status: response.status, data, headers: response.headers };
        }

        // Non-retryable client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          this.onSuccess(); // 4xx is not a service failure
          return { status: response.status, data, headers: response.headers };
        }

        // 5xx — retryable
        lastError = new Error(
          `${this.serviceName} returned ${response.status}`
        );
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        logger.warn(
          {
            service: this.serviceName,
            method,
            path: options.path,
            attempt,
            err: lastError.message,
            request_id: options.requestId,
          },
          "Downstream request failed"
        );
      }

      // Exponential backoff before retry
      if (attempt < this.maxRetries) {
        await this.sleep(Math.pow(2, attempt) * 200);
      }
    }

    this.onFailure();
    throw lastError ?? new Error(`${this.serviceName} request failed`);
  }

  // --- Convenience methods ---

  async get<T = unknown>(
    path: string,
    requestId?: string
  ): Promise<ClientResponse<T>> {
    return this.request<T>({ method: "GET", path, requestId });
  }

  async post<T = unknown>(
    path: string,
    body: unknown,
    requestId?: string
  ): Promise<ClientResponse<T>> {
    return this.request<T>({ method: "POST", path, body, requestId });
  }

  async put<T = unknown>(
    path: string,
    body: unknown,
    requestId?: string
  ): Promise<ClientResponse<T>> {
    return this.request<T>({ method: "PUT", path, body, requestId });
  }

  async delete<T = unknown>(
    path: string,
    requestId?: string
  ): Promise<ClientResponse<T>> {
    return this.request<T>({ method: "DELETE", path, requestId });
  }

  // --- Circuit breaker ---

  private checkCircuit(): void {
    if (this.circuit.state === CircuitState.Open) {
      const elapsed = Date.now() - this.circuit.lastFailureTime;
      if (elapsed >= this.cbConfig.resetTimeoutMs) {
        this.circuit.state = CircuitState.HalfOpen;
        logger.info({ service: this.serviceName }, "Circuit half-open — allowing probe request");
      } else {
        throw new Error(
          `Circuit open for ${this.serviceName} — requests blocked`
        );
      }
    }
  }

  private onSuccess(): void {
    if (
      this.circuit.state === CircuitState.HalfOpen ||
      this.circuit.state === CircuitState.Open
    ) {
      logger.info({ service: this.serviceName }, "Circuit closed — service recovered");
    }
    this.circuit = {
      state: CircuitState.Closed,
      failureCount: 0,
      lastFailureTime: 0,
    };
  }

  private onFailure(): void {
    this.circuit.failureCount++;
    this.circuit.lastFailureTime = Date.now();

    if (this.circuit.failureCount >= this.cbConfig.failureThreshold) {
      this.circuit.state = CircuitState.Open;
      logger.warn(
        {
          service: this.serviceName,
          failures: this.circuit.failureCount,
        },
        "Circuit opened — too many failures"
      );
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
