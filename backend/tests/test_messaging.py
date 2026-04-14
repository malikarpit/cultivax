"""
Test Messaging System — FR-23, FR-24, FR-25, NFR-14

Tests in-app messaging models and API behavior.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone


class TestMessaging:
    """Tests for the in-app messaging system."""

    def test_conversation_model_fields(self):
        """Conversation model should have required fields."""
        from app.models.conversation import Conversation

        conv = Conversation(
            participant_a_id=uuid4(),
            participant_b_id=uuid4(),
            status="active",
        )
        assert conv.participant_a_id is not None
        assert conv.participant_b_id is not None
        assert conv.status == "active"

    def test_message_model_fields(self):
        """Message model should have required fields."""
        from app.models.message import Message

        msg = Message(
            conversation_id=uuid4(),
            sender_id=uuid4(),
            recipient_id=uuid4(),
            content="Hello, farmer!",
            message_type="text",
        )
        assert msg.content == "Hello, farmer!"
        assert msg.message_type == "text"
        assert msg.is_read is False or msg.is_read == False

    def test_message_type_contact_share(self):
        """Contact share messages should have message_type='contact_share'."""
        from app.models.message import Message

        msg = Message(
            conversation_id=uuid4(),
            sender_id=uuid4(),
            recipient_id=uuid4(),
            content='{"name": "John", "phone": "+91-1234567890"}',
            message_type="contact_share",
        )
        assert msg.message_type == "contact_share"

    def test_offline_dedup_via_client_message_id(self):
        """Messages should support client_message_id for dedup (FR-24)."""
        from app.models.message import Message

        client_id = "offline-msg-12345"
        msg = Message(
            conversation_id=uuid4(),
            sender_id=uuid4(),
            recipient_id=uuid4(),
            content="Syncing from offline",
            client_message_id=client_id,
        )
        assert msg.client_message_id == client_id

    def test_conversation_unique_constraint(self):
        """Conversation should have unique constraint on participants + service_request."""
        from app.models.conversation import Conversation
        import inspect

        source = inspect.getsource(Conversation)
        assert "uq_conversation_participants_context" in source

    def test_message_route_registered(self):
        """Messaging router should be registered in the API."""
        from app.api.v1.router import api_router

        routes = [route.path for route in api_router.routes]
        message_routes = [r for r in routes if "messages" in r.lower() or "conversations" in r.lower()]
        assert len(message_routes) > 0, "Messaging routes not found in API router"


class TestMessagingConsent:
    """Tests for FR-25 consent-gated contact sharing."""

    def test_contact_share_requires_mutual_consent(self):
        """Contact sharing should require mutual consent."""
        from app.middleware.consent_guard import check_contact_sharing_consent

        db = MagicMock()
        sender = uuid4()
        recipient = uuid4()

        # No consent records
        db.query.return_value.filter.return_value.all.return_value = []

        result = check_contact_sharing_consent(sender, recipient, db)
        assert result is False

    def test_contact_share_allowed_with_mutual_consent(self):
        """Contact sharing should succeed with mutual consent."""
        from app.middleware.consent_guard import check_contact_sharing_consent

        db = MagicMock()
        sender = uuid4()
        recipient = uuid4()

        consent_a = MagicMock()
        consent_a.user_id = sender
        consent_b = MagicMock()
        consent_b.user_id = recipient

        db.query.return_value.filter.return_value.all.return_value = [consent_a, consent_b]

        result = check_contact_sharing_consent(sender, recipient, db)
        assert result is True
