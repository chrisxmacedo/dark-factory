"""
Version router factory.

Generates standard versioning endpoints for any versioned resource.
Attach to any router that manages a versioned model.

Usage:
    from src.routers.versions import create_version_router
    from src.models.tariff import Tariff
    from src.schemas.tariff import TariffVersionResponse

    tariff_version_router = create_version_router(
        model=Tariff,
        response_schema=TariffVersionResponse,
        prefix="/suppliers/{supplier_id}/tariffs/{resource_id}",
        tags=["tariffs"],
    )

    # This adds these endpoints to your router:
    # GET /suppliers/{supplier_id}/tariffs/{resource_id}/versions
    # GET /suppliers/{supplier_id}/tariffs/{resource_id}/versions/{version_id}
    # GET /suppliers/{supplier_id}/tariffs/{resource_id}/versions/{v1}/diff/{v2}
    # GET /suppliers/{supplier_id}/tariffs/{resource_id}/at/{timestamp}
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel

from src.dependencies import DB, RequireAuth
from src.models.versioned import VersionedMixin
from src.repositories.versioned import VersionedRepository
from src.schemas.envelope import CollectionResponse, DataResponse

ModelT = TypeVar("ModelT", bound=VersionedMixin)
ResponseT = TypeVar("ResponseT", bound=BaseModel)


class DiffResponse(BaseModel):
    resource_id: uuid.UUID
    version_a: uuid.UUID
    version_b: uuid.UUID
    version_a_number: int
    version_b_number: int
    changes: dict[str, dict[str, Any]]


def create_version_router(
    model: type[Any],
    response_schema: type[Any],
    prefix: str,
    tags: list[str],
) -> APIRouter:
    """
    Factory that returns an APIRouter with standard versioning endpoints.

    Attach the returned router to your main app or parent router.
    """
    router = APIRouter(prefix=prefix, tags=tags)

    @router.get(
        "/versions",
        response_model=CollectionResponse[response_schema],
        summary="List all versions",
        description=(
            "Returns all versions of this resource in reverse chronological order. "
            "The first item is always the current version. "
            "AI agents can use this to understand the full history of a resource."
        ),
        responses={
            404: {"description": "Resource not found"},
        },
        openapi_extra={
            "x-agent-hints": {
                "idempotent": True,
                "auth_required": True,
                "use_for": "Retrieve full version history of a resource",
            }
        },
    )
    async def list_versions(
        resource_id: uuid.UUID = Path(..., description="The stable resource identity UUID"),
        db: DB = Depends(),
        current_user: RequireAuth = Depends(),
    ) -> CollectionResponse[Any]:
        repo = VersionedRepository(db, model)
        versions = await repo.list_versions(resource_id)
        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Resource not found"},
            )
        validated = [response_schema.model_validate(v) for v in versions]
        return CollectionResponse.paginate(
            data=validated,
            total=len(validated),
            page=1,
            page_size=len(validated),
            base_url=f"{prefix}/versions",
        )

    @router.get(
        "/versions/{version_id}",
        response_model=DataResponse[response_schema],
        summary="Get a specific version",
        description=(
            "Returns a specific version of this resource by its version UUID. "
            "Use this for point-in-time compliance queries or to inspect "
            "a historical version before diffing."
        ),
        responses={
            404: {"description": "Version not found"},
        },
        openapi_extra={
            "x-agent-hints": {
                "idempotent": True,
                "auth_required": True,
                "use_for": "Retrieve a specific historical version of a resource",
            }
        },
    )
    async def get_version(
        resource_id: uuid.UUID = Path(..., description="The stable resource identity UUID"),
        version_id: uuid.UUID = Path(..., description="The version UUID to retrieve"),
        db: DB = Depends(),
        current_user: RequireAuth = Depends(),
    ) -> DataResponse[Any]:
        repo = VersionedRepository(db, model)
        version = await repo.get_version(version_id)
        if not version or version.resource_id != resource_id:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Version not found"},
            )
        return DataResponse(data=response_schema.model_validate(version))

    @router.get(
        "/versions/{version_a_id}/diff/{version_b_id}",
        response_model=DiffResponse,
        summary="Diff two versions",
        description=(
            "Returns the field-level differences between two versions of this resource. "
            "AI agents can use this to understand exactly what changed between versions, "
            "useful for generating changelogs or detecting price movements."
        ),
        responses={
            404: {"description": "One or both versions not found"},
            422: {"description": "Versions belong to different resources"},
        },
        openapi_extra={
            "x-agent-hints": {
                "idempotent": True,
                "auth_required": True,
                "use_for": "Compare two versions to understand what changed",
            }
        },
    )
    async def diff_versions(
        resource_id: uuid.UUID = Path(...),
        version_a_id: uuid.UUID = Path(..., description="UUID of the first version"),
        version_b_id: uuid.UUID = Path(..., description="UUID of the second version"),
        db: DB = Depends(),
        current_user: RequireAuth = Depends(),
    ) -> DiffResponse:
        repo = VersionedRepository(db, model)
        version_a = await repo.get_version(version_a_id)
        version_b = await repo.get_version(version_b_id)

        if not version_a or version_a.resource_id != resource_id:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Version A not found"},
            )
        if not version_b or version_b.resource_id != resource_id:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Version B not found"},
            )

        changes = repo.diff_versions(version_a, version_b)
        return DiffResponse(
            resource_id=resource_id,
            version_a=version_a_id,
            version_b=version_b_id,
            version_a_number=version_a.version_number,
            version_b_number=version_b.version_number,
            changes=changes,
        )

    @router.get(
        "/at/{timestamp}",
        response_model=DataResponse[response_schema],
        summary="Get version at point in time",
        description=(
            "Returns the version of this resource that was active at a specific timestamp. "
            "Use ISO 8601 format: 2026-01-15T00:00:00Z. "
            "Essential for regulatory queries: 'what was the tariff rate on date X?'"
        ),
        responses={
            404: {"description": "No version found for this resource at the given time"},
        },
        openapi_extra={
            "x-agent-hints": {
                "idempotent": True,
                "auth_required": True,
                "use_for": (
                    "Point-in-time queries — retrieve the state of a resource "
                    "as it was at a specific date/time"
                ),
            }
        },
    )
    async def get_at_point_in_time(
        resource_id: uuid.UUID = Path(...),
        timestamp: datetime = Path(..., description="ISO 8601 timestamp, e.g. 2026-01-15T00:00:00Z"),
        db: DB = Depends(),
        current_user: RequireAuth = Depends(),
    ) -> DataResponse[Any]:
        repo = VersionedRepository(db, model)
        version = await repo.get_at_point_in_time(resource_id, timestamp)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": f"No version found for this resource at {timestamp.isoformat()}",
                },
            )
        return DataResponse(data=response_schema.model_validate(version))

    return router
