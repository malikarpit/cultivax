"""Create users table

Revision ID: 001
Revises: None
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='farmer'),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('preferred_language', sa.String(10), server_default='en'),
        sa.Column('accessibility_settings', JSONB, server_default='{}'),
        sa.Column('is_onboarded', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_phone', 'users', ['phone'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_region', 'users', ['region'])


def downgrade() -> None:
    op.drop_table('users')
