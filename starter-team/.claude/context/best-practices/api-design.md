# REST API design best practices

Read by: all teams exposing HTTP endpoints (starter-api, starter-web API routes, starter-gateway)

## Response envelopes

Every endpoint must use a standard envelope. Never return bare arrays, raw objects, or unstructured responses.

**Single resource:**

```python
# FastAPI
from pydantic import BaseModel, Generic, TypeVar

T = TypeVar("T")

class DataResponse(BaseModel, Generic[T]):
    data: T

@router.get("/items/{id}", response_model=DataResponse[ItemResponse])
async def get_item(id: uuid.UUID, db: DB) -> DataResponse[ItemResponse]:
    item = await fetch_item(db, id)
    return DataResponse(data=item)
```

```typescript
// Next.js API route
export async function GET(req: Request, { params }: { params: { id: string } }) {
  const item = await getItem(params.id);
  return Response.json({ data: item });
}
```

**Collection with pagination:**

```json
{
  "data": [{ "id": "...", "name": "..." }],
  "meta": { "page": 1, "pageSize": 20, "total": 142 },
  "links": { "next": "/v1/items?page=2&pageSize=20", "prev": null }
}
```

**Error:**

```json
{ "error": { "code": "not_found", "message": "Item not found" } }
```

NEVER:
- Return a bare array from a list endpoint
- Return a raw object without wrapping in `{ data: ... }`
- Mix envelope shapes across endpoints in the same service

## Error codes

Use these machine-readable codes consistently across all services. The `code` field is for programmatic handling; `message` is for humans.

| Code | Meaning |
|---|---|
| `not_found` | Resource does not exist |
| `validation_error` | Request body, query params, or route params invalid |
| `unauthorized` | No valid auth token or session |
| `forbidden` | Authenticated but not permitted for this resource |
| `conflict` | Resource already exists or state conflict |
| `rate_limited` | Too many requests — check Retry-After header |
| `internal_error` | Unexpected server error |

```python
# FastAPI — raise with standard code
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail={"code": "not_found", "message": "Item not found"},
)
```

```typescript
// Next.js API route — return with standard code
return Response.json(
  { error: { code: "not_found", message: "Item not found" } },
  { status: 404 },
);
```

NEVER:
- Invent ad-hoc error codes outside this list without team agreement
- Return error details without the `code` field
- Leak stack traces, SQL errors, or internal paths in the `message`

## HTTP status codes

| Status | When to use |
|---|---|
| `200 OK` | Successful read or update |
| `201 Created` | Resource successfully created |
| `204 No Content` | Successful delete with no response body |
| `400 Bad Request` | Malformed request (unparseable JSON, missing required fields) |
| `401 Unauthorized` | Missing or invalid auth token |
| `403 Forbidden` | Valid auth but insufficient permissions |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate resource or state conflict |
| `422 Unprocessable Entity` | Syntactically valid but semantically invalid input |
| `429 Too Many Requests` | Rate limit exceeded — include Retry-After header |
| `500 Internal Server Error` | Unexpected failure — log full error server-side |

Use 400 for structurally broken requests and 422 for requests that parse but fail business validation. Be consistent within each service.

## Pagination

All list endpoints must be paginated. Never return unbounded collections.

**Offset-based (default for most endpoints):**

```python
# FastAPI
from fastapi import Depends, Query, Request
from typing import Annotated

class PaginationParams:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, alias="pageSize")] = 20,
    ):
        self.page = page
        self.page_size = page_size

@router.get("/items", response_model=CollectionResponse[ItemResponse])
async def list_items(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: DB,
) -> CollectionResponse[ItemResponse]:
    items, total = await fetch_items(db, pagination.page, pagination.page_size)
    return CollectionResponse.paginate(
        data=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        base_url=str(request.url),
    )
```

```typescript
// Next.js API route
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const page = Math.max(1, Number(searchParams.get("page") ?? 1));
  const pageSize = Math.min(100, Math.max(1, Number(searchParams.get("pageSize") ?? 20)));

  const { items, total } = await listItems({ page, pageSize });

  return Response.json({
    data: items,
    meta: { page, pageSize, total },
    links: {
      next: page * pageSize < total ? `/api/items?page=${page + 1}&pageSize=${pageSize}` : null,
      prev: page > 1 ? `/api/items?page=${page - 1}&pageSize=${pageSize}` : null,
    },
  });
}
```

**Cursor-based (for large datasets or real-time feeds):**

Use cursor-based pagination when the dataset is large enough that offset performance degrades or when rows may be inserted during pagination. Return an opaque `cursor` string instead of `page`.

- Always return `total` count in `meta`
- Always return `next` and `prev` in `links` (null when not applicable)
- Default `pageSize` of 20, maximum of 100

## Idempotency

All write endpoints (POST, PUT, PATCH) must support the `Idempotency-Key` header for safe retries.

- Client sends `Idempotency-Key: <unique-string>` with the request
- Server caches the response keyed by `(user_id, idempotency_key)` for 24 hours
- On replay with the same key, return the cached response without re-executing
- If the original request is still processing, return `409 Conflict`

```python
# FastAPI — middleware approach (src/middleware/idempotency.py)
@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        key = request.headers.get("Idempotency-Key")
        if key:
            cached = await redis.get(f"idempotency:{request.state.user_id}:{key}")
            if cached:
                return JSONResponse(content=json.loads(cached), status_code=200)
    response = await call_next(request)
    # Cache response after successful write...
    return response
```

```typescript
// Next.js API route — per-handler check
export async function POST(req: Request) {
  const idempotencyKey = req.headers.get("Idempotency-Key");
  if (idempotencyKey) {
    const cached = await redis.get(`idempotency:${userId}:${idempotencyKey}`);
    if (cached) return Response.json(JSON.parse(cached));
  }

  const result = await createItem(body);

  if (idempotencyKey) {
    await redis.set(`idempotency:${userId}:${idempotencyKey}`, JSON.stringify({ data: result }), "EX", 86400);
  }
  return Response.json({ data: result }, { status: 201 });
}
```

Document idempotency support in OpenAPI descriptions for every write endpoint.

## Versioning

URL-based versioning. All routes live under a version prefix.

```
/v1/items
/v1/items/{id}
/v2/items          # breaking changes only
```

- Never use header-based versioning (Accept-Version, custom headers)
- Each version gets its own route directory or router module
- Breaking changes require a new version — additive changes do not
- Support the previous version for at least 6 months after a new version ships
- Default version (no prefix) is not allowed — always explicit

```python
# FastAPI
app.include_router(v1_router, prefix="/v1")
app.include_router(v2_router, prefix="/v2")
```

```typescript
// Next.js — use directory structure
// src/app/api/v1/items/route.ts
// src/app/api/v2/items/route.ts
```

## Input validation

Validate at every endpoint boundary. Never trust client input.

- **Route params:** verify format (UUID, CUID) before database lookup
- **Query params:** validate types, ranges, allowed values
- **Request body:** full schema validation on every POST/PATCH/PUT

```python
# FastAPI — Pydantic schemas
from pydantic import BaseModel, Field

class CreateItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    category: str = Field(..., pattern=r"^[a-z_]+$")

@router.post("/items", response_model=DataResponse[ItemResponse], status_code=201)
async def create_item(body: CreateItemRequest, db: DB) -> DataResponse[ItemResponse]:
    ...
```

```typescript
// Next.js API route — Zod schemas
import { z } from "zod";

const CreateItemSchema = z.object({
  name: z.string().min(1).max(255),
  price: z.number().positive(),
  category: z.string().regex(/^[a-z_]+$/),
});

export async function POST(req: Request) {
  const parsed = CreateItemSchema.safeParse(await req.json());
  if (!parsed.success) {
    return Response.json(
      { error: { code: "validation_error", message: parsed.error.issues[0].message } },
      { status: 422 },
    );
  }
  // use parsed.data ...
}
```

NEVER:
- Skip validation because "the frontend already validates"
- Pass raw `req.body` to a database query or service call
- Use `any` or untyped objects for request data

## Health endpoints

Every service must expose a health endpoint that load balancers and monitors can check.

```
GET /healthz           # standalone services
GET /api/health        # Next.js API routes
GET /v1/health         # gateway
```

- Check all critical dependencies: database, Redis, external services
- Return 200 with dependency status when healthy
- Return 503 when any critical dependency is down

```python
# FastAPI
@router.get("/healthz", status_code=200)
async def health(db: DB):
    checks = {
        "database": await check_db(db),
        "redis": await check_redis(),
    }
    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(
        content={"status": "healthy" if status_code == 200 else "degraded", "checks": checks},
        status_code=status_code,
    )
```

```typescript
// Next.js API route — src/app/api/health/route.ts
export async function GET() {
  const checks = {
    database: await checkDb(),
    redis: await checkRedis(),
  };
  const healthy = Object.values(checks).every(Boolean);
  return Response.json(
    { status: healthy ? "healthy" : "degraded", checks },
    { status: healthy ? 200 : 503 },
  );
}
```

Health endpoints are always public (no auth required).

## Correlation IDs

Every request must carry a correlation ID for end-to-end tracing across services.

- Header: `x-request-id`
- If the client sends one, use it. Otherwise, generate a UUID at the entry point.
- Propagate through all inter-service calls
- Include in every log line
- Include in error responses so users can reference it in support requests

```python
# FastAPI — middleware
import uuid

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response
```

```typescript
// Next.js — middleware.ts
import { NextResponse } from "next/server";
import { randomUUID } from "crypto";

export function middleware(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? randomUUID();
  const response = NextResponse.next();
  response.headers.set("x-request-id", requestId);
  return response;
}
```

NEVER:
- Log a request without its correlation ID
- Call a downstream service without forwarding the correlation ID
- Return an error response without the `x-request-id` header

## Content negotiation

- Always return `application/json` with `Content-Type: application/json` header
- Accept `application/json` on request bodies
- Return `415 Unsupported Media Type` if the client sends a non-JSON content type on endpoints that expect JSON
- Binary responses (file downloads, images) are the exception — use appropriate MIME types

NEVER:
- Return HTML from an API endpoint
- Omit the Content-Type header
- Accept form-encoded data on JSON API endpoints unless explicitly designed for webhooks
