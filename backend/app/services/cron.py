"""
Scheduled Task Runner — 26 March: Phase 7 Cron Jobs

Runs periodic maintenance tasks:
  1. Trust decay for inactive providers (weekly)
  2. System health check (every 5 minutes)
  3. Action log compression for archived crops (daily)

Can be triggered by:
  - Cloud Scheduler hitting POST /admin/cron/run
  - A background loop in main.py
  - Manual admin trigger
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session  # type: ignore

logger = logging.getLogger(__name__)


async def run_scheduled_tasks(db: Session) -> dict:
    """
    Runs all periodic maintenance tasks.
    Returns a summary of what was executed.
    """
    results = {}
    start = datetime.now(timezone.utc)

    # 1. Trust Decay (weekly cadence — safe to run more frequently)
    try:
        from app.services.crop_enhancements import batch_apply_trust_decay
        decay_result = batch_apply_trust_decay(db)
        results["trust_decay"] = {
            "status": "ok",
            "decayed_count": decay_result["decayed_count"],
        }
        logger.info(f"Trust decay: {decay_result['decayed_count']} providers updated")
    except Exception as e:
        results["trust_decay"] = {"status": "error", "detail": str(e)}
        logger.error(f"Trust decay failed: {e}")

    # 2. System Health Check
    try:
        from app.services.system_health_service import SystemHealthService
        health_service = SystemHealthService(db)
        health = await health_service.check_all()
        results["health_check"] = {
            "status": "ok",
            "overall": health.get("status", "unknown"),
            "subsystems_checked": len(health.get("subsystems", [])),
        }
        logger.info(f"Health check: {health.get('status', 'unknown')}")
    except Exception as e:
        results["health_check"] = {"status": "error", "detail": str(e)}
        logger.error(f"Health check failed: {e}")

    # 3. Action Log Compression (for archived crops)
    try:
        from app.models.crop_instance import CropInstance
        from app.services.crop_enhancements import compress_action_logs

        archived_crops = (
            db.query(CropInstance)
            .filter(CropInstance.is_archived == True)
            .all()
        )

        total_compressed = 0
        for crop in archived_crops:
            comp_result = compress_action_logs(db, crop.id)
            total_compressed += comp_result.get("original_count", 0) - comp_result.get("compressed_count", 0)

        results["log_compression"] = {
            "status": "ok",
            "archived_crops": len(archived_crops),
            "actions_compressed": total_compressed,
        }
        logger.info(f"Log compression: {total_compressed} actions compressed across {len(archived_crops)} crops")
    except Exception as e:
        results["log_compression"] = {"status": "error", "detail": str(e)}
        logger.error(f"Log compression failed: {e}")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    results["elapsed_seconds"] = round(elapsed, 2)

    return results
