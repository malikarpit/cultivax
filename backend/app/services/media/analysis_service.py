"""
Media Analysis Service — Stub CNN Inference

Processes uploaded media files using a placeholder CNN pipeline.
Emits MediaAnalyzed event when analysis completes.

MSDD 4.6 — Media analysis integrated with crop timeline.
"""

import logging
from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session  # type: ignore

from app.models.media_file import MediaFile  # type: ignore

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Structured result from media analysis."""

    def __init__(
        self,
        media_id: str,
        analysis_type: str,
        labels: list,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.media_id = media_id
        self.analysis_type = analysis_type
        self.labels = labels
        self.confidence = confidence
        self.metadata = metadata or {}
        self.analyzed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "media_id": self.media_id,
            "analysis_type": self.analysis_type,
            "labels": self.labels,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "analyzed_at": self.analyzed_at,
        }


# ---------------------------------------------------------------------------
# Stub label mappings (will be replaced by trained CNN model)
# ---------------------------------------------------------------------------

STUB_IMAGE_LABELS = [
    {"label": "healthy_crop", "score": 0.72},
    {"label": "minor_pest_damage", "score": 0.18},
    {"label": "nutrient_deficiency", "score": 0.10},
]

STUB_VIDEO_LABELS = [
    {"label": "field_overview", "score": 0.85},
    {"label": "irrigation_visible", "score": 0.15},
]


class MediaAnalysisService:
    """
    Stub CNN-based media analysis service.

    In production, this would:
    1. Load a pre-trained CNN model (ResNet50 / EfficientNet)
    2. Pre-process the image (resize, normalize)
    3. Run inference and extract top-N labels
    4. Store results and emit MediaAnalyzed event

    Current version returns hardcoded stub results for development.
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_media(self, media_id: UUID) -> AnalysisResult:
        """
        Analyze a media file and update its analysis status.

        Args:
            media_id: UUID of the media file to analyze.

        Returns:
            AnalysisResult with stub labels and confidence.

        Raises:
            ValueError: If media file not found or already analyzed.
        """
        media = self.db.query(MediaFile).filter(
            MediaFile.id == media_id,
            MediaFile.is_deleted == False,
        ).first()

        if not media:
            raise ValueError(f"Media file {media_id} not found")

        if media.analysis_status == "Analyzed":
            raise ValueError(f"Media file {media_id} already analyzed")

        # --- Stub inference ---
        file_type = media.file_type or "image"
        if file_type == "video":
            labels = STUB_VIDEO_LABELS
            analysis_type = "video_classification"
        else:
            labels = STUB_IMAGE_LABELS
            analysis_type = "image_classification"

        # Compute aggregate confidence from top label
        top_confidence = float(labels[0]["score"]) if labels else 0.0

        result = AnalysisResult(
            media_id=str(media_id),
            analysis_type=analysis_type,
            labels=[lbl["label"] for lbl in labels],
            confidence=top_confidence,
            metadata={
                "model_version": "stub-cnn-v0",
                "raw_scores": labels,
                "file_type": file_type,
            },
        )

        # Update DB record
        media.analysis_status = "Analyzed"
        media.analysis_result = result.to_dict()
        self.db.commit()

        logger.info(
            f"Media analyzed: {media_id} — type={analysis_type}, "
            f"top_label={labels[0]['label']}, confidence={top_confidence:.2f}"
        )

        # --- Emit event (MediaAnalyzed) ---
        self._emit_event(media, result)

        return result

    def _emit_event(self, media: MediaFile, result: AnalysisResult):
        """
        Emit a MediaAnalyzed event for downstream consumers.

        In production, this would use the EventDispatcher.
        Currently logs the event for traceability.
        """
        event_payload = {
            "event_type": "MediaAnalyzed",
            "media_id": result.media_id,
            "crop_instance_id": str(media.crop_instance_id),
            "analysis_type": result.analysis_type,
            "top_label": result.labels[0] if result.labels else None,
            "confidence": result.confidence,
            "timestamp": result.analyzed_at,
        }
        logger.info(f"Event emitted: {event_payload}")

    def get_analysis(self, media_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve stored analysis result for a media file."""
        media = self.db.query(MediaFile).filter(
            MediaFile.id == media_id,
            MediaFile.is_deleted == False,
        ).first()

        if not media or not media.analysis_result:
            return None

        return media.analysis_result
