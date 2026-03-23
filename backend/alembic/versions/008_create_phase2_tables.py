"""Create tables: ml_feedback, system_health, market_prices,
deviation_profile_archive, backup_verification_logs, land_parcels,
whatsapp_sessions, farmer_action_audit_log.

Revision ID: 008
Revises: 007
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # ml_feedback — farmer feedback on ML predictions
    # ----------------------------------------------------------------
    op.create_table(
        'ml_feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('prediction_id', sa.String(255), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('farmer_notes', sa.String(1000), nullable=True),
        sa.Column('original_prediction', JSONB, nullable=True),
        sa.Column('original_confidence', sa.Float, nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_ml_feedback_crop', 'ml_feedback', ['crop_instance_id'])

    # ----------------------------------------------------------------
    # system_health — subsystem health monitoring
    # ----------------------------------------------------------------
    op.create_table(
        'system_health',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('subsystem', sa.String(50), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='Operational'),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('details', JSONB, server_default='{}'),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ----------------------------------------------------------------
    # market_prices — regional crop pricing with staleness detection
    # ----------------------------------------------------------------
    op.create_table(
        'market_prices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_type', sa.String(100), nullable=False),
        sa.Column('variety', sa.String(100), nullable=True),
        sa.Column('region', sa.String(200), nullable=False),
        sa.Column('price_per_unit', sa.Float, nullable=False),
        sa.Column('unit', sa.String(20), server_default='kg'),
        sa.Column('currency', sa.String(10), server_default='INR'),
        sa.Column('price_date', sa.Date, nullable=False),
        sa.Column('source_provider', sa.String(200), nullable=True),
        sa.Column('is_stale', sa.Boolean, server_default='false'),
        sa.Column('staleness_threshold_hours', sa.Float, server_default='24.0'),
        sa.Column('metadata_extra', JSONB, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_market_prices_crop', 'market_prices', ['crop_type'])
    op.create_index('ix_market_prices_region', 'market_prices', ['region'])

    # ----------------------------------------------------------------
    # deviation_profile_archive — seasonal deviation history
    # ----------------------------------------------------------------
    op.create_table(
        'deviation_profile_archive',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('crop_type', sa.String(100), nullable=False),
        sa.Column('season', sa.String(50), nullable=False),
        sa.Column('archived_profile', JSONB, nullable=False, server_default='{}'),
        sa.Column('archived_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_deviation_archive_farmer', 'deviation_profile_archive', ['farmer_id'])

    # ----------------------------------------------------------------
    # backup_verification_logs — backup audit trail
    # ----------------------------------------------------------------
    op.create_table(
        'backup_verification_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('backup_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('backup_type', sa.String(50), server_default='full'),
        sa.Column('restore_tested', sa.Boolean, server_default='false'),
        sa.Column('restore_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.String(20), server_default='pending'),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ----------------------------------------------------------------
    # land_parcels — farmer land registry
    # ----------------------------------------------------------------
    op.create_table(
        'land_parcels',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('parcel_name', sa.String(255), nullable=False),
        sa.Column('region', sa.String(200), nullable=False),
        sa.Column('sub_region', sa.String(200), nullable=True),
        sa.Column('land_area', sa.Float, nullable=True),
        sa.Column('land_area_unit', sa.String(20), server_default='acres'),
        sa.Column('soil_type', JSONB, server_default='{}'),
        sa.Column('gps_coordinates', JSONB, server_default='{}'),
        sa.Column('irrigation_source', sa.String(100), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_land_parcels_farmer', 'land_parcels', ['farmer_id'])

    # ----------------------------------------------------------------
    # whatsapp_sessions — chatbot session management
    # ----------------------------------------------------------------
    op.create_table(
        'whatsapp_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_phone', sa.String(20), nullable=False),
        sa.Column('session_type', sa.String(50), server_default='general'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('context_data', JSONB, server_default='{}'),
        sa.Column('language', sa.String(10), server_default='hi'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_whatsapp_sessions_phone', 'whatsapp_sessions', ['farmer_phone'])

    # ----------------------------------------------------------------
    # farmer_action_audit_log — farmer action audit trail
    # ----------------------------------------------------------------
    op.create_table(
        'farmer_action_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('channel', sa.String(20), nullable=True),
        sa.Column('details', JSONB, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_farmer_audit_farmer', 'farmer_action_audit_log', ['farmer_id'])
    op.create_index('ix_farmer_audit_action', 'farmer_action_audit_log', ['action_type'])


def downgrade() -> None:
    op.drop_table('farmer_action_audit_log')
    op.drop_table('whatsapp_sessions')
    op.drop_table('land_parcels')
    op.drop_table('backup_verification_logs')
    op.drop_table('deviation_profile_archive')
    op.drop_table('market_prices')
    op.drop_table('system_health')
    op.drop_table('ml_feedback')
