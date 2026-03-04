"""Create CTIS tables

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # crop_instances
    op.create_table(
        'crop_instances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('crop_type', sa.String(100), nullable=False),
        sa.Column('variety', sa.String(100), nullable=True),
        sa.Column('sowing_date', sa.Date, nullable=False),
        sa.Column('state', sa.String(50), nullable=False, server_default='Created'),
        sa.Column('stage', sa.String(100), nullable=True),
        sa.Column('current_day_number', sa.Integer, server_default='0'),
        sa.Column('stress_score', sa.Float, server_default='0.0'),
        sa.Column('risk_index', sa.Float, server_default='0.0'),
        sa.Column('seasonal_window_category', sa.String(20), nullable=True),
        sa.Column('land_area', sa.Float, nullable=True),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('sub_region', sa.String(100), nullable=True),
        sa.Column('rule_template_id', UUID(as_uuid=True), nullable=True),
        sa.Column('rule_template_version', sa.Integer, nullable=True),
        sa.Column('stage_offset_days', sa.Integer, server_default='0'),
        sa.Column('max_allowed_drift', sa.Integer, server_default='7'),
        sa.Column('last_risk_probability', sa.Float, nullable=True),
        sa.Column('last_inference_at', sa.String(50), nullable=True),
        sa.Column('metadata_extra', JSONB, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_crop_instances_farmer_id', 'crop_instances', ['farmer_id'])
    op.create_index('ix_crop_instances_state', 'crop_instances', ['state'])
    op.create_index('ix_crop_instances_crop_type', 'crop_instances', ['crop_type'])
    op.create_index('ix_crop_instances_region', 'crop_instances', ['region'])

    # action_logs
    op.create_table(
        'action_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='Operational'),
        sa.Column('metadata_json', JSONB, server_default='{}'),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('local_seq_no', sa.Integer, nullable=True),
        sa.Column('device_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('server_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('idempotency_key', sa.String(255), unique=True, nullable=True),
        sa.Column('applied_in_replay', sa.String(20), server_default='pending'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_action_logs_crop_instance_id', 'action_logs', ['crop_instance_id'])
    op.create_index('ix_action_logs_action_type', 'action_logs', ['action_type'])

    # crop_instance_snapshots
    op.create_table(
        'crop_instance_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('snapshot_data', JSONB, nullable=False),
        sa.Column('action_count_at_snapshot', sa.Integer, nullable=False),
        sa.Column('snapshot_version', sa.Integer, server_default='1'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # deviation_profiles
    op.create_table(
        'deviation_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), unique=True, nullable=False),
        sa.Column('consecutive_deviation_count', sa.Integer, server_default='0'),
        sa.Column('deviation_trend_slope', sa.Float, server_default='0.0'),
        sa.Column('recurring_pattern_flag', sa.Boolean, server_default='false'),
        sa.Column('last_deviation_type', sa.String(50), nullable=True),
        sa.Column('last_deviation_days', sa.Integer, server_default='0'),
        sa.Column('cumulative_deviation_days', sa.Integer, server_default='0'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # yield_records
    op.create_table(
        'yield_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('reported_yield', sa.Float, nullable=False),
        sa.Column('yield_unit', sa.String(20), server_default='kg/acre'),
        sa.Column('harvest_date', sa.Date, nullable=True),
        sa.Column('ml_yield_value', sa.Float, nullable=True),
        sa.Column('biological_cap', sa.Float, nullable=True),
        sa.Column('bio_cap_applied', sa.Boolean, server_default='false'),
        sa.Column('yield_verification_score', sa.Float, nullable=True),
        sa.Column('verification_metadata', JSONB, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('yield_records')
    op.drop_table('deviation_profiles')
    op.drop_table('crop_instance_snapshots')
    op.drop_table('action_logs')
    op.drop_table('crop_instances')
