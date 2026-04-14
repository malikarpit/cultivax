"""
Test Listing Re-confirmation — FR-15, OR-2

Tests stale listing detection and auto-suspension.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


class TestListingReconfirmation:
    """Tests for the listing_reconfirmation cron task."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return MagicMock()

    @patch("app.services.cron._should_run", return_value=(True, None))
    @patch("app.services.cron._record_run")
    @patch("app.services.cron._reset_failures")
    async def test_stale_providers_flagged(
        self, mock_reset, mock_record, mock_should, db_session
    ):
        """Providers not updated in 90+ days should be flagged as stale."""
        from app.services.cron import _run_listing_reconfirmation

        # Mock provider that hasn't been updated in 100 days
        stale_provider = MagicMock()
        stale_provider.listing_status = "active"
        stale_provider.updated_at = datetime.now(timezone.utc) - timedelta(days=100)

        db_session.query.return_value.filter.return_value.all.side_effect = [
            [stale_provider],  # stale providers
            [],                # auto-suspend candidates
            [],                # reconfirmed providers
        ]

        result = await _run_listing_reconfirmation(db_session, force=True)
        assert result["status"] == "ok"
        assert stale_provider.listing_status == "stale"

    @patch("app.services.cron._should_run", return_value=(True, None))
    @patch("app.services.cron._record_run")
    @patch("app.services.cron._reset_failures")
    async def test_auto_suspend_after_grace_period(
        self, mock_reset, mock_record, mock_should, db_session
    ):
        """Stale providers beyond 14-day grace should be auto-suspended."""
        from app.services.cron import _run_listing_reconfirmation

        expired_provider = MagicMock()
        expired_provider.listing_status = "stale"
        expired_provider.is_suspended = False

        db_session.query.return_value.filter.return_value.all.side_effect = [
            [],                    # newly stale
            [expired_provider],    # auto-suspend candidates
            [],                    # reconfirmed
        ]

        result = await _run_listing_reconfirmation(db_session, force=True)
        assert result["status"] == "ok"
        assert expired_provider.is_suspended == True

    @patch("app.services.cron._should_run", return_value=(True, None))
    @patch("app.services.cron._record_run")
    @patch("app.services.cron._reset_failures")
    async def test_recently_updated_providers_reconfirmed(
        self, mock_reset, mock_record, mock_should, db_session
    ):
        """Recently updated stale providers should be reset to active."""
        from app.services.cron import _run_listing_reconfirmation

        reconfirmed_provider = MagicMock()
        reconfirmed_provider.listing_status = "stale"

        db_session.query.return_value.filter.return_value.all.side_effect = [
            [],                        # newly stale
            [],                        # auto-suspend
            [reconfirmed_provider],    # reconfirmed
        ]

        result = await _run_listing_reconfirmation(db_session, force=True)
        assert result["status"] == "ok"
        assert reconfirmed_provider.listing_status == "active"
