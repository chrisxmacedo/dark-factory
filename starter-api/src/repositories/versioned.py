"""
Versioned repository base class.

Provides standard create/supersede/query operations for any model
that uses VersionedMixin. Never issues UPDATE or DELETE statements.

Usage:
    class TariffRepository(VersionedRepository[Tariff, CreateTariffRequest]):

        async def create_first_version(
            self,
            data: CreateTariffRequest,
            created_by: uuid.UUID,
        ) -> Tariff:
            resource_id = uuid.uuid4()
            return await self.create_version(
                resource_id=resource_id,
                data=data,
                created_by=created_by,
                version_number=1,
            )

        async def update(
            self,
            resource_id: uuid.UUID,
            data: UpdateTariffRequest,
            created_by: uuid.UUID,
        ) -> Tariff:
            current = await self.get_current(resource_id)
            if not current:
                raise ValueError(f"Resource {resource_id} not found")
            return await self.supersede(
                current=current,
                data=data,
                created_by=created_by,
            )

    repo = TariffRepository(db, Tariff)
    tariff = await repo.create_first_version(data, user_id)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.versioned import VersionedMixin

ModelT = TypeVar("ModelT", bound=VersionedMixin)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)


class VersionedRepository(Generic[ModelT, CreateSchemaT]):
    def __init__(self, db: AsyncSession, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    # ── Write operations ──────────────────────────────────────────────────────

    async def create_version(
        self,
        resource_id: uuid.UUID,
        data: BaseModel,
        created_by: uuid.UUID | None,
        version_number: int = 1,
        extra_fields: dict[str, Any] | None = None,
    ) -> ModelT:
        """
        Insert a new version record. Does not supersede any existing version.
        Use supersede() when updating an existing resource.
        """
        fields = {
            **data.model_dump(),
            "resource_id": resource_id,
            "version_number": version_number,
            "is_current": True,
            "valid_from": datetime.now(UTC),
            "valid_to": None,
            "created_by": created_by,
            "superseded_by": None,
        }
        if extra_fields:
            fields.update(extra_fields)

        instance = self.model(**fields)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def supersede(
        self,
        current: ModelT,
        data: BaseModel,
        created_by: uuid.UUID | None,
        extra_fields: dict[str, Any] | None = None,
    ) -> ModelT:
        """
        Create a new version that supersedes the current one.
        Marks the current version as no longer active.
        """
        now = datetime.now(UTC)

        # Create the new version
        new_version = await self.create_version(
            resource_id=current.resource_id,  # type: ignore[attr-defined]
            data=data,
            created_by=created_by,
            version_number=current.version_number + 1,
            extra_fields=extra_fields,
        )

        # Mark the current version as superseded
        await self.db.execute(
            update(self.model)
            .where(self.model.id == current.id)  # type: ignore[attr-defined]
            .values(
                is_current=False,
                valid_to=now,
                superseded_by=new_version.id,
            )
        )

        return new_version

    # ── Read operations ───────────────────────────────────────────────────────

    async def get_current(self, resource_id: uuid.UUID) -> ModelT | None:
        """Get the current (latest) version of a resource."""
        result = await self.db.execute(
            select(self.model).where(
                self.model.resource_id == resource_id,  # type: ignore[attr-defined]
                self.model.is_current.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_version(self, version_id: uuid.UUID) -> ModelT | None:
        """Get a specific version by its version UUID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == version_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def list_versions(
        self,
        resource_id: uuid.UUID,
    ) -> list[ModelT]:
        """List all versions of a resource, newest first."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.resource_id == resource_id)  # type: ignore[attr-defined]
            .order_by(self.model.version_number.desc())  # type: ignore[attr-defined]
        )
        return list(result.scalars().all())

    async def get_at_point_in_time(
        self,
        resource_id: uuid.UUID,
        at: datetime,
    ) -> ModelT | None:
        """
        Get the version that was active at a specific point in time.
        Useful for regulatory queries: 'what were the tariffs on 2026-01-15?'
        """
        result = await self.db.execute(
            select(self.model)
            .where(
                self.model.resource_id == resource_id,  # type: ignore[attr-defined]
                self.model.valid_from <= at,
                (self.model.valid_to.is_(None)) | (self.model.valid_to > at),
            )
            .order_by(self.model.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_current(
        self,
        limit: int = 20,
        offset: int = 0,
        extra_filters: list[Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        """
        List current versions of all resources, with total count.
        Returns (items, total) for pagination.
        """
        from sqlalchemy import func, select

        base_query = select(self.model).where(
            self.model.is_current.is_(True)  # type: ignore[attr-defined]
        )

        if extra_filters:
            for f in extra_filters:
                base_query = base_query.where(f)

        # Total count
        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0

        # Paginated results
        result = await self.db.execute(
            base_query
            .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    # ── Diff ─────────────────────────────────────────────────────────────────

    def diff_versions(
        self,
        version_a: ModelT,
        version_b: ModelT,
        exclude_fields: set[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Compare two versions and return a dict of changed fields.

        Returns:
            {
                "field_name": {"from": old_value, "to": new_value},
                ...
            }
        """
        excluded = exclude_fields or {
            "id", "version_number", "is_current",
            "valid_from", "valid_to", "created_at",
            "created_by", "superseded_by",
        }

        a_dict = {
            k: v for k, v in version_a.__dict__.items()
            if not k.startswith("_") and k not in excluded
        }
        b_dict = {
            k: v for k, v in version_b.__dict__.items()
            if not k.startswith("_") and k not in excluded
        }

        changes: dict[str, dict[str, Any]] = {}
        all_keys = set(a_dict) | set(b_dict)

        for key in all_keys:
            a_val = a_dict.get(key)
            b_val = b_dict.get(key)
            if a_val != b_val:
                changes[key] = {"from": a_val, "to": b_val}

        return changes
