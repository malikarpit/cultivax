import logging

from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def process_media_analysis(media_id: str):
    """
    Background task to analyze media synchronously using a new DB session.

    Routes to the appropriate processor based on media type:
    - Video files → VideoProcessor (frame extraction + aggregated analysis)
    - Image files → AnalysisService (direct pixel analysis)

    TDD 7.4, 7.6: Separated video/image processing paths.
    """
    try:
        from app.models.media_file import MediaFile

        db = SessionLocal()
        try:
            media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
            if not media:
                logger.error(f"Media {media_id} not found for analysis")
                return

            mime_type = getattr(media, "mime_type", "") or ""

            if mime_type.startswith("video/"):
                # Route to video processor (TDD 7.6)
                from app.services.media.video_processor import VideoProcessor

                result = await VideoProcessor(db).process_video(media_id)
                logger.info(
                    f"Video analysis completed for media {media_id}: "
                    f"{result.get('frame_count', 0)} frames processed"
                )
            else:
                # Route to image analysis (default path)
                from app.services.media.analysis_service import AnalysisService

                await AnalysisService(db).analyze_media(media_id)
                logger.info(
                    f"Image analysis completed for media {media_id}"
                )
        finally:
            db.close()
    except Exception as e:
        logger.error(
            f"Background analysis failed for media {media_id}: {e}", exc_info=True
        )

