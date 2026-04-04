import logging
from sqlalchemy.orm import Session

from app.services.media.post_analysis_service import apply_media_analysis_updates


logger = logging.getLogger(__name__)

async def emit_upload_event(media_id: str):
    """Triggered on media upload. Kicks off background analysis."""
    logger.info(f"MediaUploaded event received for {media_id}. Enqueuing analysis.")
    # Here we are calling the background analysis synchronous or async proxy
    # Since background_tasks run asynchronously within FastAPI, we can await or run directly.
    from app.workers.analysis_worker import process_media_analysis
    await process_media_analysis(media_id)


async def emit_analyzed_event(
    media_id: str,
    crop_instance_id: str,
    quality_score: float,
    pest_probability: float,
    stress_probability: float,
    is_quarantined: bool,
    db: Session,
):
    """
    Handle MediaAnalyzed event.
    Delegates domain updates to post-analysis service.
    """
    logger.info("Handling MediaAnalyzed event for media=%s", media_id)
    await apply_media_analysis_updates(
        media_id=media_id,
        crop_instance_id=crop_instance_id,
        quality_score=quality_score,
        pest_probability=pest_probability,
        stress_probability=stress_probability,
        is_quarantined=is_quarantined,
        db=db,
    )
