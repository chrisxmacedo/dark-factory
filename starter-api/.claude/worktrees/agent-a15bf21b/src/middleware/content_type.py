"""Pure ASGI middleware to enforce JSON:API content type on requests.

Rejects requests that have a body but don't use the expected content type.
Implemented as pure ASGI (not BaseHTTPMiddleware) to avoid event loop
issues with async SQLAlchemy.
"""

import json
from typing import Any

EXPECTED_CONTENT_TYPE = "application/json"
_EXEMPT_PATHS = {b"/health", b"/schema", b"/docs", b"/redoc", b"/openapi.json"}
_BODYLESS_METHODS = {b"GET", b"DELETE", b"HEAD", b"OPTIONS"}


class ContentTypeMiddleware:
    """ASGI middleware that enforces expected content type on request bodies."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw_path = scope.get("path", "")
        path = (
            raw_path.encode()
            if isinstance(raw_path, str)
            else scope.get("raw_path", b"")
        )
        raw_method = scope.get("method", "")
        method = raw_method.encode() if isinstance(raw_method, str) else b""

        path_stripped = path.rstrip(b"/") or path

        if path_stripped in _EXEMPT_PATHS or method in _BODYLESS_METHODS:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        ct_raw = headers.get(b"content-type", b"")
        content_type = ct_raw.decode("utf-8", errors="replace")

        if not content_type.startswith(EXPECTED_CONTENT_TYPE):
            error_body = json.dumps(
                {
                    "error": {
                        "code": "unsupported_media_type",
                        "message": (
                            f"Content-Type must be {EXPECTED_CONTENT_TYPE}, "
                            f"got {content_type!r}"
                        ),
                    }
                }
            ).encode("utf-8")

            await send(
                {
                    "type": "http.response.start",
                    "status": 415,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(error_body)).encode()],
                    ],
                }
            )
            await send({"type": "http.response.body", "body": error_body})
            return

        await self.app(scope, receive, send)
