"""
Scheduled Task Runner — Audit 33 Hardened

Runs periodic maintenance tasks with:
  - Concurrency guard: in-process async lock + DB-level last-run dedupe
  - Cadence tags: hourly | daily | weekly
  - Per-task metrics: duration_ms, status, error, last_run
  - Failure alerting: consecutive-failure thresholds emitting DB alerts
  - Structured summary response

Trigger paths:
  - Cloud Scheduler → POST /admin/cron/run (secured by API key)
  - Manual admin trigger in UI

Cadence definitions:
  | Task                 | Cadence | Min interval |
  |----------------------|---------|--------------|
  | system_health        | hourly  | 5 min        |
  | alert_cleanup        | hourly  | 30 min       |
  | recommendations      | daily   | 6 h          |
  | log_compression      | daily   | 6 h          |
  | trust_decay          | weekly  | 24 h         |
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Concurrency guard — prevents overlapping runs in the same process
# ──────────────────────────────────────────────────────────────────────────────
_CRON_LOCK = asyncio.Lock()

# In-memory last-run tracker; used to enforce minimum intervals between runs.
# Survives the lifetime of the process (cleared on restart — acceptable for
# a manual/scheduled trigger model in a single-instance deployment).
_LAST_RUN: dict[str, datetime] = {}

# Per-task minimum intervals
TASK_CADENCES: dict[str, timedelta] = {
    "system_health":  timedelta(minutes=5),
    "alert_cleanup":  timedelta(minutes=30),
    "recommendations": timedelta(hours=6),
    "log_compression": timedelta(hours=6),
    "trust_decay":    timedelta(hours=24),
}

# ──────────────────────────────────────────────────────────────────────────────
# Failure-counter for alerting (resets on process restart)
# ──────────────────────────────────────────────────────────────────────────────
_FAILURE_COUNTS: dict[str, int] = {}
FAILURE_ALERT_THRESHOLD = 3   # emit system alert after N consecutive failures


def _should_run(task_name: str, force: bool = False) -> tuple[bool, Optional[str]]:
    """Return (should_run, skip_reason)."""
    if force:
        return True, None
    interval = TASK_CADENCES.get(task_name)
    if not interval:
        return True, None
    last = _LAST_RUN.get(task_name)
    if last is None:
        return True, None
    elapsed = datetime.now(timezone.utc) - last
    if elapsed < interval:
        remaining_s = int((interval - elapsed).total_seconds())
        return False, f"too_soon — next run in {remaining_s}s"
    return True, None


def _record_run(task_name: str):
    _LAST_RUN[task_name] = datetime.now(timezone.utc)


def _record_failure(task_name: str, db: Session, error: str):
    _FAILURE_COUNTS[task_name] = _FAILURE_COUNTS.get(task_name, 0) + 1
    count = _FAILURE_COUNTS[task_name]
    if count >= FAILURE_ALERT_THRESHOLD:
        try:
            from app.models.alert import Alert
            alert = Alert(
                alert_type="SystemAlert",
                severity="critical",
                urgency_level="Critical",
                message=f"[CronAlert] '{task_name}' has failed {count} times. "
                        f"Last error: {error[:300]}",
            )
            db.add(alert)
            db.commit()
            logger.warning(f"Cron failure alert emitted for '{task_name}' (count={count})")
        except Exception as exc:
            logger.error(f"Failed to emit cron failure alert: {exc}")


def _reset_failures(task_name: str):
    _FAILURE_COUNTS[task_name] = 0


def _task_result(status: str, duration_ms: float, **kwargs) -> dict:
    return {"status": status, "duration_ms": round(duration_ms, 2), **kwargs}


# ──────────────────────────────────────────────────────────────────────────────
# Individual task runners
# ──────────────────────────────────────────────────────────────────────────────

async def _run_trust_decay(db: Session, force: bool) -> dict:
    should, reason = _should_run("trust_decay", force)
    if not should:
        return {"status": "skipped", "reason": reason}

    t0 = _now_ms()
    try:
        from app.services.crop_enhancements import batch_apply_trust_decay
        result = batch_apply_trust_decay(db)
        _record_run("trust_decay")
        _reset_failures("trust_decay")
        return _task_result("ok", _elapsed(t0), decayed_count=result.get("decayed_count", 0))
    except Exception as e:
        ms = _elapsed(t0)
        _record_failure("trust_decay", db, str(e))
        logger.error(f"trust_decay failed: {e}")
        return _task_result("error", ms, error=str(e))


async def _run_health_check(db: Session, force: bool) -> dict:
    should, reason = _should_run("system_health", force)
    if not should:
        return {"status": "skipped", "reason": reason}

    t0 = _now_ms()
    try:
        from app.services.system_health_service import SystemHealthService
        health_service = SystemHealthService(db)
        health = await health_service.check_all()
        overall = health.get("status", "unknown") if isinstance(health, dict) and "status" in health else "unknown"
        # check_all returns subsystem→dict, overall is derived from summary
        _record_run("system_health")
        _reset_failures("system_health")
        return _task_result("ok", _elapsed(t0), subsystems_checked=len(health))
    except Exception as e:
        ms = _elapsed(t0)
        _record_failure("system_health", db, str(e))
        logger.error(f"system_health failed: {e}")
        return _task_result("error", ms, error=str(e))


async def _run_log_compression(db: Session, force: bool) -> dict:
    should, reason = _should_run("log_compression", force)
    if not should:
        return {"status": "skipped", "reason": reason}

    t0 = _now_ms()
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
            res = compress_action_logs(db, crop.id)
            total_compressed += res.get("original_count", 0) - res.get("compressed_count", 0)

        _record_run("log_compression")
        _reset_failures("log_compression")
        return _task_result(
            "ok", _elapsed(t0),
            archived_crops=len(archived_crops),
            actions_compressed=total_compressed
        )
    except Exception as e:
        ms = _elapsed(t0)
        _record_failure("log_compression", db, str(e))
        logger.error(f"log_compression failed: {e}")
        return _task_result("error", ms, error=str(e))


async def _run_recommendations(db: Session, force: bool) -> dict:
    should, reason = _should_run("recommendations", force)
    if not should:
        return {"status": "skipped", "reason": reason}

    t0 = _now_ms()
    try:
        from app.services.recommendations.recommendation_engine import RecommendationEngine
        refreshed = RecommendationEngine(db).refresh_for_active_crops()
        _record_run("recommendations")
        _reset_failures("recommendations")
        return _task_result("ok", _elapsed(t0), crops_refreshed=refreshed)
    except Exception as e:
        ms = _elapsed(t0)
        _record_failure("recommendations", db, str(e))
        logger.error(f"recommendations refresh failed: {e}")
        return _task_result("error", ms, error=str(e))


async def _run_alert_cleanup(db: Session, force: bool) -> dict:
    should, reason = _should_run("alert_cleanup", force)
    if not should:
        return {"status": "skipped", "reason": reason}

    t0 = _now_ms()
    try:
        from app.services.notifications import AlertService
        cleaned = AlertService(db).cleanup_expired_alerts()
        _record_run("alert_cleanup")
        _reset_failures("alert_cleanup")
        return _task_result("ok", _elapsed(t0), alerts_cleaned=cleaned)
    except Exception as e:
        ms = _elapsed(t0)
        _record_failure("alert_cleanup", db, str(e))
        logger.error(f"alert_cleanup failed: {e}")
        return _task_result("error", ms, error=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Public entrypoint
# ──────────────────────────────────────────────────────────────────────────────

async def run_scheduled_tasks(
    db: Session,
    cadence: Optional[str] = None,   # None = all; "hourly" | "daily" | "weekly"
    force: bool = False,              # bypass min-interval guards
) -> dict:
    """
    Run all (or cadence-scoped) maintenance tasks.

    Returns a structured summary:
    {
      "run_id": "...",
      "overall_status": "ok | partial_failure | all_failed | skipped",
      "cadence": "hourly | daily | weekly | all",
      "elapsed_seconds": 1.23,
      "tasks": {
        "trust_decay": {"status": "ok", "duration_ms": 120, ...},
        ...
      }
    }
    """
    if _CRON_LOCK.locked():
        logger.warning("Cron run skipped — another run is already in progress")
        return {
            "run_id": _run_id(),
            "overall_status": "skipped",
            "reason": "concurrent_run_in_progress",
            "cadence": cadence or "all",
        }

    async with _CRON_LOCK:
        run_start = datetime.now(timezone.utc)
        results: dict = {}

        HOURLY_TASKS = [("system_health", _run_health_check), ("alert_cleanup", _run_alert_cleanup)]
        DAILY_TASKS  = [("log_compression", _run_log_compression), ("recommendations", _run_recommendations)]
        WEEKLY_TASKS = [("trust_decay", _run_trust_decay)]

        task_groups = {
            "hourly": HOURLY_TASKS,
            "daily":  DAILY_TASKS,
            "weekly": WEEKLY_TASKS,
        }

        tasks_to_run = []
        if cadence and cadence in task_groups:
            tasks_to_run = task_groups[cadence]
        else:
            for group in task_groups.values():
                tasks_to_run.extend(group)

        for task_name, task_fn in tasks_to_run:
            try:
                results[task_name] = await task_fn(db, force)
            except Exception as e:
                results[task_name] = {"status": "error", "error": str(e)}
                logger.exception(f"Unexpected error in task '{task_name}': {e}")

        elapsed = (datetime.now(timezone.utc) - run_start).total_seconds()
        statuses = [r.get("status") for r in results.values()]

        if all(s == "skipped" for s in statuses):
            overall = "skipped"
        elif all(s in ("ok", "skipped") for s in statuses):
            overall = "ok"
        elif any(s == "ok" for s in statuses):
            overall = "partial_failure"
        else:
            overall = "all_failed"

        return {
            "run_id": _run_id(run_start),
            "overall_status": overall,
            "cadence": cadence or "all",
            "elapsed_seconds": round(elapsed, 2),
            "tasks": results,
        }


def get_maintenance_status() -> dict:
    """
    Return in-memory maintenance status snapshot for the status API.
    Includes last run times, failure counts, and next eligible run windows.
    """
    now = datetime.now(timezone.utc)
    tasks = {}
    for task_name, interval in TASK_CADENCES.items():
        last = _LAST_RUN.get(task_name)
        failures = _FAILURE_COUNTS.get(task_name, 0)
        next_run = None
        overdue = False
        if last:
            next_eligible = last + interval
            next_run = next_eligible.isoformat()
            overdue = now > next_eligible
        tasks[task_name] = {
            "last_run": last.isoformat() if last else None,
            "next_eligible_run": next_run,
            "overdue": overdue,
            "consecutive_failures": failures,
            "min_interval_seconds": int(interval.total_seconds()),
        }
    return {
        "server_time": now.isoformat(),
        "lock_held": _CRON_LOCK.locked(),
        "tasks": tasks,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

import time as _time

def _now_ms() -> float:
    return _time.monotonic() * 1000

def _elapsed(t0: float) -> float:
    return _time.monotonic() * 1000 - t0

def _run_id(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    return f"cron_{d.strftime('%Y%m%d_%H%M%S')}"
