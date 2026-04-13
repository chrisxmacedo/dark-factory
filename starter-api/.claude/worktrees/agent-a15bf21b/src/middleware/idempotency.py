"""Pure ASGI idempotency middleware backed by Redis.

Accepts an optional Idempotency-Key header on POST, PATCH, DELETE requests.
If a duplicate key is received, the cached response is returned without
re-executing the request.

Keys expire after 24 hours. Uses Redis for storage so idempotency works
correctly across multiple replicas. Falls back gracefully when Redis is
unavailable (requests proceed without idempotency).
"""

import json
from typing import Any

from src.cache import cache_get, cache_set, get_redis_client

IDEMPOTENCY_HEADER = b"idempotency-key"
WRITE_METHODS = {b"POST", b"PATCH", b"DELETE"}
TTL_SECONDS = 86400  # 24 hours


def _get_header(headers: list[tuple[bytes, bytes]], name: bytes) -> bytes | None:
    for key, value in headers:
        if key.lower() == name:
            return value
    return None


class IdempotencyMiddleware:
    """ASGI middleware for idempotency key handling via Redis."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw_method = scope.get("method", "")
        method = raw_method.encode() if isinstance(raw_method, str) else b""

        if method not in WRITE_METHODS:
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        idem_key = _get_header(headers, IDEMPOTENCY_HEADER)

        if not idem_key:
            await self.app(scope, receive, send)
            return

        if not get_redis_client():
            await self.app(scope, receive, send)
            return

        auth_header = _get_header(headers, b"authorization")
        user_key = "anon"
        if auth_header:
            import hashlib

            user_key = hashlib.sha256(auth_header).hexdigest()[:16]

        idem_str = idem_key.decode("utf-8", errors="replace")
        cache_key = f"idempotency:{user_key}:{idem_str}"

        cached = await cache_get(cache_key)
        if cached is not None:
            cached_data = json.loads(cached)
            response_body = json.dumps(cached_data["body"]).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": cached_data["status"],
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(response_body)).encode()],
                        [b"x-idempotency-replay", b"true"],
                    ],
                }
            )
            await send({"type": "http.response.body", "body": response_body})
            return

        response_status = 200
        response_body = b""

        async def capture_send(message: dict[str, Any]) -> None:
            nonlocal response_status, response_body

            if message["type"] == "http.response.start":
                response_status = message["status"]
                await send(message)
            elif message["type"] == "http.response.body":
                body_chunk = message.get("body", b"")
                response_body += body_chunk
                await send(message)

        await self.app(scope, receive, capture_send)

        if 200 <= response_status < 300 and response_body:
            try:
                body_json = json.loads(response_body.decode("utf-8"))
                cache_data = json.dumps({"status": response_status, "body": body_json})
                await cache_set(cache_key, cache_data, TTL_SECONDS)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
