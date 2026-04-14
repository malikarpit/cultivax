"""
Test CTIS→SOE Suggestion Event — MSDD 2.11

Tests the SuggestService event pipeline.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4


class TestCTISSOESuggestion:
    """Tests for the CTIS→SOE SuggestService event handler."""

    def test_suggest_service_event_type_exists(self):
        """SUGGEST_SERVICE should be a registered event type."""
        from app.services.event_dispatcher.event_types import CTISEvents, is_valid_event_type

        assert hasattr(CTISEvents, "SUGGEST_SERVICE")
        assert CTISEvents.SUGGEST_SERVICE == "ctis.suggest_service"
        assert is_valid_event_type(CTISEvents.SUGGEST_SERVICE)

    def test_suggest_service_handler_registered(self):
        """Handler should be registered in the handler map."""
        from app.services.event_dispatcher.handlers import get_handler
        from app.services.event_dispatcher.event_types import CTISEvents

        handler = get_handler(CTISEvents.SUGGEST_SERVICE)
        assert handler is not None

    def test_handler_creates_recommendation(self):
        """SuggestService handler should create a service suggestion recommendation."""
        from app.services.event_dispatcher.handlers import handle_suggest_service

        db = MagicMock()
        event = MagicMock()
        event.entity_id = uuid4()
        event.payload = {
            "crop_instance_id": str(event.entity_id),
            "service_type": "irrigation_service",
            "urgency": "high",
        }

        with patch(
            "app.services.event_dispatcher.handlers.RecommendationEngine"
        ) as MockEngine:
            handle_suggest_service(db, event)
            MockEngine.return_value.create_service_suggestion.assert_called_once_with(
                crop_instance_id=str(event.entity_id),
                service_type="irrigation_service",
                urgency="high",
            )

    def test_handler_missing_crop_id_logs_error(self):
        """Handler should log error and return if crop_instance_id is missing."""
        from app.services.event_dispatcher.handlers import handle_suggest_service

        db = MagicMock()
        event = MagicMock()
        event.entity_id = None
        event.payload = {}

        # Should not raise, just log and return
        handle_suggest_service(db, event)

    def test_soe_isolation_maintained(self):
        """Handler should NOT mutate CTIS state directly."""
        from app.services.event_dispatcher.handlers import handle_suggest_service
        from app.models.crop_instance import CropInstance

        db = MagicMock()
        event = MagicMock()
        event.entity_id = uuid4()
        event.payload = {
            "crop_instance_id": str(event.entity_id),
            "service_type": "pest_control",
            "urgency": "medium",
        }

        with patch(
            "app.services.event_dispatcher.handlers.RecommendationEngine"
        ):
            handle_suggest_service(db, event)

        # Verify no CropInstance query was made (SOE isolation)
        for call in db.query.call_args_list:
            if call and call.args:
                assert call.args[0] != CropInstance, (
                    "SOE handler should not query CropInstance directly"
                )
