"""
Test Recommendation Overrides — FR-7, FR-8, FR-9

Tests recommendation override tracking and adaptive guidance.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import datetime, timezone


class TestRecommendationOverrides:
    """Tests for the recommendation override system."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_crop(self):
        crop = MagicMock()
        crop.id = uuid4()
        crop.farmer_id = uuid4()
        crop.state = "Active"
        crop.stage = "vegetative"
        crop.is_deleted = False
        crop.is_archived = False
        crop.stress_score = 0.65
        crop.risk_index = 0.3
        crop.current_day_number = 30
        crop.stage_offset_days = 5
        return crop

    def test_override_creates_tracking_record(self, mock_db, mock_crop):
        """Override should create a RecommendationOverride record."""
        from app.services.recommendations.recommendation_engine import RecommendationEngine
        from app.models.recommendation import Recommendation

        rec = MagicMock(spec=Recommendation)
        rec.id = uuid4()
        rec.crop_instance_id = mock_crop.id
        rec.recommendation_type = "irrigation"
        rec.priority_rank = 50
        rec.rationale = {"trigger": "stress_score > 50%"}
        rec.is_deleted = False

        mock_db.query.return_value.filter.return_value.first.return_value = rec

        engine = RecommendationEngine(mock_db)
        override = engine.override_recommendation(
            crop_instance_id=mock_crop.id,
            recommendation_id=rec.id,
            farmer_id=mock_crop.farmer_id,
            override_action="dismissed",
            farmer_reason="Not applicable to my conditions",
        )

        assert mock_db.add.called
        assert rec.status == "overridden"

    def test_invalid_override_action_raises(self, mock_db, mock_crop):
        """Invalid override action should raise ValueError."""
        from app.services.recommendations.recommendation_engine import RecommendationEngine

        rec = MagicMock()
        rec.id = uuid4()
        rec.is_deleted = False
        mock_db.query.return_value.filter.return_value.first.return_value = rec

        engine = RecommendationEngine(mock_db)
        with pytest.raises(ValueError, match="Invalid override action"):
            engine.override_recommendation(
                crop_instance_id=mock_crop.id,
                recommendation_id=rec.id,
                farmer_id=mock_crop.farmer_id,
                override_action="invalid_action",
            )

    def test_rationale_populated_on_active_recommendations(self, mock_db, mock_crop):
        """Generated recommendations should include structured rationale (FR-9)."""
        from app.services.recommendations.recommendation_engine import RecommendationEngine

        mock_db.query.return_value.filter.return_value.first.return_value = mock_crop
        mock_db.query.return_value.filter.return_value.all.return_value = []

        engine = RecommendationEngine(mock_db)

        # Patch _load_deviation_profile to return None
        with patch.object(engine, '_load_deviation_profile', return_value=None):
            recs = engine.compute_recommendations(mock_crop.id)

        for rec in recs:
            assert rec.rationale is not None, f"Recommendation {rec.message_key} missing rationale"
            assert "trigger" in rec.rationale
            assert "evidence" in rec.rationale
            assert "confidence" in rec.rationale

    def test_deviation_triggers_corrective_recommendation(self, mock_db, mock_crop):
        """High consecutive deviations should inject corrective recommendations (FR-6)."""
        from app.services.recommendations.recommendation_engine import RecommendationEngine

        mock_db.query.return_value.filter.return_value.first.return_value = mock_crop

        deviation = MagicMock()
        deviation.consecutive_count = 5
        deviation.trend_slope = 0.15
        deviation.cumulative_days = 12

        engine = RecommendationEngine(mock_db)

        with patch.object(engine, '_load_deviation_profile', return_value=deviation):
            recs = engine.compute_recommendations(mock_crop.id)

        deviation_recs = [r for r in recs if r.message_key == "deviation_corrective_action"]
        assert len(deviation_recs) > 0, "Missing corrective recommendation for high deviation"

    def test_service_suggestion_created(self, mock_db, mock_crop):
        """MSDD 2.11: create_service_suggestion should create recommendation."""
        from app.services.recommendations.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine(mock_db)
        rec = engine.create_service_suggestion(
            crop_instance_id=mock_crop.id,
            service_type="irrigation_service",
            urgency="high",
        )

        assert mock_db.add.called
        assert mock_db.commit.called
