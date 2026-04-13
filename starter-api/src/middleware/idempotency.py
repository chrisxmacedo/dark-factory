"""
Idempotency key middleware.

Accepts an Idempotency-Key header on write operations (POST, PATCH, PUT, DELETE).
If the same key is used again within the TTL window, the original response is
returned without re-executing the operation.

This allows AI agents to safely retry failed requests without creating duplicates.

Usage:
    All write endpoints automatically benefit from this middleware.
    Clients/agents should:
    1. Generate a unique key per logical operation (e.g. UUID)
    2. Include it as: Idempotency-Key: <uuid>
    3. On network failure, retry with the same key

The idempotency keys are stored in the Supabase `idempotency_keys` table
(created via Alembic migration).

TTL: 24 hours — keys older than this are ignored and the operation re-executes.
"""

import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.database import AsyncSessionLocal

logger = structlog.get_logger()

IDEMPOTENCY_TTL_HOURS = 24
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


async def idempotency_middleware(request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
    # Only apply to write operations
    if request.method not in WRITE_METHODS:
        return await call_next(request)

    idempotency_key = request.headers.get("Idempotency-Key")

    if not idempotency_key:
        return await call_next(request)

    # Validate key format
    try:
        uuid.UUID(idempotency_key)
    except ValueError:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_idempotency_key",
                    "message": "Idempotency-Key must be a valid UUID v4",
                }
            },
        )

    # Hash the key + path to namespace by endpoint
    cache_key = hashlib.sha256(
        f"{idempotency_key}:{request.url.path}".encode()
    ).hexdigest()

    async with AsyncSessionLocal() as session:
        # Check for existing response
        result = await session.execute(
            text("""
                SELECT status_code, response_body, created_at
                FROM idempotency_keys
                WHERE cache_key = :cache_key
                AND created_at > :cutoff
            """),
            {
                "cache_key": cache_key,
                "cutoff": datetime.now(UTC) - timedelta(hours=IDEMPOTENCY_TTL_HOURS),
            },
        )
        row = result.fetchone()

        if row:
            logger.info(
                "idempotency_cache_hit",
                idempotency_key=idempotency_key,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=row.status_code,
                content=json.loads(row.response_body),
                headers={"Idempotency-Key": idempotency_key, "X-Idempotent-Replayed": "true"},
            )

    # Execute the request
    response: Response = await call_next(request)

    # Cache successful responses only (2xx)
    if 200 <= response.status_code < 300:
        # Read response body
        body_bytes = b""
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body_bytes += chunk

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("""
                        INSERT INTO idempotency_keys (cache_key, status_code, response_body, created_at)
                        VALUES (:cache_key, :status_code, :response_body, :created_at)
                        ON CONFLICT (cache_key) DO NOTHING
                    """),
                    {
                        "cache_key": cache_key,
                        "status_code": response.status_code,
                        "response_body": body_bytes.decode("utf-8"),
                        "created_at": datetime.now(UTC),
                    },
                )
                await session.commit()
        except Exception:
            logger.exception("idempotency_cache_write_failed", cache_key=cache_key)

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                "Idempotency-Key": idempotency_key,
            },
            media_type=response.media_type,
        )

    return response
