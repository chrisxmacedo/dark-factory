# Authentication best practices

Read by: all teams, all starters

## Auth architecture

The system uses two complementary auth strategies:

- **API services (FastAPI):** Supabase Auth with JWT verification. The API never manages sessions or login flows — it receives a JWT on every request, validates it, and extracts the user identity from claims.
- **Web frontends (Next.js):** NextAuth.js with Prisma adapter and database-backed sessions. The web app handles OAuth flows, manages sessions, and stores session state server-side.

Both sides share the same user identity via Supabase user ID. The web app authenticates the user through NextAuth, then uses the Supabase JWT when calling API services on behalf of that user.

## JWT verification (API side)

Validate tokens on every request via middleware — never per-route checks.

```python
# src/middleware/auth.py
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel

class CurrentUser(BaseModel):
    id: str
    email: str
    role: str | None = None

async def verify_jwt(request: Request) -> CurrentUser:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "unauthorized", "message": "Authentication required"}},
        )

    token = auth_header.removeprefix("Bearer ")
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            issuer=settings.supabase_url,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "unauthorized", "message": "Authentication required"}},
        )

    return CurrentUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        role=payload.get("role"),
    )
```

```python
# src/dependencies.py
from typing import Annotated
from fastapi import Depends
from src.middleware.auth import verify_jwt, CurrentUser

RequireAuth = Annotated[CurrentUser, Depends(verify_jwt)]
```

Rules:

- Verify signature, expiry, audience, and issuer on every token
- Extract user ID from the `sub` claim — never trust client-supplied user IDs
- Return 401 with a generic message on any failure — never reveal whether the user exists or why the token failed
- Protected by default — explicitly mark public endpoints, not the other way around

## Session management (web side)

NextAuth.js with Prisma adapter and database-backed sessions.

```typescript
// src/lib/auth.ts
import { PrismaAdapter } from "@auth/prisma-adapter";
import { getServerSession, type NextAuthOptions } from "next-auth";
import { prisma } from "@/lib/prisma";

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  session: {
    strategy: "database",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async session({ session, user }) {
      session.user.id = user.id;
      return session;
    },
  },
  // OAuth providers configured per project
};

export function getSession() {
  return getServerSession(authOptions);
}
```

```typescript
// Server Component usage
import { getSession } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const session = await getSession();
  if (!session) redirect("/auth/sign-in");

  // session.user.id is the authenticated user
}
```

```typescript
// API route usage
import { getSession } from "@/lib/auth";
import { NextResponse } from "next/server";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json(
      { error: { code: "unauthorized", message: "Authentication required" } },
      { status: 401 },
    );
  }
  // ...
}
```

Rules:

- Database strategy, not JWT sessions — sessions live server-side
- httpOnly cookies — the session token is never accessible to client JavaScript
- 30-day max age — enforce server-side, don't trust client-side expiry
- `getServerSession()` in Server Components and API routes
- Protect client-side pages with `middleware.ts` route matching
- Encrypt OAuth tokens before storing (AES-256-GCM)

## Token storage

| Platform | Strategy |
|---|---|
| Web | httpOnly cookies (managed by NextAuth) |
| iOS | Keychain |
| Android | EncryptedSharedPreferences |
| API services | Don't store — validate per request |

Never store tokens in `localStorage` or `sessionStorage`. Both are accessible to any JavaScript running on the page, making them vulnerable to XSS. httpOnly cookies are not readable by JavaScript and are sent automatically by the browser.

API services are stateless with respect to auth. They receive a JWT, validate it, extract the user, and discard it. No token persistence, no session table, no refresh logic.

## Inter-service auth

When Service A calls Service B on behalf of a user, forward the user's JWT.

```python
# Service A calling Service B
async def call_service_b(endpoint: str, user_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.service_b_url}{endpoint}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        response.raise_for_status()
        return response.json()
```

```typescript
// Next.js API route calling the FastAPI service
const response = await fetch(`${process.env.API_URL}/items`, {
  headers: { Authorization: `Bearer ${session.accessToken}` },
});
```

Rules:

- Forward the user's JWT in the `Authorization` header — Service B validates independently
- Never create "service accounts" that bypass auth — every request must carry a user identity
- If a background job needs to act on behalf of a user, store the user ID with the job and use a scoped service token that identifies both the service and the user
- Never embed one service's secret in another service's env

## Row-level security

Every database query must scope to the authenticated user.

```python
# FastAPI — always filter by current user
@router.get("/items", response_model=CollectionResponse[ItemResponse])
async def list_items(db: DB, current_user: RequireAuth):
    query = select(Item).where(Item.owner_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/items/{item_id}", response_model=DataResponse[ItemResponse])
async def get_item(item_id: UUID, db: DB, current_user: RequireAuth):
    query = select(Item).where(
        Item.id == item_id,
        Item.owner_id == current_user.id,
    )
    item = (await db.execute(query)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=...)
    return item
```

```typescript
// Next.js API route — always filter by session user
const items = await prisma.item.findMany({
  where: { userId: session.user.id },
});

const item = await prisma.item.findFirst({
  where: { id: params.id, userId: session.user.id },
});
if (!item) return NextResponse.json({ error: { code: "not_found" } }, { status: 404 });
```

Rules:

- Every query includes `WHERE owner_id = current_user.id` (or the domain-appropriate equivalent like `bank_id`, `org_id`)
- Never allow cross-user reads unless explicitly designed as a public or comparison endpoint
- Admin endpoints use separate middleware with role checks and audit logging
- A missing resource and an unauthorized resource both return 404 — never reveal that a resource exists but belongs to someone else

## Auth middleware patterns

### FastAPI

```python
# Protected (default) — use RequireAuth dependency
@router.get("/items")
async def list_items(db: DB, current_user: RequireAuth):
    ...

# Public (explicit) — no RequireAuth dependency
@router.get("/health")
async def health():
    return {"status": "ok"}
```

### Next.js middleware

```typescript
// src/middleware.ts
import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: { signIn: "/auth/sign-in" },
});

export const config = {
  matcher: ["/(app)/:path*", "/api/:path((?!health|auth).*)"],
};
```

### Next.js API route wrapper

```typescript
// src/lib/api/with-auth.ts
import { getSession } from "@/lib/auth";
import { NextResponse } from "next/server";

type AuthenticatedHandler = (
  request: Request,
  context: { session: Session },
) => Promise<NextResponse>;

export function withAuth(handler: AuthenticatedHandler) {
  return async (request: Request) => {
    const session = await getSession();
    if (!session) {
      return NextResponse.json(
        { error: { code: "unauthorized", message: "Authentication required" } },
        { status: 401 },
      );
    }
    return handler(request, { session });
  };
}
```

### Express (gateway)

```typescript
// middleware/auth.ts
import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    return res.status(401).json({
      error: { code: "unauthorized", message: "Authentication required" },
    });
  }

  try {
    const payload = jwt.verify(
      authHeader.slice(7),
      process.env.SUPABASE_JWT_SECRET!,
      { algorithms: ["HS256"], issuer: process.env.SUPABASE_URL },
    );
    req.user = { id: payload.sub, email: payload.email };
    next();
  } catch {
    return res.status(401).json({
      error: { code: "unauthorized", message: "Authentication required" },
    });
  }
}

// Usage
app.use("/api", requireAuth);
app.get("/health", (req, res) => res.json({ status: "ok" })); // public
```

## Testing auth

Test both authenticated and unauthenticated code paths for every protected endpoint.

```python
# FastAPI test fixtures — conftest.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user_token: str):
    client.headers["Authorization"] = f"Bearer {test_user_token}"
    return client

# Test both paths
async def test_list_items_authenticated(authenticated_client):
    response = await authenticated_client.get("/items")
    assert response.status_code == 200

async def test_list_items_unauthenticated(client):
    response = await client.get("/items")
    assert response.status_code == 401

async def test_cannot_read_other_users_items(authenticated_client, other_user_item):
    response = await authenticated_client.get(f"/items/{other_user_item.id}")
    assert response.status_code == 404  # not 403
```

```typescript
// Next.js API route test
import { GET } from "@/app/api/items/route";

jest.mock("@/lib/auth", () => ({
  getSession: jest.fn(),
}));

it("returns 401 when not authenticated", async () => {
  (getSession as jest.Mock).mockResolvedValue(null);
  const response = await GET(new Request("http://localhost/api/items"));
  expect(response.status).toBe(401);
});

it("returns only the current user's items", async () => {
  (getSession as jest.Mock).mockResolvedValue({
    user: { id: "user-1", email: "test@example.com" },
  });
  const response = await GET(new Request("http://localhost/api/items"));
  const body = await response.json();
  expect(body.data.every((item: any) => item.userId === "user-1")).toBe(true);
});
```

Rules:

- Use test fixtures with known user identities from seed data
- Never use real API keys or secrets in tests
- Mock the auth provider in unit tests — `getSession`, `verify_jwt`
- Use real auth in integration and E2E tests
- Test cross-user isolation: user A must not see user B's data
- Test that unauthorized access returns 404 (not 403) for resources that exist but belong to another user

NEVER:
- Store tokens in localStorage or sessionStorage
- Trust client-supplied user IDs — always extract from the verified token or session
- Return 403 for another user's resource — use 404 to avoid leaking existence
- Create service accounts that bypass user-scoped auth
- Skip auth checks on "internal" endpoints — every request carries a user identity
- Log or return token contents in error messages
- Use per-route auth checks instead of middleware
