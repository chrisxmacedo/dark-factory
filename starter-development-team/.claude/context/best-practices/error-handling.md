# Error handling best practices

Read by: all teams, all starters (API routes, FastAPI services, frontend apps)

## Error hierarchy

Separate operational errors from programmer errors. They get different treatment.

**Operational errors** are expected failures: validation, not found, auth, rate limits. The system is working correctly — the request is wrong. Return a clean, structured error response with the appropriate HTTP status.

**Programmer errors** are unexpected failures: null references, type errors, unhandled promise rejections, database connection crashes. The system has a bug or an infrastructure problem. Log the full error with stack trace server-side, return a generic 500 to the client.

```python
# FastAPI — operational error (expected)
raise HTTPException(
    status_code=404,
    detail={"code": "not_found", "message": "Invoice not found"},
)

# FastAPI — programmer error (unexpected)
# Don't catch these per-handler. Let the global exception handler catch them:
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        error=str(exc),
        traceback=traceback.format_exc(),
        request_id=request.state.request_id,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
    )
```

```typescript
// Next.js API route — operational error (expected)
return Response.json(
  { error: { code: "not_found", message: "Invoice not found" } },
  { status: 404 },
);

// Next.js API route — programmer error (unexpected)
// Wrap route handlers in a try/catch at the boundary:
export async function GET(req: Request) {
  try {
    const data = await fetchInvoice(params.id);
    return Response.json({ data });
  } catch (error) {
    if (error instanceof AppError) {
      return Response.json(
        { error: { code: error.code, message: error.message } },
        { status: error.statusCode },
      );
    }
    logger.error({ error, requestId, path: req.url }, "unhandled_exception");
    return Response.json(
      { error: { code: "internal_error", message: "An unexpected error occurred" } },
      { status: 500 },
    );
  }
}
```

## Error response shape

Every error response across every service uses this shape:

```json
{ "error": { "code": "not_found", "message": "Invoice not found" } }
```

With optional details for validation errors:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": {
      "fields": [
        { "path": "email", "message": "Invalid email address" },
        { "path": "amount", "message": "Must be greater than 0" }
      ]
    }
  }
}
```

- `code` — machine-readable, for programmatic handling (switch statements, retry logic)
- `message` — human-readable, safe to display in UI
- `details` — optional, structured metadata (validation field errors, downstream service info)

## Standard error codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `not_found` | 404 | Resource does not exist |
| `validation_error` | 400 or 422 | Request body, query params, or route params invalid |
| `unauthorized` | 401 | No valid auth token or session |
| `forbidden` | 403 | Authenticated but not permitted for this resource |
| `conflict` | 409 | Resource already exists or state conflict |
| `rate_limited` | 429 | Too many requests — check Retry-After header |
| `internal_error` | 500 | Unexpected server error |

Add domain-specific codes when needed (e.g. `insufficient_balance`, `account_suspended`, `quota_exceeded`). Document new codes in the service's CLAUDE.md and get team agreement before adding them.

## HTTP to error code mapping

Map inbound HTTP status codes to error codes consistently:

| HTTP Status | Error Code |
|---|---|
| 400 | `validation_error` |
| 401 | `unauthorized` |
| 403 | `forbidden` |
| 404 | `not_found` |
| 409 | `conflict` |
| 422 | `validation_error` |
| 429 | `rate_limited` |
| 500 | `internal_error` |

Use 400 for structurally broken requests (unparseable JSON, missing required fields). Use 422 for requests that parse but fail business validation (invalid email format, amount out of range).

## Custom error classes

### Python (FastAPI)

```python
# src/errors.py
from fastapi import HTTPException

class AppError(HTTPException):
    """Base class for operational errors with a machine-readable code."""

    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        detail = {"code": code, "message": message}
        if details:
            detail["details"] = details
        super().__init__(status_code=status_code, detail=detail)

class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(404, "not_found", f"{resource} not found")

class ValidationError(AppError):
    def __init__(self, message: str, fields: list[dict] | None = None):
        details = {"fields": fields} if fields else None
        super().__init__(422, "validation_error", message, details)

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(409, "conflict", message)

class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to access this resource"):
        super().__init__(403, "forbidden", message)
```

### TypeScript (Next.js)

```typescript
// src/lib/errors.ts
export class AppError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly code: string,
    message: string,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(404, "not_found", `${resource} not found`);
  }
}

export class ValidationError extends AppError {
  constructor(message: string, fields?: Array<{ path: string; message: string }>) {
    super(422, "validation_error", message, fields ? { fields } : undefined);
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super(409, "conflict", message);
  }
}

export class ForbiddenError extends AppError {
  constructor(message = "You do not have permission to access this resource") {
    super(403, "forbidden", message);
  }
}
```

## Validation errors

Return all validation failures at once. Never return one error at a time — that forces users to fix-and-retry repeatedly.

```python
# FastAPI — Pydantic handles this automatically.
# Override the RequestValidationError handler to use the standard shape:
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    fields = [
        {"path": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": {"fields": fields},
            }
        },
    )
```

```typescript
// Next.js — format Zod errors into the standard shape
import { z } from "zod";

function formatZodError(error: z.ZodError) {
  return {
    error: {
      code: "validation_error" as const,
      message: "Request validation failed",
      details: {
        fields: error.issues.map((issue) => ({
          path: issue.path.join("."),
          message: issue.message,
        })),
      },
    },
  };
}

export async function POST(req: Request) {
  const parsed = CreateInvoiceSchema.safeParse(await req.json());
  if (!parsed.success) {
    return Response.json(formatZodError(parsed.error), { status: 422 });
  }
  // use parsed.data ...
}
```

## Error context propagation

Every error log and error response must carry a correlation ID (`x-request-id`). This is the thread that ties logs, traces, and support requests together.

- Include correlation ID in every error log entry
- Include the originating service name for cross-service errors
- Propagate error codes from downstream services — don't swallow and re-throw generic errors

```python
# FastAPI — include correlation ID in error responses
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "unhandled_exception",
        error=str(exc),
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
        headers={"x-request-id": request_id},
    )
```

```typescript
// Next.js — include correlation ID in error responses
const requestId = req.headers.get("x-request-id") ?? randomUUID();

return Response.json(
  { error: { code: "internal_error", message: "An unexpected error occurred" } },
  { status: 500, headers: { "x-request-id": requestId } },
);
```

## Cross-service errors

When Service A calls Service B and B returns an error:

1. **Log the full error in A** — including B's response body, status code, correlation ID
2. **Propagate B's error code if it's relevant to the client** — if B returns `not_found` and A's client needs to know, forward it
3. **Don't leak B's internal details** — strip implementation-specific messages, internal paths, stack traces
4. **Include the originating service** — log which downstream service failed

```python
# FastAPI — calling a downstream service
async def get_user_from_auth_service(user_id: str, request_id: str) -> dict:
    response = await http_client.get(
        f"{AUTH_SERVICE_URL}/v1/users/{user_id}",
        headers={"x-request-id": request_id},
        timeout=5.0,
    )
    if response.status_code != 200:
        error_body = response.json().get("error", {})
        logger.warn(
            "downstream_error",
            service="auth-service",
            status_code=response.status_code,
            error_code=error_body.get("code"),
            error_message=error_body.get("message"),
            request_id=request_id,
        )
        # Propagate relevant codes, wrap others
        if error_body.get("code") == "not_found":
            raise NotFoundError("User", user_id)
        raise AppError(502, "internal_error", "Failed to fetch user data")
    return response.json()["data"]
```

```typescript
// Next.js — calling a downstream service
async function getUserFromAuthService(userId: string, requestId: string) {
  const res = await fetch(`${AUTH_SERVICE_URL}/v1/users/${userId}`, {
    headers: { "x-request-id": requestId },
    signal: AbortSignal.timeout(5000),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const errorCode = body?.error?.code;

    logger.warn(
      { service: "auth-service", statusCode: res.status, errorCode, requestId },
      "downstream_error",
    );

    if (errorCode === "not_found") {
      throw new NotFoundError("User");
    }
    throw new AppError(502, "internal_error", "Failed to fetch user data");
  }

  return (await res.json()).data;
}
```

## Error logging

Use consistent log levels based on the error type:

| Status range | Log level | Rationale |
|---|---|---|
| 5xx | `error` | Something is broken — needs investigation |
| 4xx (unexpected) | `warn` | Client error that might indicate a bug (e.g. repeated 403s from a service account) |
| 4xx (expected) | `info` | Normal operations — not found, validation failures |

Every error log entry must include:

- `request_id` — correlation ID
- `error_code` — machine-readable code
- `path` — request path
- `method` — HTTP method
- `status_code` — response status
- `duration_ms` — request duration

```python
# FastAPI — structured error logging in middleware
logger.bind(
    request_id=request.state.request_id,
    path=request.url.path,
    method=request.method,
    status_code=response.status_code,
    duration_ms=duration_ms,
)

if response.status_code >= 500:
    logger.error("request_failed")
elif response.status_code >= 400:
    logger.info("request_client_error")
```

```typescript
// Next.js — structured error logging
logger.error({
  requestId,
  errorCode: "internal_error",
  path: req.url,
  method: req.method,
  statusCode: 500,
  durationMs: Date.now() - startTime,
}, "request_failed");
```

## Error boundaries (frontend)

Use Next.js error boundaries to catch rendering errors and show a user-friendly fallback.

**Per-route error boundary** — colocate `error.tsx` with the page:

```typescript
// src/app/(app)/invoices/error.tsx
"use client";

import { useEffect } from "react";

export default function InvoicesError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to error reporting service (Sentry, etc.)
    console.error(error);
  }, [error]);

  return (
    <div>
      <h2>Something went wrong loading invoices</h2>
      {error.digest && (
        <p className="text-sm text-gray-500">
          Error reference: {error.digest}
        </p>
      )}
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

**Global error boundary** — catches errors in the root layout:

```typescript
// src/app/global-error.tsx
"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div>
          <h2>Something went wrong</h2>
          {error.digest && (
            <p>Error reference: {error.digest}</p>
          )}
          <button onClick={reset}>Try again</button>
        </div>
      </body>
    </html>
  );
}
```

- Every route segment that fetches data should have its own `error.tsx`
- Show the `digest` (Next.js error ID) so users can reference it in support requests
- The global error boundary is the last resort — it catches errors that no route-level boundary handled
- Never show stack traces, error messages, or internal details to users

NEVER:
- Catch errors and swallow them silently (empty catch blocks)
- Return stack traces, SQL errors, internal file paths, or database structure in error responses
- Return one validation error at a time — always return all failures
- Invent ad-hoc error codes without team agreement
- Use generic `catch (e) { throw new Error("something went wrong") }` — preserve the original error code
- Log a request without its correlation ID
- Return an error response without the `x-request-id` header
- Retry on 4xx client errors (except 429 with Retry-After)
- Expose which downstream service failed in client-facing error messages
