"""
Messaging API — FR-23, FR-24, FR-25, NFR-14

In-app messaging endpoints for farmer↔provider communication.

All endpoints require JWT auth (NFR-14).
Contact sharing requires mutual consent (FR-25).
Offline-synced messages use client_message_id for dedup (FR-24).
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["Messaging"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class CreateConversationRequest(BaseModel):
    participant_id: UUID
    service_request_id: Optional[UUID] = None
    initial_message: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"  # text | contact_share
    client_message_id: Optional[str] = None  # FR-24: offline dedup


class ConversationResponse(BaseModel):
    id: UUID
    participant_a_id: UUID
    participant_b_id: UUID
    service_request_id: Optional[UUID] = None
    last_message_at: Optional[datetime] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    recipient_id: UUID
    content: str
    message_type: str
    is_read: bool
    read_at: Optional[datetime] = None
    client_message_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    dependencies=[Depends(require_role(["farmer", "provider", "admin"]))],
)
async def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """List all conversations for the current user."""
    offset = (page - 1) * page_size
    conversations = (
        db.query(Conversation)
        .filter(
            or_(
                Conversation.participant_a_id == current_user.id,
                Conversation.participant_b_id == current_user.id,
            ),
            Conversation.is_deleted == False,
        )
        .order_by(Conversation.last_message_at.desc().nullslast())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["farmer", "provider", "admin"]))],
)
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation or return existing one."""
    if request.participant_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    # Check if participant exists
    participant = (
        db.query(User)
        .filter(User.id == request.participant_id, User.is_deleted == False)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Normalize participant order (smaller UUID first) for uniqueness
    a_id, b_id = sorted([current_user.id, request.participant_id])

    # Check for existing conversation
    existing = (
        db.query(Conversation)
        .filter(
            Conversation.participant_a_id == a_id,
            Conversation.participant_b_id == b_id,
            Conversation.service_request_id == request.service_request_id,
            Conversation.is_deleted == False,
        )
        .first()
    )
    if existing:
        return ConversationResponse.model_validate(existing)

    conv = Conversation(
        participant_a_id=a_id,
        participant_b_id=b_id,
        service_request_id=request.service_request_id,
        status="active",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Send initial message if provided
    if request.initial_message:
        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            recipient_id=request.participant_id,
            content=request.initial_message,
            message_type="text",
        )
        db.add(msg)
        conv.last_message_at = datetime.now(timezone.utc)
        db.commit()

    return ConversationResponse.model_validate(conv)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
    dependencies=[Depends(require_role(["farmer", "provider", "admin"]))],
)
async def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Get paginated message history for a conversation."""
    conv = _get_conversation_for_user(db, conversation_id, current_user.id)

    offset = (page - 1) * page_size
    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conv.id,
            Message.is_deleted == False,
        )
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [MessageResponse.model_validate(m) for m in messages]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["farmer", "provider", "admin"]))],
)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message in a conversation."""
    conv = _get_conversation_for_user(db, conversation_id, current_user.id)

    # FR-25: Contact sharing requires mutual consent
    if request.message_type == "contact_share":
        from app.middleware.consent_guard import check_contact_sharing_consent

        recipient_id = (
            conv.participant_b_id
            if conv.participant_a_id == current_user.id
            else conv.participant_a_id
        )
        if not check_contact_sharing_consent(current_user.id, recipient_id, db):
            raise HTTPException(
                status_code=403,
                detail="Mutual consent required for contact sharing (FR-25)",
            )

    # FR-24: Deduplicate offline-synced messages
    if request.client_message_id:
        existing = (
            db.query(Message)
            .filter(
                Message.client_message_id == request.client_message_id,
                Message.is_deleted == False,
            )
            .first()
        )
        if existing:
            return MessageResponse.model_validate(existing)

    recipient_id = (
        conv.participant_b_id
        if conv.participant_a_id == current_user.id
        else conv.participant_a_id
    )

    msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=request.content,
        message_type=request.message_type,
        client_message_id=request.client_message_id,
    )
    db.add(msg)

    conv.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)

    return MessageResponse.model_validate(msg)


@router.patch(
    "/conversations/{conversation_id}/messages/{message_id}/read",
    response_model=MessageResponse,
    dependencies=[Depends(require_role(["farmer", "provider", "admin"]))],
)
async def mark_message_read(
    conversation_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a message as read."""
    conv = _get_conversation_for_user(db, conversation_id, current_user.id)

    msg = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.conversation_id == conv.id,
            Message.recipient_id == current_user.id,
            Message.is_deleted == False,
        )
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if not msg.is_read:
        msg.is_read = True
        msg.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(msg)

    return MessageResponse.model_validate(msg)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_conversation_for_user(
    db: Session, conversation_id: UUID, user_id: UUID
) -> Conversation:
    """Fetch conversation and verify user is a participant."""
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if user_id not in (conv.participant_a_id, conv.participant_b_id):
        raise HTTPException(
            status_code=403, detail="You are not a participant in this conversation"
        )

    return conv
