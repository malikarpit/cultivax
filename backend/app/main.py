"""
CultivaX — Main Application Entry Point

FastAPI application with CORS, middleware, API router registration,
and background event processing loop.
"""

import asyncio
import logging
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session  # type: ignore

from app.config import settings
from app.database import get_db
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.api.v1.router import api_router
from app.database import SessionLocal
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Crop Lifecycle Management & Service Orchestration Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware (order matters — outermost first)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(api_router)

# --- Background Event Processor ---
_event_processor_task: Optional[asyncio.Task] = None
_shutdown_event = asyncio.Event()


@app.on_event("startup")
async def start_event_processor():
    """
    Launch background event processing on app startup.

    1. Crash recovery: reset any events stuck in 'Processing' from a
       previous crash back to 'Created' so they can be re-processed.
    2. Start the async polling loop as a background task.
    """
    global _event_processor_task

    # Crash recovery
    db = SessionLocal()
    try:
        reset_count = DBEventDispatcher.reset_stale_processing(db)
        if reset_count > 0:
            logger.warning(f"Startup crash recovery: reset {reset_count} stale events")
        else:
            logger.info("Startup crash recovery: no stale events found")
    finally:
        db.close()

    # Launch background processor
    db = SessionLocal()
    dispatcher = DBEventDispatcher(db)
    _shutdown_event.clear()
    _event_processor_task = asyncio.create_task(
        dispatcher.run_processing_loop(
            interval_seconds=5.0,
            shutdown_event=_shutdown_event,
        )
    )
    logger.info("Background event processor task created")


@app.on_event("shutdown")
async def stop_event_processor():
    """Gracefully stop background event processing on shutdown."""
    global _event_processor_task

    if _event_processor_task and not _event_processor_task.done():
        logger.info("Signaling event processor to stop...")
        _shutdown_event.set()
        try:
            await asyncio.wait_for(_event_processor_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Event processor did not stop in time, cancelling")
            _event_processor_task.cancel()
        _event_processor_task = None
        logger.info("Background event processor stopped")


@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Enhanced health check endpoint (26 march: Phase 7B).
    Returns subsystem-level health statuses for monitoring and Cloud Run.
    """
    try:
        from app.services.system_health_service import SystemHealthService

        service = SystemHealthService(db)
        summary = service.get_status_summary()
        return {
            "status": summary["overall_status"].lower(),
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "1.0.0",
            "subsystems": summary["subsystems"],
            "checked_at": summary["checked_at"],
        }
    except Exception:
        # Fallback if health service itself fails
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "1.0.0",
        }


@app.post("/admin/cron/run", tags=["Admin"])
async def run_cron_tasks(db: Session = Depends(get_db)):
    """
    Manually trigger scheduled maintenance tasks (admin-only).
    Runs trust decay, health checks, and log compression.
    """
    from app.services.cron import run_scheduled_tasks
    result = await run_scheduled_tasks(db)
    return {"status": "completed", "tasks": result}


@app.post("/admin/health-check", tags=["Admin"])
async def trigger_health_check(db: Session = Depends(get_db)):
    """Manually trigger a full system health check and persist results."""
    from app.services.system_health_service import SystemHealthService
    service = SystemHealthService(db)
    result = await service.check_all()
    return result


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }
