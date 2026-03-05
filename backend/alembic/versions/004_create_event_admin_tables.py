"""Create event and admin tables

Revision ID: 004
Revises: 003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'event_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('payload', JSONB, server_default='{}'),
        sa.Column('partition_key', UUID(as_uuid=True), nullable=False),
        sa.Column('event_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='Created'),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('failure_reason', sa.String(1000), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_event_log_status', 'event_log', ['status'])
    op.create_index('ix_event_log_partition_key', 'event_log', ['partition_key'])

    op.create_table(
        'admin_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('admin_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('before_value', JSONB, nullable=True),
        sa.Column('after_value', JSONB, nullable=True),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'feature_flags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('flag_name', sa.String(100), unique=True, nullable=False),
        sa.Column('is_enabled', sa.Boolean, server_default='false'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('scope', sa.String(20), server_default='global'),
        sa.Column('scope_value', sa.String(100), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'abuse_flags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('flag_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), server_default='low'),
        sa.Column('anomaly_score', sa.Float, nullable=True),
        sa.Column('details', JSONB, server_default='{}'),
        sa.Column('status', sa.String(20), server_default='open'),
        sa.Column('resolved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('abuse_flags')
    op.drop_table('feature_flags')
    op.drop_table('admin_audit_log')
    op.drop_table('event_log')
