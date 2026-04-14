"""
Test ML Feedback Loop — FR-10

Tests feedback aggregation and confidence adjustment.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4


class TestFeedbackAggregator:
    """Tests for the ML feedback aggregator."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_insufficient_data_returns_no_adjustment(self, mock_db):
        """With fewer than 5 feedbacks, adjustment factor should be 1.0."""
        from app.services.ml.feedback_aggregator import FeedbackAggregator

        # Mock only 3 feedbacks
        feedbacks = [MagicMock(feedback_type="confirmed", is_deleted=False)] * 3
        mock_db.query.return_value.filter.return_value.all.return_value = feedbacks

        aggregator = FeedbackAggregator(mock_db)
        factor = aggregator.compute_adjustment_factor("v1")
        assert factor == 1.0

    def test_all_confirmed_returns_max_factor(self, mock_db):
        """100% confirmed feedback should produce factor = 1.0."""
        from app.services.ml.feedback_aggregator import FeedbackAggregator

        feedbacks = [MagicMock(feedback_type="confirmed", is_deleted=False)] * 10
        mock_db.query.return_value.filter.return_value.all.return_value = feedbacks

        aggregator = FeedbackAggregator(mock_db)
        factor = aggregator.compute_adjustment_factor("v1")
        assert factor == 1.0

    def test_high_rejection_lowers_confidence(self, mock_db):
        """High rejection rate should lower confidence factor."""
        from app.services.ml.feedback_aggregator import FeedbackAggregator

        feedbacks = (
            [MagicMock(feedback_type="rejected", is_deleted=False)] * 8
            + [MagicMock(feedback_type="confirmed", is_deleted=False)] * 2
        )
        mock_db.query.return_value.filter.return_value.all.return_value = feedbacks

        aggregator = FeedbackAggregator(mock_db)
        factor = aggregator.compute_adjustment_factor("v1")
        assert factor < 0.8  # Should be significantly penalized
        assert factor >= 0.5  # Bounded minimum

    def test_factor_bounded_to_half(self, mock_db):
        """Factor should never go below 0.5."""
        from app.services.ml.feedback_aggregator import FeedbackAggregator

        feedbacks = [MagicMock(feedback_type="rejected", is_deleted=False)] * 20
        mock_db.query.return_value.filter.return_value.all.return_value = feedbacks

        aggregator = FeedbackAggregator(mock_db)
        factor = aggregator.compute_adjustment_factor("v1")
        assert factor == 0.5

    def test_feedback_summary_returns_correct_counts(self, mock_db):
        """Summary should return correct counts."""
        from app.services.ml.feedback_aggregator import FeedbackAggregator

        feedbacks = [
            MagicMock(feedback_type="confirmed", model_version="v1", is_deleted=False),
            MagicMock(feedback_type="rejected", model_version="v1", is_deleted=False),
            MagicMock(feedback_type="partially_correct", model_version="v1", is_deleted=False),
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = feedbacks

        aggregator = FeedbackAggregator(mock_db)
        summary = aggregator.get_feedback_summary("v1")
        assert summary["total_feedback"] == 3
        assert summary["confirmed"] == 1
        assert summary["rejected"] == 1
        assert summary["partially_correct"] == 1
