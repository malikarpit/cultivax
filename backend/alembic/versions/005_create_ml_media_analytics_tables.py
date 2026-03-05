"""Create ML, media, and analytics tables

Revision ID: 005
Revises: 004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('ml_models',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('model_type', sa.String(100), nullable=False),
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('accuracy', sa.Float, nullable=True),
        sa.Column('f1_score', sa.Float, nullable=True),
        sa.Column('training_metadata', JSONB, server_default='{}'),
        sa.Column('min_compatible_backend_version', sa.String(20), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('ml_training_audit',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', UUID(as_uuid=True), sa.ForeignKey('ml_models.id'), nullable=False),
        sa.Column('dataset_size', sa.Integer, nullable=False),
        sa.Column('training_duration_seconds', sa.Float, nullable=True),
        sa.Column('accuracy', sa.Float, nullable=True),
        sa.Column('loss', sa.Float, nullable=True),
        sa.Column('dataset_metadata', JSONB, server_default='{}'),
        sa.Column('triggered_by', UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('media_files',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('uploaded_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=True),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('analysis_status', sa.String(20), server_default='pending'),
        sa.Column('extracted_features', JSONB, server_default='{}'),
        sa.Column('stress_probability', sa.Float, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('frame_count', sa.Integer, nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('scheduled_deletion_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('stress_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_instance_id', UUID(as_uuid=True), sa.ForeignKey('crop_instances.id'), nullable=False),
        sa.Column('stress_score', sa.Float, nullable=False),
        sa.Column('stage', sa.String(100), nullable=True),
        sa.Column('day_number', sa.Float, nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('signal_breakdown', JSONB, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('regional_clusters',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_type', sa.String(100), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('season', sa.String(20), nullable=True),
        sa.Column('avg_delay', sa.Float, server_default='0.0'),
        sa.Column('avg_yield', sa.Float, server_default='0.0'),
        sa.Column('sample_size', sa.Integer, server_default='0'),
        sa.Column('std_dev_delay', sa.Float, nullable=True),
        sa.Column('std_dev_yield', sa.Float, nullable=True),
        sa.Column('confidence_interval_95', JSONB, server_default='{}'),
        sa.Column('last_updated_from_count', sa.Integer, server_default='0'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('regional_clusters')
    op.drop_table('stress_history')
    op.drop_table('media_files')
    op.drop_table('ml_training_audit')
    op.drop_table('ml_models')
