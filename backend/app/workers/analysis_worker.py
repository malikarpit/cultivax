import logging

from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def process_media_analysis(media_id: str):
    """Background task to analyze media synchronously using a new DB session."""
    try:
        # Local import prevents eager module loading chains during app startup.
        from app.services.media.analysis_service import AnalysisService

        # Create a new session for the background worker
        db = SessionLocal()
        try:
            analysis_service = AnalysisService(db)
            await analysis_service.analyze_media(media_id)
            logger.info(
                f"Background analysis completed successfully for media {media_id}"
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(
            f"Background analysis failed for media {media_id}: {e}", exc_info=True
        )
