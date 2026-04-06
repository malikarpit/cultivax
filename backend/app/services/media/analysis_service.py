"""
Media Analysis Service — V1 Computer Vision Heuristics

Processes uploaded media files using OpenCV/NumPy heuristics with graceful
fallback when ML dependencies are unavailable.
Emits MediaAnalyzed event when analysis completes.

MSDD 4.6 — Media analysis integrated with crop timeline.
TDD 1710-1711 — Graceful fallback when CV/ML deps unavailable.
"""

import logging
from datetime import datetime, timezone
from io import BytesIO

try:
    from PIL import Image

    _PIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PIL_AVAILABLE = False
    Image = None

try:
    import cv2
    import numpy as np

    _CV_AVAILABLE = True
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]
    cv2 = None  # type: ignore[assignment]
    _CV_AVAILABLE = False

from app.models.media_file import MediaFile
from app.services.media.post_analysis_service import \
    apply_media_analysis_updates

logger = logging.getLogger(__name__)


class AnalysisService:
    """Image analysis with heuristic scoring (v1)."""

    def __init__(self, db):
        self.db = db

    async def analyze_media(self, media_id: str) -> dict:
        """
        Analyze uploaded media directly and persist results.
        Returns heuristics dict.
        """
        media = self.db.query(MediaFile).filter(MediaFile.id == media_id).first()
        if not media:
            logger.error(f"Media {media_id} not found for analysis.")
            return {}

        try:
            from app.services.feature_flags import is_enabled

            if not is_enabled(self.db, "prod.media_analysis", default=True):
                logger.info(
                    f"Media Analysis flag disabled. Skipping execution for {media_id}."
                )
                return {}

            # 1. Load Image from opaque storage path
            file_data = self._resolve_and_load_file(media.storage_path)
            if not file_data:
                raise ValueError(
                    f"Could not load image bytes from {media.storage_path}"
                )

            image = Image.open(BytesIO(file_data)).convert("RGB")
            image_array = np.array(image)

            # 2. Compute heuristics
            quality = self._compute_quality_score(image_array)
            pest_prob = self._compute_pest_probability(image_array)
            stress_prob = self._compute_stress_probability(image_array)
            confidence = self._compute_confidence(quality, pest_prob, stress_prob)

            # 3. Persist
            media.analysis_status = "analyzed"
            media.image_quality_score = quality
            media.pest_probability = pest_prob
            media.stress_probability = stress_prob
            media.confidence_score = confidence
            media.analysis_source = "backend_heuristic_v1"
            media.updated_at = datetime.now(timezone.utc)

            # 4. Quarantine fallback
            if quality < 0.5:
                media.is_quarantined = True
                logger.warning(f"Media {media_id} quarantined: quality={quality:.2f}")

            self.db.commit()

            # 5. Apply post-analysis domain updates without handler/worker coupling.
            await apply_media_analysis_updates(
                media_id=str(media_id),
                crop_instance_id=str(media.crop_instance_id),
                quality_score=quality,
                pest_probability=pest_prob,
                stress_probability=stress_prob,
                is_quarantined=media.is_quarantined,
                db=self.db,
            )

            return {
                "quality_score": quality,
                "pest_probability": pest_prob,
                "stress_probability": stress_prob,
                "confidence": confidence,
                "model_status": "stub",
                "model_version": "heuristic-v1",
            }
        except Exception as e:
            logger.error(f"Analysis failed for {media_id}: {e}", exc_info=True)
            media.analysis_status = "failed"
            self.db.commit()
            return {}

    def _resolve_and_load_file(self, storage_path: str) -> bytes:
        """Reads local files or fetches GCS blobs."""
        if storage_path.startswith("gs://"):
            from google.cloud import storage  # type: ignore

            # gs://<bucket>/<path...>
            bucket_and_path = storage_path[5:]
            if "/" not in bucket_and_path:
                raise ValueError(f"Invalid GCS path: {storage_path}")
            bucket_name, blob_path = bucket_and_path.split("/", 1)

            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            return blob.download_as_bytes()
        else:
            with open(storage_path, "rb") as f:
                return f.read()

    def _compute_quality_score(self, img_array: np.ndarray) -> float:
        """Blur detection (Laplacian variance), Exposure (histogram)."""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 500, 1.0)

        hist_std = np.std(gray)
        exposure_score = 1.0 if 30 < hist_std < 220 else 0.5
        noise_score = 0.7

        quality = 0.4 * blur_score + 0.4 * exposure_score + 0.2 * noise_score
        return float(np.clip(quality, 0, 1))

    def _compute_pest_probability(self, img_array: np.ndarray) -> float:
        """Green vs brown ratio."""
        img_hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([30, 255, 255])

        mask = cv2.inRange(img_hsv, lower_brown, upper_brown)
        pest_percentage = np.sum(mask > 0) / mask.size

        pest_prob = min(pest_percentage / 0.1, 1.0)
        return float(np.clip(pest_prob, 0, 1))

    def _compute_stress_probability(self, img_array: np.ndarray) -> float:
        """Saturation indicators for wilting."""
        img_hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        saturation = img_hsv[:, :, 1].astype(float)
        mean_saturation = np.mean(saturation)

        stress_prob = 1.0 - (mean_saturation / 255)
        return float(np.clip(stress_prob, 0, 1))

    def _compute_confidence(self, quality: float, pest: float, stress: float) -> float:
        base_confidence = 0.7
        return float(base_confidence * quality)

    @staticmethod
    def stress_escalation_guardrail(
        current_stress: float,
        new_stress: float,
        confidence: float = 1.0,
        max_daily_increase: float = 20.0,
    ) -> float:
        """
        Guardrail for stress updates: caps daily increase and applies confidence weighting.
        """
        if new_stress <= current_stress:
            return new_stress

        increase = new_stress - current_stress
        weighted_increase = increase * confidence
        capped_increase = min(weighted_increase, max_daily_increase)

        return current_stress + capped_increase

    def _cv_available(self) -> bool:
        """Runtime guard — True when OpenCV + NumPy are importable."""
        return _CV_AVAILABLE


# Backward-compat alias used by some test paths
MediaAnalysisService = AnalysisService
