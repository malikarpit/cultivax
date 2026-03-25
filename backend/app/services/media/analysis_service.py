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
        media.extracted_features = result.to_dict()

        # 26 march: Phase 4E: Image quality validation (Media Enh 2)
        quality_score = self._compute_image_quality(media)
        media.image_quality_score = quality_score

        # 26 march: Phase 4E: Pest probability extraction
        pest_labels = [lbl for lbl in labels if "pest" in lbl.get("label", "")]
        if pest_labels:
            media.pest_probability = float(pest_labels[0]["score"])

        # Phase 4E: Analysis source tracking
        media.analysis_source = "backend"

        self.db.commit()

        logger.info(
            f"Media analyzed: {media_id} — type={analysis_type}, "
            f"top_label={labels[0]['label']}, confidence={top_confidence:.2f}, "
            f"quality={quality_score:.2f}"
        )

        # --- Emit event (MediaAnalyzed) ---
        self._emit_event(media, result)

        return result

    def _compute_image_quality(self, media: MediaFile) -> float:
        """
        Image quality validation (Media Enh 2).
        Computes a quality score based on blur and brightness estimation.
        In production: Laplacian variance for blur, histogram analysis for brightness.
        Current: stub returning estimated quality based on file metadata.
        """
        quality = 0.85  # Default good quality

        # File size heuristic: very small images likely low quality
        if media.file_size_bytes and media.file_size_bytes < 50000:  # < 50KB
            quality -= 0.3

        # Video files get slightly lower quality score (frame extraction needed)
        if media.file_type == "video":
            quality -= 0.1

        return max(0.0, min(1.0, quality))

    @staticmethod
    def stress_escalation_guardrail(
        current_stress: float,
        new_stress: float,
        confidence: float = 1.0,
        max_daily_increase: float = 15.0,
    ) -> float:
        """
        Stress escalation guardrail (Media Enh 5).
        Caps maximum daily stress increase and applies confidence-weighted smoothing.

        Formula: smoothed = current + min(delta, max_daily_increase) × confidence

        Args:
            current_stress: Current stress score
            new_stress: Proposed new stress score
            confidence: Confidence in the analysis (0-1)
            max_daily_increase: Maximum allowed daily stress increase

        Returns:
            Guardrail-applied stress score
        """
        delta = new_stress - current_stress

        if delta > 0:
            # Cap the increase
            capped_delta = min(delta, max_daily_increase)
            # Apply confidence weighting
            smoothed_delta = capped_delta * confidence
            return round(current_stress + smoothed_delta, 4)

        # Stress decreases are allowed without guardrail
        return round(new_stress, 4)

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
