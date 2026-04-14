"""
Test Consent Enforcement — NFR-19, FR-25

Tests consent guard middleware behavior.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4


class TestConsentGuard:
    """Tests for the consent enforcement middleware."""

    def test_consent_granted_allows_access(self):
        """Access should be allowed when consent is granted."""
        from app.middleware.consent_guard import check_contact_sharing_consent

        db = MagicMock()
        sender_id = uuid4()
        recipient_id = uuid4()

        # Mock both users having consent
        consent_a = MagicMock()
        consent_a.user_id = sender_id
        consent_b = MagicMock()
        consent_b.user_id = recipient_id

        db.query.return_value.filter.return_value.all.return_value = [
            consent_a, consent_b
        ]

        result = check_contact_sharing_consent(sender_id, recipient_id, db)
        assert result is True

    def test_consent_missing_blocks_access(self):
        """Access should be blocked when consent is not granted."""
        from app.middleware.consent_guard import check_contact_sharing_consent

        db = MagicMock()
        sender_id = uuid4()
        recipient_id = uuid4()

        # Only sender has consent
        consent_a = MagicMock()
        consent_a.user_id = sender_id
        db.query.return_value.filter.return_value.all.return_value = [consent_a]

        result = check_contact_sharing_consent(sender_id, recipient_id, db)
        assert result is False

    def test_no_consent_blocks_both(self):
        """Access should be blocked when neither party has consent."""
        from app.middleware.consent_guard import check_contact_sharing_consent

        db = MagicMock()
        sender_id = uuid4()
        recipient_id = uuid4()

        db.query.return_value.filter.return_value.all.return_value = []

        result = check_contact_sharing_consent(sender_id, recipient_id, db)
        assert result is False
