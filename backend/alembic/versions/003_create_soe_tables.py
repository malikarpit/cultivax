"""Create SOE tables

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'service_providers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('business_name', sa.String(255), nullable=True),
        sa.Column('service_type', sa.String(100), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('sub_region', sa.String(100), nullable=True),
        sa.Column('service_radius_km', sa.Float, nullable=True),
        sa.Column('crop_specializations', JSONB, server_default='[]'),
        sa.Column('trust_score', sa.Float, server_default='0.5'),
        sa.Column('is_verified', sa.Boolean, server_default='false'),
        sa.Column('verified_by', UUID(as_uuid=True), nullable=True),
        sa.Column('is_suspended', sa.Boolean, server_default='false'),
        sa.Column('suspension_reason', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'equipment',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_id', UUID(as_uuid=True), sa.ForeignKey('service_providers.id'), nullable=False),
        sa.Column('equipment_type', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('is_available', sa.Boolean, server_default='true'),
        sa.Column('hourly_rate', sa.Float, nullable=True),
        sa.Column('daily_rate', sa.Float, nullable=True),
        sa.Column('condition', sa.String(50), server_default='good'),
        sa.Column('is_flagged', sa.Boolean, server_default='false'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'service_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider_id', UUID(as_uuid=True), sa.ForeignKey('service_providers.id'), nullable=False),
        sa.Column('service_type', sa.String(100), nullable=False),
        sa.Column('crop_type', sa.String(100), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('requested_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='Pending'),
        sa.Column('provider_acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('agreed_price', sa.Float, nullable=True),
        sa.Column('final_price', sa.Float, nullable=True),
        sa.Column('metadata_json', JSONB, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'service_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', UUID(as_uuid=True), sa.ForeignKey('service_requests.id'), unique=True, nullable=False),
        sa.Column('reviewer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Float, nullable=False),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('complaint_category', sa.String(100), nullable=True),
        sa.Column('is_flagged', sa.String(20), server_default='none'),
        sa.Column('flagged_reason', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'provider_availability',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_id', UUID(as_uuid=True), sa.ForeignKey('service_providers.id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('is_available', sa.Boolean, server_default='true'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('provider_availability')
    op.drop_table('service_reviews')
    op.drop_table('service_requests')
    op.drop_table('equipment')
    op.drop_table('service_providers')
