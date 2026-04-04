"""Add extended yield fields for quality and moisture

Revision ID: 011
Revises: 010
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("yield_records", sa.Column("quality_grade", sa.String(length=10), nullable=True))
    op.add_column("yield_records", sa.Column("moisture_pct", sa.Float(), nullable=True))
    op.add_column("yield_records", sa.Column("notes", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("yield_records", "notes")
    op.drop_column("yield_records", "moisture_pct")
    op.drop_column("yield_records", "quality_grade")
