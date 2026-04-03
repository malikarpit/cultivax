"""
Post-analysis domain updates for media processing.

This module intentionally has no dependency on `app.events.handlers` or
`app.workers.analysis_worker` so media analysis can update domain state
without creating import cycles.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.crop_instance import CropInstance
from app.models.media_file import MediaFile
from app.models.stress_history import StressHistory
from app.services.notifications import AlertService

logger = logging.getLogger(__name__)


async def apply_media_analysis_updates(
    *,
    media_id: str,
    crop_instance_id: str,
    quality_score: float,
    pest_probability: float,
    stress_probability: float,
    is_quarantined: bool,
    db: Session,
) -> None:
    """
    Apply domain-side effects after media analysis completes.
    """
    logger.info("Applying media analysis updates for media=%s", media_id)

    if is_quarantined:
        logger.info("Media %s is quarantined; skipping domain updates.", media_id)
        return

    crop = db.query(CropInstance).filter(CropInstance.id == crop_instance_id).first()
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not crop or not media:
        logger.error("Crop or media not found for analysis update media=%s", media_id)
        return

    stress_from_pest = pest_probability * 20
    stress_from_plant = stress_probability * 30
    stress_delta = (stress_from_pest + stress_from_plant) / 2

    current_stress = crop.stress_score or 0.0
    crop.stress_score = min(current_stress + stress_delta, 100.0)
    crop.updated_at = datetime.utcnow()

    stress_history = StressHistory(
        crop_instance_id=UUID(crop_instance_id),
        stress_score=crop.stress_score,
        cause="media_analysis",
        action_taken=f"Analyzed {media_id}",
    )
    db.add(stress_history)
    db.flush()

    alert_service = AlertService(db)
    user_id = crop.farmer_id
    source_event_id = UUID(media_id)

    if pest_probability > 0.6:
        alert_service.generate_alert(
            crop_instance_id=UUID(crop_instance_id),
            user_id=user_id,
            alert_type="pest_alert",
            severity="HIGH" if pest_probability > 0.8 else "MEDIUM",
            message=(
                f"High pest probability ({pest_probability:.0%}) detected in analyzed media. "
                "Consider preventive action."
            ),
            source_event_id=source_event_id,
        )

    if stress_probability > 0.6:
        alert_service.generate_alert(
            crop_instance_id=UUID(crop_instance_id),
            user_id=user_id,
            alert_type="stress_alert",
            severity="HIGH" if stress_probability > 0.8 else "MEDIUM",
            message=f"Plant stress detected ({stress_probability:.0%}) in media analysis.",
            source_event_id=source_event_id,
        )

    db.commit()
    logger.info(
        "Media analysis updates complete for crop=%s quality=%.3f stress_delta=%.1f",
        crop_instance_id,
        quality_score,
        stress_delta,
    )
