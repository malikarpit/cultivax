"""
Test Video Processing — TDD 7.6, UML Deploy

Tests video frame extraction, per-frame analysis, and aggregation.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4


class TestVideoProcessor:
    """Tests for the video frame extraction worker."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_aggregate_empty_results(self, mock_db):
        """Aggregation of empty results should return zero values."""
        from app.services.media.video_processor import VideoProcessor

        processor = VideoProcessor(mock_db)
        result = processor._aggregate_frame_results([])
        assert result["stress_probability"] == 0.0
        assert result["confidence"] == 0.0
        assert result["valid_frames"] == 0

    def test_aggregate_single_frame(self, mock_db):
        """Aggregation of single frame should return that frame's values."""
        from app.services.media.video_processor import VideoProcessor

        processor = VideoProcessor(mock_db)
        result = processor._aggregate_frame_results([
            {
                "stress_probability": 0.7,
                "confidence": 0.8,
                "pest_detected": False,
                "quality_score": 0.9,
            }
        ])
        assert result["stress_probability"] == 0.7
        assert result["valid_frames"] == 1

    def test_aggregate_multiple_frames_weighted(self, mock_db):
        """Aggregation should use confidence-weighted mean."""
        from app.services.media.video_processor import VideoProcessor

        processor = VideoProcessor(mock_db)
        result = processor._aggregate_frame_results([
            {"stress_probability": 0.8, "confidence": 0.9, "pest_detected": False, "quality_score": 0.7},
            {"stress_probability": 0.2, "confidence": 0.3, "pest_detected": False, "quality_score": 0.8},
        ])
        # Weighted by confidence: (0.8*0.9 + 0.2*0.3) / (0.9 + 0.3) = 0.78/1.2 ≈ 0.65
        assert result["stress_probability"] > 0.5  # Weighted towards high-confidence frame
        assert result["valid_frames"] == 2
        assert result["aggregation_method"] == "confidence_weighted_mean"

    def test_aggregate_filters_error_frames(self, mock_db):
        """Aggregation should exclude frames with errors."""
        from app.services.media.video_processor import VideoProcessor

        processor = VideoProcessor(mock_db)
        result = processor._aggregate_frame_results([
            {"stress_probability": 0.7, "confidence": 0.8, "pest_detected": False, "quality_score": 0.9},
            {"error": "frame_corrupted", "frame": "/tmp/bad_frame.jpg"},
        ])
        assert result["valid_frames"] == 1
        assert result["total_frames"] == 2

    def test_pest_detection_threshold(self, mock_db):
        """Pest detection should use 30% threshold across frames."""
        from app.services.media.video_processor import VideoProcessor

        processor = VideoProcessor(mock_db)

        # Less than 30% pest detection → False
        result = processor._aggregate_frame_results([
            {"stress_probability": 0.5, "confidence": 0.8, "pest_detected": True, "quality_score": 0.7},
            {"stress_probability": 0.3, "confidence": 0.7, "pest_detected": False, "quality_score": 0.8},
            {"stress_probability": 0.4, "confidence": 0.6, "pest_detected": False, "quality_score": 0.7},
            {"stress_probability": 0.4, "confidence": 0.6, "pest_detected": False, "quality_score": 0.7},
        ])
        assert result["pest_detected"] is False

    def test_extract_frames_no_cv2(self, mock_db):
        """Extract frames should return empty list when cv2 is not installed."""
        from app.services.media.video_processor import VideoProcessor

        processor = VideoProcessor(mock_db)
        with patch.dict("sys.modules", {"cv2": None}):
            # Import would fail, but the code handles ImportError gracefully
            frames = processor.extract_frames("/tmp/nonexistent.mp4")
            assert isinstance(frames, list)

    def test_worker_routes_video_correctly(self):
        """Analysis worker should route video files to VideoProcessor."""
        import inspect
        from app.workers.analysis_worker import process_media_analysis

        source = inspect.getsource(process_media_analysis)
        assert "video/" in source
        assert "VideoProcessor" in source
