"""
Versioned model mixin.

Any model that inherits from VersionedMixin gets full immutable versioning.
Records are never updated or deleted — each change creates a new version.

Usage:
    class Tariff(VersionedMixin, Base):
        __tablename__ = "tariffs"

        # Resource identity (shared across all versions of the same tariff)
        resource_id: Mapped[uuid.UUID] = mapped_column(
            UUID(as_uuid=True),
            nullable=False,
            index=True,
        )

        # Your resource-specific fields
        name: Mapped[str] = mapped_column(String(255), nullable=False)
        rate: Mapped[float] = mapped_column(nullable=False)

The versioning fields (id, version_number, is_current, valid_from, valid_to,
created_by, superseded_by) are provided by the mixin.

Conventions:
- `id` is the version UUID — unique per version
- `resource_id` is the stable identity across versions — defined per model
- `is_current` is True only for the latest version of each resource_id
- `valid_to` is NULL for the current version, set when superseded
- Never UPDATE or DELETE rows — always INSERT a new version
- Use VersionedRepository for all write operations
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class VersionedMixin:
    """
    Mixin for immutable versioned models.

    Inherit from this alongside Base for any model that requires
    full version history with point-in-time queries.
    """

    # Version identity
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique ID for this specific version",
    )

    # Version sequence
    version_number: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        default=1,
        comment="Sequential version number within this resource_id (1, 2, 3...)",
    )

    # Current version flag
    is_current: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
        index=True,
        comment="True only for the latest version of each resource_id",
    )

    # Validity window
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this version became active",
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="When this version was superseded. NULL means currently active.",
    )

    # Authorship
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this version record was created",
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of the user who created this version",
    )

    # Chain
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
        comment="ID of the version that replaced this one. NULL if still current.",
    )
