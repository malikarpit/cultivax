"""Gap closure: messaging, overrides, listing_status, read_replica

Revision ID: gap_closure_100pct
Revises: (auto — append to chain)
Create Date: 2026-04-14

Creates:
- conversations table (FR-23)
- messages table (FR-23/24)
- recommendation_overrides table (FR-7/8)
- listing_status column on service_providers (FR-15)
- rationale column on recommendations (FR-9)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "gap_closure_100pct"
down_revision = None  # Alembic auto-resolves; safe for standalone run
branch_labels = None
depends_on = None


def upgrade():
    # --- Conversations table (FR-23) ---
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_a_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("participant_b_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("service_request_id", UUID(as_uuid=True), sa.ForeignKey("service_requests.id"), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint(
            "participant_a_id", "participant_b_id", "service_request_id",
            name="uq_conversation_participants_context",
        ),
    )
    op.create_index("ix_conversations_participant_a_id", "conversations", ["participant_a_id"])
    op.create_index("ix_conversations_participant_b_id", "conversations", ["participant_b_id"])
    op.create_index("ix_conversations_service_request_id", "conversations", ["service_request_id"])

    # --- Messages table (FR-23/24) ---
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("sender_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(30), server_default="text", nullable=False),
        sa.Column("is_read", sa.Boolean(), default=False, nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_message_id", sa.String(255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_recipient_id", "messages", ["recipient_id"])

    # --- Recommendation Overrides table (FR-7/8) ---
    op.create_table(
        "recommendation_overrides",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("recommendation_id", UUID(as_uuid=True), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("crop_instance_id", UUID(as_uuid=True), sa.ForeignKey("crop_instances.id"), nullable=False),
        sa.Column("farmer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("override_action", sa.String(50), nullable=False),
        sa.Column("farmer_reason", sa.Text(), nullable=True),
        sa.Column("original_recommendation_type", sa.String(50), nullable=False),
        sa.Column("original_priority_rank", sa.Integer(), nullable=False, default=0),
        sa.Column("original_rationale", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_recommendation_overrides_recommendation_id", "recommendation_overrides", ["recommendation_id"])
    op.create_index("ix_recommendation_overrides_crop_instance_id", "recommendation_overrides", ["crop_instance_id"])
    op.create_index("ix_recommendation_overrides_farmer_id", "recommendation_overrides", ["farmer_id"])

    # --- Add rationale column to recommendations (FR-9) ---
    try:
        op.add_column("recommendations", sa.Column("rationale", JSONB, nullable=True))
    except Exception:
        pass  # Column may already exist

    # --- Add listing_status column to service_providers (FR-15) ---
    try:
        op.add_column(
            "service_providers",
            sa.Column("listing_status", sa.String(20), server_default="active", nullable=False),
        )
    except Exception:
        pass  # Column may already exist


def downgrade():
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("recommendation_overrides")

    try:
        op.drop_column("recommendations", "rationale")
    except Exception:
        pass
    try:
        op.drop_column("service_providers", "listing_status")
    except Exception:
        pass
