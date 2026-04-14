"""
Video Frame Extraction Worker — TDD 7.6, UML Deploy Diagram

Processes video media files by extracting frames at regular intervals,
running per-frame analysis, and aggregating results.

Separated from the image analysis worker to support independent scaling
(UML deployment constraint: dedicated media worker container).
"""

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

# Frame extraction defaults
DEFAULT_FRAME_INTERVAL_SECONDS = 5
MAX_FRAMES_PER_VIDEO = 30  # Safety cap to limit processing


class VideoProcessor:
    """
    Video processing pipeline:
    1. Extract frames from video at regular intervals
    2. Analyze each frame through the image analysis heuristic/CNN pipeline
    3. Aggregate per-frame results into a single analysis output
    """

    def __init__(self, db):
        self.db = db

    def extract_frames(
        self,
        video_path: str,
        interval_seconds: int = DEFAULT_FRAME_INTERVAL_SECONDS,
    ) -> List[str]:
        """
        Extract frames from a video file at regular intervals.

        Uses OpenCV (cv2) for frame extraction. Falls back gracefully
        if cv2 is not available.

        Args:
            video_path: Path to the video file.
            interval_seconds: Seconds between extracted frames.

        Returns:
            List of paths to extracted frame images.
        """
        try:
            import cv2
        except ImportError:
            logger.warning(
                "OpenCV (cv2) not installed — video frame extraction unavailable. "
                "Install with: pip install opencv-python-headless"
            )
            return []

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_interval = max(1, int(fps * interval_seconds))

        frames_dir = f"{video_path}_frames"
        os.makedirs(frames_dir, exist_ok=True)

        extracted = []
        frame_count = 0

        while cap.isOpened() and len(extracted) < MAX_FRAMES_PER_VIDEO:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                frame_path = os.path.join(
                    frames_dir, f"frame_{frame_count:06d}.jpg"
                )
                cv2.imwrite(frame_path, frame)
                extracted.append(frame_path)

            frame_count += 1

        cap.release()

        logger.info(
            f"Extracted {len(extracted)} frames from {video_path} "
            f"(total_frames={total_frames}, fps={fps:.1f}, interval={interval_seconds}s)"
        )
        return extracted

    async def process_video(self, media_id: str) -> dict:
        """
        Full video processing pipeline:
        1. Load media record from DB
        2. Extract frames
        3. Analyze each frame
        4. Aggregate results

        Returns aggregated analysis result.
        """
        from app.models.media_file import MediaFile
        from app.services.media.analysis_service import AnalysisService

        media = (
            self.db.query(MediaFile)
            .filter(MediaFile.id == media_id)
            .first()
        )
        if not media:
            logger.error(f"Media file {media_id} not found")
            return {"error": "Media not found"}

        storage_path = getattr(media, "storage_path", None) or getattr(
            media, "file_path", None
        )
        if not storage_path or not os.path.exists(storage_path):
            logger.warning(f"Video file path invalid for media {media_id}")
            return {"error": "Video file not accessible", "media_id": media_id}

        # Step 1: Extract frames
        frames = self.extract_frames(storage_path)
        if not frames:
            return {
                "media_id": media_id,
                "status": "no_frames_extracted",
                "frame_count": 0,
            }

        # Step 2: Analyze each frame
        frame_results = []
        analysis_service = AnalysisService(self.db)
        for frame_path in frames:
            try:
                result = analysis_service._analyze_single_image(frame_path)
                frame_results.append(result)
            except Exception as e:
                logger.warning(f"Frame analysis failed for {frame_path}: {e}")
                frame_results.append({"error": str(e), "frame": frame_path})

        # Step 3: Aggregate
        aggregated = self._aggregate_frame_results(frame_results)
        aggregated["media_id"] = media_id
        aggregated["frame_count"] = len(frames)
        aggregated["analysis_source"] = "video_frame_extraction"

        # Update media record with aggregated results
        if hasattr(media, "analysis_result"):
            media.analysis_result = aggregated
        if hasattr(media, "analysis_status"):
            media.analysis_status = "completed"

        self.db.commit()

        logger.info(
            f"Video analysis completed for media {media_id}: "
            f"{len(frames)} frames, aggregated stress={aggregated.get('stress_probability', 'N/A')}"
        )
        return aggregated

    def _aggregate_frame_results(self, results: List[dict]) -> dict:
        """
        Aggregate per-frame analysis results using confidence-weighted mean.

        Frames with higher confidence contribute more to the final score.
        """
        valid_results = [r for r in results if "error" not in r]

        if not valid_results:
            return {
                "stress_probability": 0.0,
                "confidence": 0.0,
                "pest_detected": False,
                "quality_score": 0.0,
                "aggregation_method": "none",
                "valid_frames": 0,
            }

        # Confidence-weighted aggregation
        total_weight = 0.0
        weighted_stress = 0.0
        weighted_quality = 0.0
        pest_detections = 0

        for r in valid_results:
            confidence = r.get("confidence", 0.5)
            stress = r.get("stress_probability", 0.0)
            quality = r.get("quality_score", 0.5)

            weighted_stress += stress * confidence
            weighted_quality += quality * confidence
            total_weight += confidence

            if r.get("pest_detected", False):
                pest_detections += 1

        if total_weight == 0:
            total_weight = 1.0

        return {
            "stress_probability": round(weighted_stress / total_weight, 4),
            "confidence": round(total_weight / len(valid_results), 4),
            "pest_detected": pest_detections > len(valid_results) * 0.3,
            "quality_score": round(weighted_quality / total_weight, 4),
            "aggregation_method": "confidence_weighted_mean",
            "valid_frames": len(valid_results),
            "total_frames": len(results),
            "pest_detection_ratio": (
                round(pest_detections / len(valid_results), 4)
                if valid_results
                else 0.0
            ),
        }
