"""Per-role rate limiting.

Keys on user ID from the JWT. Falls back to IP address for
unauthenticated requests (public endpoints).
"""

from fastapi import Request, Response, status

ROLE_LIMITS: dict[str, int] = {
    "admin": 120,
    "supplier": 60,
    "consumer": 120,
}
DEFAULT_LIMIT = 60


def get_rate_limit_key(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return str(user.id)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "rate_limited",
                "message": str(exc),
            }
        },
    )
