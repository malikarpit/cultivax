"""Create regional sowing calendars table

Revision ID: 006
Revises: 005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'regional_sowing_calendars',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_type', sa.String(100), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('optimal_start', sa.Date, nullable=False),
        sa.Column('optimal_end', sa.Date, nullable=False),
        sa.Column('version_id', sa.Integer, server_default='1'),
        sa.Column('effective_from_date', sa.Date, nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_sowing_cal_crop_region', 'regional_sowing_calendars', ['crop_type', 'region'])


def downgrade() -> None:
    op.drop_table('regional_sowing_calendars')
