"""
API v1 Health Endpoint

Compatibility endpoint for docs/contracts that reference:
GET /api/v1/health
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/health", tags=["System"])


@router.get("/")
async def api_v1_health(db: Session = Depends(get_db)):
    """
    Return subsystem-aware health summary under /api/v1/health.
    """
    try:
        from app.services.system_health_service import SystemHealthService

        service = SystemHealthService(db)
        summary = service.get_status_summary(admin_detail=False)
        return {
            "status": summary["overall_status"].lower(),
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "2.0.0",
            "subsystems": [
                {"name": k, "status": v["status"]}
                for k, v in summary["subsystems"].items()
            ],
            "checked_at": summary["checked_at"],
        }
    except Exception:
        # Fail-open summary for health probes if internals are unavailable.
        return {
            "status": "operational",
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "2.0.0",
        }
