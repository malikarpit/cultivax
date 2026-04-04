"""012: Fix TimestampMixin drift on exposure_logs and weather_snapshots

Closes model-DB drift detected by `alembic check`:

exposure_logs:
  - Add TimestampMixin columns (created_at, updated_at)
  - Add soft-delete columns (is_deleted, deleted_at, deleted_by)
  - Data-migrate: copy shown_at → created_at for existing rows
  - Drop shown_at column
  - Rebuild indexes to reference created_at instead of shown_at
  - Add is_deleted index

weather_snapshots:
  - Add TimestampMixin columns (created_at, updated_at)
  - Add soft-delete columns (is_deleted, deleted_at, deleted_by)
  - Alter captured_at + expires_at: TIMESTAMP → DateTime(timezone=True)
  - Add is_deleted index

Revision ID: 012_drift_fix
Revises: 6afd114c0415
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "012_drift_fix"
down_revision: Union[str, None] = "6afd114c0415"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. exposure_logs — add TimestampMixin + soft-delete columns
    # -----------------------------------------------------------------------
    op.add_column(
        "exposure_logs",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "exposure_logs",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "exposure_logs",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "exposure_logs",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "exposure_logs",
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )

    # Copy existing shown_at → created_at (data migration, single atomic UPDATE)
    op.execute(
        "UPDATE exposure_logs SET created_at = shown_at WHERE shown_at IS NOT NULL"
    )

    # Drop old indexes that reference shown_at
    op.drop_index("ix_exposure_logs_provider_shown", table_name="exposure_logs")
    op.drop_index("ix_exposure_logs_region_shown", table_name="exposure_logs")

    # Drop shown_at column
    op.drop_column("exposure_logs", "shown_at")

    # Recreate indexes referencing created_at
    op.create_index(
        "ix_exposure_logs_provider_shown",
        "exposure_logs",
        ["provider_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_exposure_logs_region_shown",
        "exposure_logs",
        ["region", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_exposure_logs_is_deleted",
        "exposure_logs",
        ["is_deleted"],
        unique=False,
    )

    # -----------------------------------------------------------------------
    # 2. weather_snapshots — add TimestampMixin + soft-delete columns
    # -----------------------------------------------------------------------
    op.add_column(
        "weather_snapshots",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "weather_snapshots",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "weather_snapshots",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "weather_snapshots",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "weather_snapshots",
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_weather_snapshots_is_deleted",
        "weather_snapshots",
        ["is_deleted"],
        unique=False,
    )

    # Alter captured_at / expires_at: TIMESTAMP → TIMESTAMPTZ
    op.alter_column(
        "weather_snapshots",
        "captured_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        "weather_snapshots",
        "expires_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # -----------------------------------------------------------------------
    # Reverse: weather_snapshots
    # -----------------------------------------------------------------------
    op.alter_column(
        "weather_snapshots",
        "expires_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "weather_snapshots",
        "captured_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.drop_index("ix_weather_snapshots_is_deleted", table_name="weather_snapshots")
    for col in ("deleted_by", "deleted_at", "is_deleted", "updated_at", "created_at"):
        op.drop_column("weather_snapshots", col)

    # -----------------------------------------------------------------------
    # Reverse: exposure_logs — restore shown_at
    # -----------------------------------------------------------------------
    op.drop_index("ix_exposure_logs_is_deleted", table_name="exposure_logs")
    op.drop_index("ix_exposure_logs_region_shown", table_name="exposure_logs")
    op.drop_index("ix_exposure_logs_provider_shown", table_name="exposure_logs")

    op.add_column(
        "exposure_logs",
        sa.Column(
            "shown_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    # Restore shown_at from created_at
    op.execute("UPDATE exposure_logs SET shown_at = created_at")

    op.create_index(
        "ix_exposure_logs_provider_shown",
        "exposure_logs",
        ["provider_id", "shown_at"],
        unique=False,
    )
    op.create_index(
        "ix_exposure_logs_region_shown",
        "exposure_logs",
        ["region", "shown_at"],
        unique=False,
    )

    for col in ("deleted_by", "deleted_at", "is_deleted", "updated_at", "created_at"):
        op.drop_column("exposure_logs", col)
