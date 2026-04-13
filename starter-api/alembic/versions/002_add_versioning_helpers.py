"""add versioning helper functions and indexes

Revision ID: 002
Revises: 001
Create Date: 2026-03-15

Adds Postgres helper functions and indexes used by versioned models.
Individual versioned tables are created in later migrations (one per model).
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Helper function: get current version of any resource
    # Used for direct SQL queries and views
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_version(p_resource_id UUID, p_table TEXT)
        RETURNS UUID
        LANGUAGE plpgsql
        STABLE
        AS $$
        DECLARE
            v_id UUID;
        BEGIN
            EXECUTE format(
                'SELECT id FROM %I WHERE resource_id = $1 AND is_current = TRUE LIMIT 1',
                p_table
            ) INTO v_id USING p_resource_id;
            RETURN v_id;
        END;
        $$;
    """)

    # Helper function: get version active at a specific timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION get_version_at(
            p_resource_id UUID,
            p_table TEXT,
            p_at TIMESTAMPTZ
        )
        RETURNS UUID
        LANGUAGE plpgsql
        STABLE
        AS $$
        DECLARE
            v_id UUID;
        BEGIN
            EXECUTE format(
                'SELECT id FROM %I
                 WHERE resource_id = $1
                 AND valid_from <= $2
                 AND (valid_to IS NULL OR valid_to > $2)
                 ORDER BY version_number DESC
                 LIMIT 1',
                p_table
            ) INTO v_id USING p_resource_id, p_at;
            RETURN v_id;
        END;
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS get_version_at(UUID, TEXT, TIMESTAMPTZ)")
    op.execute("DROP FUNCTION IF EXISTS get_current_version(UUID, TEXT)")
