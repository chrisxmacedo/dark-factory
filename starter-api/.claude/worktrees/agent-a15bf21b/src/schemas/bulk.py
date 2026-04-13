"""
Base schemas for bulk operations.

Bulk endpoints allow agents to create, update, or delete multiple resources
in a single request, reducing round-trips and improving efficiency.

Convention:
    POST /resource/bulk      — bulk create or upsert
    PATCH /resource/bulk     — bulk update
    DELETE /resource/bulk    — bulk delete

Usage:
    class CreateTariffRequest(BaseModel):
        name: str
        rate: float

    class TariffResponse(BaseModel):
        id: uuid.UUID
        name: str
        rate: float

    @router.post("/tariffs/bulk", response_model=BulkResponse[TariffResponse])
    async def bulk_create_tariffs(
        body: BulkCreateRequest[CreateTariffRequest],
        db: DB,
        current_user: RequireAuth,
    ) -> BulkResponse[TariffResponse]:
        results = []
        for item in body.items:
            tariff = await create_tariff(db, item)
            results.append(BulkResult(
                index=body.items.index(item),
                success=True,
                data=TariffResponse.model_validate(tariff),
            ))
        return BulkResponse(results=results)
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
R = TypeVar("R")


class BulkCreateRequest(BaseModel, Generic[T]):
    """Request body for bulk create operations."""

    items: list[T] = Field(
        description="List of items to create. Maximum 100 items per request.",
        max_length=100,
    )

    model_config = {"arbitrary_types_allowed": True}


class BulkUpdateRequest(BaseModel, Generic[T]):
    """Request body for bulk update operations."""

    items: list[T] = Field(
        description="List of items to update. Each item must include its ID.",
        max_length=100,
    )

    model_config = {"arbitrary_types_allowed": True}


class BulkDeleteRequest(BaseModel):
    """Request body for bulk delete operations."""

    ids: list[str] = Field(
        description="List of resource IDs to delete. Maximum 100 IDs per request.",
        max_length=100,
    )


class BulkResult(BaseModel, Generic[R]):
    """Result for a single item in a bulk operation."""

    index: int = Field(
        description="Zero-based index of this item in the original request array"
    )
    success: bool = Field(description="Whether this item was processed successfully")
    data: R | None = Field(
        None,
        description="The created/updated resource, if successful",
    )
    error: str | None = Field(
        None,
        description="Error message for this item, if unsuccessful",
    )

    model_config = {"arbitrary_types_allowed": True}


class BulkResponse(BaseModel, Generic[R]):
    """
    Response for bulk operations.

    Always returns 200 even if some items failed — check each result's
    success field. This allows agents to handle partial failures gracefully
    without retrying the entire batch.
    """

    results: list[BulkResult[R]] = Field(
        description="Results for each item in the request, in the same order"
    )
    succeeded: int = Field(description="Number of items processed successfully")
    failed: int = Field(description="Number of items that failed")

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_results(cls, results: list[BulkResult[R]]) -> BulkResponse[R]:
        return cls(
            results=results,
            succeeded=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success),
        )
