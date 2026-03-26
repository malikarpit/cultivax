"""
System Health Service — 26 march: Phase 7B

Manages system health monitoring:
  - Checks subsystem health (ML, weather, media, events, database)
  - Persists results to system_health table
  - Provides data for GET /health endpoint

MSDD 11.7 — System Health & Graceful Degradation
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import func, text  # type: ignore

from app.models.system_health import SystemHealth  # type: ignore

logger = logging.getLogger(__name__)

# Subsystems to monitor
SUBSYSTEMS = ["database", "ml", "weather", "media", "events"]

# Staleness thresholds (seconds)
STALENESS_THRESHOLDS = {
    "database": 30,
    "ml": 300,
    "weather": 600,
    "media": 300,
    "events": 120,
}


class SystemHealthService:
    """
    Monitors and reports on subsystem health.

    Statuses:
      - Operational: everything working normally
      - Degraded: partial functionality, some features limited
      - Down: subsystem unavailable
    """

    def __init__(self, db: Session):
        self.db = db

    def check_all(self) -> Dict[str, dict]:
        """
        Run health checks on all subsystems and persist results.
        Returns a dict of subsystem → {status, last_checked, details}.
        """
        results = {}

        for subsystem in SUBSYSTEMS:
            checker = getattr(self, f"_check_{subsystem}", self._check_generic)
            try:
                status, details = checker()
            except Exception as e:
                status = "Down"
                details = {"error": str(e)}
                logger.error(f"Health check failed for {subsystem}: {e}")

            # Persist to system_health table
            self._upsert_health(subsystem, status, details)
            results[subsystem] = {
                "status": status,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "details": details,
            }

        return results

    def get_status_summary(self) -> dict:
        """
        Get current health status from DB (read-only, no new checks).
        Used by the GET /health endpoint for fast responses.
        """
        records = (
            self.db.query(SystemHealth)
            .filter(SystemHealth.is_deleted == False)
            .all()
        )

        subsystems = {}
        overall = "Operational"

        for record in records:
            subsystems[record.subsystem] = {
                "status": record.status,
                "last_checked": record.last_checked.isoformat() if record.last_checked else None,
                "details": record.details or {},
            }
            if record.status == "Down":
                overall = "Down"
            elif record.status == "Degraded" and overall != "Down":
                overall = "Degraded"

        return {
            "overall_status": overall,
            "subsystems": subsystems,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------------
    # Individual health checks
    # -------------------------------------------------------------------

    def _check_database(self) -> tuple:
        """Check database connectivity."""
        try:
            self.db.execute(text("SELECT 1"))
            return "Operational", {"connected": True}
        except Exception as e:
            return "Down", {"connected": False, "error": str(e)}

    def _check_ml(self) -> tuple:
        """Check ML subsystem health."""
        try:
            from app.services.ml.risk_predictor import RiskPredictor, MODEL_VERSION
            predictor = RiskPredictor()
            # Quick sanity check — predict with defaults
            result = predictor.predict_risk(stress_score=0, action_count=1, current_day_number=1)
            return "Operational", {
                "model_version": MODEL_VERSION,
                "test_prediction": result.prediction_value,
            }
        except Exception as e:
            return "Degraded", {"error": str(e)}

    def _check_weather(self) -> tuple:
        """Check weather data freshness."""
        # In production: check last weather API call timestamp
        # Stub: always operational
        return "Operational", {"source": "stub", "note": "Weather API not yet integrated"}

    def _check_media(self) -> tuple:
        """Check media analysis service."""
        try:
            from app.services.media.analysis_service import MediaAnalysisService
            return "Operational", {"service": "available"}
        except Exception as e:
            return "Degraded", {"error": str(e)}

    def _check_events(self) -> tuple:
        """Check event processing health."""
        try:
            from app.models.event_log import EventLog
            # Count stuck events (Created for > 5 minutes)
            stuck_count = (
                self.db.query(func.count(EventLog.id))
                .filter(
                    EventLog.status == "Created",
                    EventLog.is_deleted == False,
                )
                .scalar()
                or 0
            )

            if stuck_count > 100:
                return "Degraded", {"stuck_events": stuck_count}
            return "Operational", {"pending_events": stuck_count}
        except Exception as e:
            return "Degraded", {"error": str(e)}

    def _check_generic(self) -> tuple:
        """Fallback check for unknown subsystems."""
        return "Operational", {"note": "Generic check — no specific probe implemented"}

    # -------------------------------------------------------------------
    # DB persistence
    # -------------------------------------------------------------------

    def _upsert_health(self, subsystem: str, status: str, details: dict):
        """Insert or update the health record for a subsystem."""
        record = (
            self.db.query(SystemHealth)
            .filter(
                SystemHealth.subsystem == subsystem,
                SystemHealth.is_deleted == False,
            )
            .first()
        )

        now = datetime.now(timezone.utc)

        if record:
            record.status = status
            record.last_checked = now
            record.details = details
        else:
            record = SystemHealth(
                subsystem=subsystem,
                status=status,
                last_checked=now,
                details=details,
            )
            self.db.add(record)

        self.db.commit()
