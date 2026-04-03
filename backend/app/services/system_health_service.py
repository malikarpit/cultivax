"""
System Health Service — Audit 29 Hardened

Manages system health monitoring:
  - Checks subsystem health (ML, weather, media, events, database)
  - Persists results to system_health table (corrected: last_checked_at)
  - Auto-freshness decay: marks stale subsystems Unknown
  - Deterministic status aggregation: Down > Degraded > Operational > Unknown
  - Provides data for GET /health and GET /api/v1/admin/health endpoints
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.system_health import SystemHealth

logger = logging.getLogger(__name__)

# Subsystems to monitor
SUBSYSTEMS = ["database", "ml", "weather", "media", "events"]

# Staleness max-age thresholds in seconds
FRESHNESS_THRESHOLDS = {
    "database": 60,
    "ml": 300,
    "weather": 600,
    "media": 300,
    "events": 120,
}

# Latency degradation thresholds (ms)
LATENCY_THRESHOLDS = {
    "database": {"degraded": 200, "down": 1000},
    "ml": {"degraded": 500, "down": 2000},
}


class SystemHealthService:
    """
    Monitors and reports on subsystem health.

    Canonical statuses:
      - Operational: everything working normally
      - Degraded: partial functionality, some features limited
      - Down: subsystem unavailable
      - Unknown: stale/no data available

    Aggregation rule (deterministic):
      1. Any Down      → overall Down
      2. Any Degraded  → overall Degraded
      3. All fresh + Operational → overall Operational
      4. Stale/missing → overall Unknown
    """

    def __init__(self, db: Session):
        self.db = db

    async def check_all(self) -> Dict[str, dict]:
        """
        Run health checks on all subsystems and persist results.
        Returns a dict of subsystem → {status, last_checked_at, details}.
        """
        results = {}

        for subsystem in SUBSYSTEMS:
            checker = getattr(self, f"_check_{subsystem}", self._check_generic)
            probe_start = time.monotonic()
            try:
                status, details = checker()
            except Exception as e:
                status = "Down"
                details = {"error": str(e)}
                logger.error(f"Health check failed for {subsystem}: {e}")

            probe_ms = round((time.monotonic() - probe_start) * 1000, 2)
            details["probe_latency_ms"] = probe_ms

            self._upsert_health(subsystem, status, details)
            results[subsystem] = {
                "status": status,
                "last_checked_at": datetime.now(timezone.utc).isoformat(),
                "details": details,
            }

        return results

    def get_status_summary(self, admin_detail: bool = False) -> dict:
        """
        Get current health status from DB (read-only, no new checks).
        Applies freshness decay: stale records are reported as Unknown.
        """
        records = (
            self.db.query(SystemHealth)
            .filter(SystemHealth.is_deleted == False)
            .all()
        )

        now = datetime.now(timezone.utc)
        subsystems = {}
        overall = "Operational"
        has_data = False

        for record in records:
            has_data = True
            max_age = FRESHNESS_THRESHOLDS.get(record.subsystem, 300)

            # Freshness check
            if record.last_checked_at:
                checked = record.last_checked_at
                if checked.tzinfo is None:
                    checked = checked.replace(tzinfo=timezone.utc)
                age_seconds = (now - checked).total_seconds()
                is_stale = age_seconds > max_age
            else:
                is_stale = True

            effective_status = "Unknown" if is_stale else record.status

            entry = {
                "status": effective_status,
                "last_checked_at": record.last_checked_at.isoformat() if record.last_checked_at else None,
                "is_stale": is_stale,
            }
            if admin_detail:
                entry["details"] = record.details or {}
                entry["error_message"] = record.error_message

            subsystems[record.subsystem] = entry

            # Aggregate
            if effective_status == "Down":
                overall = "Down"
            elif effective_status in ("Degraded", "Unknown") and overall != "Down":
                overall = "Degraded"

        if not has_data:
            overall = "Unknown"

        return {
            "overall_status": overall,
            "subsystems": subsystems,
            "checked_at": now.isoformat(),
        }

    # -------------------------------------------------------------------
    # Individual health probes
    # -------------------------------------------------------------------

    def _check_database(self) -> tuple:
        """Lightweight DB connectivity + latency probe."""
        try:
            start = time.monotonic()
            self.db.execute(text("SELECT 1"))
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            thresholds = LATENCY_THRESHOLDS["database"]
            if latency_ms >= thresholds["down"]:
                return "Down", {"connected": True, "latency_ms": latency_ms, "verdict": "latency_critical"}
            elif latency_ms >= thresholds["degraded"]:
                return "Degraded", {"connected": True, "latency_ms": latency_ms, "verdict": "latency_high"}

            return "Operational", {"connected": True, "latency_ms": latency_ms, "verdict": "ok"}
        except Exception as e:
            return "Down", {"connected": False, "error": str(e)}

    def _check_ml(self) -> tuple:
        """ML subsystem readiness + bounded smoke test."""
        try:
            from app.services.ml.risk_predictor import RiskPredictor, MODEL_VERSION
            predictor = RiskPredictor()

            start = time.monotonic()
            result = predictor.predict_risk(stress_score=0, action_count=1, current_day_number=1)
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            thresholds = LATENCY_THRESHOLDS["ml"]
            if latency_ms >= thresholds["down"]:
                return "Down", {"model_version": MODEL_VERSION, "latency_ms": latency_ms, "verdict": "latency_critical"}
            elif latency_ms >= thresholds["degraded"]:
                return "Degraded", {
                    "model_version": MODEL_VERSION,
                    "latency_ms": latency_ms,
                    "verdict": "latency_high",
                    "test_prediction": result.prediction_value,
                }

            return "Operational", {
                "model_version": MODEL_VERSION,
                "latency_ms": latency_ms,
                "test_prediction": result.prediction_value,
                "risk_label": result.risk_label,
                "verdict": "ok",
            }
        except Exception as e:
            return "Down", {"error": str(e)}

    def _check_weather(self) -> tuple:
        """Weather subsystem: check freshness of last successful snapshot."""
        try:
            from app.repositories.weather_repository import WeatherRepository
            repo = WeatherRepository(self.db)

            # Find the most recent snapshot across all locations
            from app.models.weather_snapshot import WeatherSnapshot
            latest = (
                self.db.query(WeatherSnapshot)
                .filter(WeatherSnapshot.is_deleted == False)
                .order_by(WeatherSnapshot.captured_at.desc())
                .first()
            )

            if not latest:
                return "Degraded", {"source": "no_data", "note": "No weather snapshots found"}

            now = datetime.now(timezone.utc)
            captured = latest.captured_at
            if captured.tzinfo is None:
                captured = captured.replace(tzinfo=timezone.utc)
            age_minutes = round((now - captured).total_seconds() / 60, 1)

            if age_minutes > 60:
                return "Degraded", {
                    "source": latest.provider_source,
                    "last_snapshot_age_minutes": age_minutes,
                    "verdict": "stale_data",
                }

            return "Operational", {
                "source": latest.provider_source,
                "last_snapshot_age_minutes": age_minutes,
                "verdict": "ok",
            }
        except Exception as e:
            return "Degraded", {"error": str(e)}

    def _check_media(self) -> tuple:
        """Media analysis: check queue depth and failed analysis items."""
        try:
            from app.models.media_file import MediaFile

            pending = (
                self.db.query(func.count(MediaFile.id))
                .filter(
                    MediaFile.analysis_status == "pending",
                    MediaFile.is_deleted == False,
                )
                .scalar() or 0
            )
            failed = (
                self.db.query(func.count(MediaFile.id))
                .filter(
                    MediaFile.analysis_status == "failed",
                    MediaFile.is_deleted == False,
                )
                .scalar() or 0
            )

            if failed > 50:
                return "Degraded", {"pending": pending, "failed": failed, "verdict": "high_failure_rate"}
            if pending > 200:
                return "Degraded", {"pending": pending, "failed": failed, "verdict": "queue_backlog"}

            return "Operational", {"pending": pending, "failed": failed, "verdict": "ok"}
        except Exception as e:
            return "Degraded", {"error": str(e)}

    def _check_events(self) -> tuple:
        """Event processor: pending count, oldest age, DLQ size."""
        try:
            from app.models.event_log import EventLog

            pending = (
                self.db.query(func.count(EventLog.id))
                .filter(
                    EventLog.status == "Created",
                    EventLog.is_deleted == False,
                )
                .scalar() or 0
            )

            failed = (
                self.db.query(func.count(EventLog.id))
                .filter(
                    EventLog.status == "Failed",
                    EventLog.is_deleted == False,
                )
                .scalar() or 0
            )

            # Oldest pending event age
            oldest = (
                self.db.query(func.min(EventLog.created_at))
                .filter(
                    EventLog.status == "Created",
                    EventLog.is_deleted == False,
                )
                .scalar()
            )
            oldest_age_minutes = 0.0
            if oldest:
                if oldest.tzinfo is None:
                    oldest = oldest.replace(tzinfo=timezone.utc)
                oldest_age_minutes = round((datetime.now(timezone.utc) - oldest).total_seconds() / 60, 1)

            if pending > 100 or oldest_age_minutes > 30:
                return "Degraded", {
                    "pending": pending,
                    "failed_dlq": failed,
                    "oldest_pending_age_minutes": oldest_age_minutes,
                    "verdict": "backlog_detected",
                }

            return "Operational", {
                "pending": pending,
                "failed_dlq": failed,
                "oldest_pending_age_minutes": oldest_age_minutes,
                "verdict": "ok",
            }
        except Exception as e:
            return "Degraded", {"error": str(e)}

    def _check_generic(self) -> tuple:
        """Fallback check for unknown subsystems."""
        return "Operational", {"note": "No specific probe — generic pass"}

    # -------------------------------------------------------------------
    # DB persistence
    # -------------------------------------------------------------------

    def _upsert_health(self, subsystem: str, status: str, details: dict, error_message: str = None):
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
            record.last_checked_at = now
            record.details = details
            record.error_message = error_message or details.get("error")
        else:
            record = SystemHealth(
                subsystem=subsystem,
                status=status,
                last_checked_at=now,
                details=details,
                error_message=error_message or details.get("error"),
            )
            self.db.add(record)

        self.db.commit()
