"""Create remaining tables and add missing columns

Revision ID: 007
Revises: 006

Creates tables: crop_rule_templates, alerts, recommendations, labor,
service_request_events, pest_alert_history.

Adds missing columns to: crop_instances, action_logs, event_log,
service_providers, media_files.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # NEW TABLE: crop_rule_templates (MSDD 1.4)
    # ----------------------------------------------------------------
    op.create_table(
        'crop_rule_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_type', sa.String(100), nullable=False),
        sa.Column('variety', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('version_id', sa.String(50), nullable=False, server_default='1.0'),
        sa.Column('effective_from_date', sa.Date, nullable=False),
        sa.Column('is_active', sa.String(10), server_default='active'),
        sa.Column('stage_definitions', JSONB, server_default='[]'),
        sa.Column('risk_parameters', JSONB, server_default='{}'),
        sa.Column('irrigation_windows', JSONB, server_default='{}'),
        sa.Column('fertilizer_windows', JSONB, server_default='{}'),
        sa.Column('harvest_windows', JSONB, server_default='{}'),
        sa.Column('drift_limits', JSONB, server_default='{}'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_crop_rule_templates_crop_type', 'crop_rule_templates', ['crop_type'])

    # ----------------------------------------------------------------
    # NEW TABLE: alerts (MSDD Enhancement Sec 14)
    # ----------------------------------------------------------------
    op.create_table(
        'alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), server_default='info'),
        sa.Column('urgency_level', sa.String(20), server_default='Medium'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('source_event_id', UUID(as_uuid=True), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('ix_alerts_crop_instance_id', 'alerts', ['crop_instance_id'])
    op.create_index('ix_alerts_alert_type', 'alerts', ['alert_type'])

    # ----------------------------------------------------------------
    # NEW TABLE: recommendations (MSDD Enhancement Sec 15)
    # ----------------------------------------------------------------
    op.create_table(
        'recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('priority_rank', sa.Integer, server_default='0'),
        sa.Column('message_key', sa.String(100), nullable=False),
        sa.Column('message_parameters', JSONB, nullable=True),
        sa.Column('basis', sa.Text, nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_recommendations_crop', 'recommendations', ['crop_instance_id'])

    # ----------------------------------------------------------------
    # NEW TABLE: labor (MSDD 2.6)
    # ----------------------------------------------------------------
    op.create_table(
        'labor',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_id', UUID(as_uuid=True), sa.ForeignKey('service_providers.id'), nullable=False),
        sa.Column('labor_type', sa.String(100), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('available_units', sa.Integer, server_default='1'),
        sa.Column('daily_rate', sa.Float, nullable=True),
        sa.Column('hourly_rate', sa.Float, nullable=True),
        sa.Column('region', sa.String(200), nullable=False),
        sa.Column('sub_region', sa.String(200), nullable=True),
        sa.Column('is_available', sa.Boolean, server_default='true'),
        sa.Column('is_flagged', sa.Boolean, server_default='false'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_labor_provider', 'labor', ['provider_id'])
    op.create_index('ix_labor_region', 'labor', ['region'])

    # ----------------------------------------------------------------
    # NEW TABLE: service_request_events (SOE Enhancement 7)
    # ----------------------------------------------------------------
    op.create_table(
        'service_request_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', UUID(as_uuid=True), sa.ForeignKey('service_requests.id'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('previous_state', sa.String(50), nullable=True),
        sa.Column('new_state', sa.String(50), nullable=False),
        sa.Column('actor_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('actor_role', sa.String(50), nullable=True),
        sa.Column('transitioned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_sre_request_id', 'service_request_events', ['request_id'])

    # ----------------------------------------------------------------
    # NEW TABLE: pest_alert_history (MSDD Section 6 Enhancement)
    # ----------------------------------------------------------------
    op.create_table(
        'pest_alert_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('pest_type', sa.String(200), nullable=False),
        sa.Column('alert_level', sa.String(50), server_default='Low'),
        sa.Column('detected_by', sa.String(100), server_default='manual'),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('pest_density_index', sa.Float, nullable=True),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_pest_alert_crop', 'pest_alert_history', ['crop_instance_id'])

    # ================================================================
    # COLUMN ADDITIONS TO EXISTING TABLES
    # ================================================================

    # --- crop_instances ---
    op.add_column('crop_instances', sa.Column('baseline_day_number', sa.Integer, server_default='0'))
    op.add_column('crop_instances', sa.Column('baseline_growth_stage', sa.String(100), nullable=True))
    op.add_column('crop_instances', sa.Column('is_archived', sa.Boolean, server_default='false'))
    op.add_column('crop_instances', sa.Column('event_chain_hash', sa.String(255), nullable=True))

    # --- action_logs ---
    op.add_column('action_logs', sa.Column('action_subtype', sa.String(100), nullable=True))
    op.add_column('action_logs', sa.Column('action_impact_type', sa.String(50), server_default='Operational'))
    op.add_column('action_logs', sa.Column('source', sa.String(50), server_default='web'))
    op.add_column('action_logs', sa.Column('is_override', sa.Boolean, server_default='false'))
    op.add_column('action_logs', sa.Column('rule_version_at_action', sa.String(100), nullable=True))
    op.add_column('action_logs', sa.Column('is_orphaned', sa.Boolean, server_default='false'))

    # --- event_log ---
    op.add_column('event_log', sa.Column('module_target', sa.String(50), nullable=True))
    op.add_column('event_log', sa.Column('priority', sa.Integer, server_default='5'))
    op.add_column('event_log', sa.Column('chain_hash', sa.String(255), nullable=True))
    op.add_column('event_log', sa.Column('schema_version', sa.Integer, server_default='1'))

    # --- service_providers ---
    op.add_column('service_providers', sa.Column('complaint_count', sa.Integer, server_default='0'))
    op.add_column('service_providers', sa.Column('completion_count', sa.Integer, server_default='0'))
    op.add_column('service_providers', sa.Column('resolution_score', sa.Float, server_default='0.0'))
    op.add_column('service_providers', sa.Column('contact_name', sa.String(255), nullable=True))
    op.add_column('service_providers', sa.Column('contact_phone', sa.String(50), nullable=True))
    op.add_column('service_providers', sa.Column('is_flagged', sa.Boolean, server_default='false'))

    # --- media_files ---
    op.add_column('media_files', sa.Column('image_quality_score', sa.Float, nullable=True))
    op.add_column('media_files', sa.Column('pest_probability', sa.Float, nullable=True))
    op.add_column('media_files', sa.Column('analysis_source', sa.String(20), nullable=True))
    op.add_column('media_files', sa.Column('geo_verified', sa.Boolean, server_default='false'))


def downgrade() -> None:
    # Drop added columns (reverse order)
    op.drop_column('media_files', 'geo_verified')
    op.drop_column('media_files', 'analysis_source')
    op.drop_column('media_files', 'pest_probability')
    op.drop_column('media_files', 'image_quality_score')

    op.drop_column('service_providers', 'is_flagged')
    op.drop_column('service_providers', 'contact_phone')
    op.drop_column('service_providers', 'contact_name')
    op.drop_column('service_providers', 'resolution_score')
    op.drop_column('service_providers', 'completion_count')
    op.drop_column('service_providers', 'complaint_count')

    op.drop_column('event_log', 'schema_version')
    op.drop_column('event_log', 'chain_hash')
    op.drop_column('event_log', 'priority')
    op.drop_column('event_log', 'module_target')

    op.drop_column('action_logs', 'is_orphaned')
    op.drop_column('action_logs', 'rule_version_at_action')
    op.drop_column('action_logs', 'is_override')
    op.drop_column('action_logs', 'source')
    op.drop_column('action_logs', 'action_impact_type')
    op.drop_column('action_logs', 'action_subtype')

    op.drop_column('crop_instances', 'event_chain_hash')
    op.drop_column('crop_instances', 'is_archived')
    op.drop_column('crop_instances', 'baseline_growth_stage')
    op.drop_column('crop_instances', 'baseline_day_number')

    # Drop new tables
    op.drop_table('pest_alert_history')
    op.drop_table('service_request_events')
    op.drop_table('labor')
    op.drop_table('recommendations')
    op.drop_table('alerts')
    op.drop_table('crop_rule_templates')
