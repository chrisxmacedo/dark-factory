"""
Standard response envelope for all API endpoints.

All endpoints must wrap their responses in these schemas so that AI agents
and clients have a consistent, predictable shape to parse across all operations.

Usage:
    # Single resource
    @router.get("/items/{id}", response_model=DataResponse[ItemResponse])
    async def get_item(id: uuid.UUID) -> DataResponse[ItemResponse]:
        item = await fetch_item(id)
        return DataResponse(data=item)

    # Collection with pagination
    @router.get("/items", response_model=CollectionResponse[ItemResponse])
    async def list_items(...) -> CollectionResponse[ItemResponse]:
        items, total = await fetch_items(...)
        return CollectionResponse.paginate(
            data=items,
            total=total,
            page=page,
            page_size=page_size,
            base_url=str(request.url),
        )

    # Error (usually raised via HTTPException, but can be returned directly)
    return ErrorResponse(
        error=ErrorDetail(code="not_found", message="Item not found")
    )
"""

from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Pagination ────────────────────────────────────────────────────────────────


class PaginationLinks(BaseModel):
    self: str = Field(description="URL of the current page")
    next: str | None = Field(None, description="URL of the next page, if any")
    prev: str | None = Field(None, description="URL of the previous page, if any")
    first: str = Field(description="URL of the first page")
    last: str = Field(description="URL of the last page")


class PaginationMeta(BaseModel):
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")


# ── Response envelopes ────────────────────────────────────────────────────────


class DataResponse(BaseModel, Generic[T]):
    """Single resource response."""

    data: T = Field(description="The requested resource")

    model_config = {"arbitrary_types_allowed": True}


class CollectionResponse(BaseModel, Generic[T]):
    """Paginated collection response."""

    data: list[T] = Field(description="List of resources for the current page")
    meta: PaginationMeta = Field(description="Pagination metadata")
    links: PaginationLinks = Field(description="Pagination navigation links")

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def paginate(
        cls,
        data: list[T],
        total: int,
        page: int,
        page_size: int,
        base_url: str,
    ) -> CollectionResponse[T]:
        """Build a paginated response with navigation links."""
        total_pages = max(1, math.ceil(total / page_size))

        # Strip existing page param from URL
        base = base_url.split("?")[0]

        def page_url(p: int) -> str:
            return f"{base}?page={p}&page_size={page_size}"

        return cls(
            data=data,
            meta=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
            links=PaginationLinks(
                self=page_url(page),
                next=page_url(page + 1) if page < total_pages else None,
                prev=page_url(page - 1) if page > 1 else None,
                first=page_url(1),
                last=page_url(total_pages),
            ),
        )


# ── Error envelope ────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str = Field(
        description=(
            "Machine-readable error code. "
            "Agents should use this field to handle errors programmatically. "
            "Examples: not_found, validation_error, unauthorized, conflict, "
            "rate_limited, internal_error"
        )
    )
    message: str = Field(description="Human-readable error description")
    field: str | None = Field(
        None,
        description="The field that caused the error, for validation errors",
    )


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(description="Error details")


# ── Pagination query params ───────────────────────────────────────────────────


class PaginationParams(BaseModel):
    """Reusable pagination query parameters. Use as a FastAPI dependency."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
