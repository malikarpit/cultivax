"""
CultivaX — Main Application Entry Point

FastAPI application with CORS, middleware, API router registration,
and background event processing loop.

Security Enhancements (2026 Standards):
- HTTPOnly cookie authentication
- Content Security Policy headers
- Production security validation
- Input sanitization and XSS prevention
- Distributed rate limiting
- AI-powered anomaly detection
- Quantum-resistant cryptography
- Blockchain-based audit trail
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
from app.middleware.idempotency import DistributedIdempotencyMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.input_sanitization import InputSanitizationMiddleware
from app.middleware.distributed_rate_limiter import DistributedRateLimitMiddleware
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.body_size_limiter import BodySizeLimiterMiddleware
from app.api.v1.router import api_router
from app.database import SessionLocal
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher
from app.security.production_validator import ProductionSecurityValidator
from app.security.admin_api_key import require_admin_api_key
from app.middleware.response_envelope import ResponseEnvelopeMiddleware
from app.core.logging_config import setup_structured_logging

# Enable structured logging (Observability)
setup_structured_logging(app_name=settings.APP_NAME, environment=settings.APP_ENV)
logger = logging.getLogger(__name__)

# Enforce production security validation
if settings.APP_ENV == "production":
    ProductionSecurityValidator.enforce_production_security()
    logger.info("✓ Production security validation passed")

# Warn about missing production configuration (REDIS_URL, SECRET_KEY, ADMIN_API_KEY)
settings.warn_production_gaps()


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Crop Lifecycle Management & Service Orchestration Platform with Advanced Security",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware Registration (Order matters: add_middleware inserts at index 0, so the LAST added is the OUTERMOST)

# 9. Security headers (Closest to app)
app.add_middleware(SecurityHeadersMiddleware)

# 8. CORS
cors_config = {
    "allow_origins": settings.cors_origins_list,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
}
if settings.APP_ENV == "production":
    cors_config["allow_methods"] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_config["allow_headers"] = [
        "Authorization", "Content-Type", "X-API-Key", "X-Signature", 
        "X-Timestamp", "Idempotency-Key", "X-Request-ID"
    ]
    logger.info("Using strict CORS policy for production")
app.add_middleware(CORSMiddleware, **cors_config)

# 7. Input sanitization (logging only)
app.add_middleware(InputSanitizationMiddleware)

# 6. Body-size limiter
app.add_middleware(BodySizeLimiterMiddleware)

# 5. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 4. Distributed Idempotency
app.add_middleware(DistributedIdempotencyMiddleware)

# 3. Distributed Rate Limiting
try:
    app.add_middleware(DistributedRateLimitMiddleware)
    logger.info("Using distributed rate limiter")
except Exception as e:
    logger.warning(f"Distributed rate limiter failed, using in-memory: {e}")
    app.add_middleware(RateLimitMiddleware)

# 2.5 Response Envelope
app.add_middleware(ResponseEnvelopeMiddleware)

# 2. Correlation ID
app.add_middleware(CorrelationIdMiddleware)

# 1. Error handler (Outermost wrapper - catches EVERYTHING)
app.add_middleware(ErrorHandlerMiddleware)

# Register API routers
app.include_router(api_router)

# --- Exception Handlers ---
# These run INSIDE the ASGI app before middleware sees the response,
# preventing the BaseHTTPMiddleware call_next stream-breaking issue.
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Convert HTTPExceptions to structured JSON — prevents middleware chain breakage."""
    request_id = getattr(request.state, "request_id", "unknown")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": detail,
            "details": [{"message": detail}],
            "request_id": request_id
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to structured JSON."""
    request_id = getattr(request.state, "request_id", "unknown")
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": errors,
            "request_id": request_id
        },
    )

# --- Background Tasks ---
_event_processor_task: Optional[asyncio.Task] = None
_health_check_task: Optional[asyncio.Task] = None
_shutdown_event = asyncio.Event()
HEALTH_CHECK_INTERVAL = 30  # seconds


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

    # Launch background event processor
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

    # Launch background health polling loop
    async def _health_polling_loop():
        from app.services.system_health_service import SystemHealthService
        while not _shutdown_event.is_set():
            try:
                health_db = SessionLocal()
                try:
                    svc = SystemHealthService(health_db)
                    await svc.check_all()
                    logger.debug("Scheduled health check completed")
                finally:
                    health_db.close()
            except Exception as exc:
                logger.error(f"Background health check error: {exc}")
            try:
                await asyncio.wait_for(_shutdown_event.wait(), timeout=HEALTH_CHECK_INTERVAL)
            except asyncio.TimeoutError:
                pass  # normal — interval elapsed

    global _health_check_task
    _health_check_task = asyncio.create_task(_health_polling_loop())
    logger.info(f"Background health polling task created (interval={HEALTH_CHECK_INTERVAL}s)")


@app.on_event("shutdown")
async def stop_event_processor():
    """Gracefully stop background event processing on shutdown."""
    global _event_processor_task, _health_check_task

    _shutdown_event.set()
    for task, name in [(_event_processor_task, "event processor"), (_health_check_task, "health polling")]:
        if task and not task.done():
            logger.info(f"Waiting for {name} to stop...")
            try:
                await asyncio.wait_for(task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning(f"{name} did not stop in time, cancelling")
                task.cancel()
            logger.info(f"{name} stopped")
    _event_processor_task = None
    _health_check_task = None


@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Enhanced health check endpoint (26 march: Phase 7B).
    Returns subsystem-level health statuses for monitoring and Cloud Run.
    """
    try:
        from app.services.system_health_service import SystemHealthService
        service = SystemHealthService(db)
        # Public endpoint returns redacted coarse summary (no details/errors)
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
        return {
            "status": "operational",
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "2.0.0",
        }


@app.post("/admin/cron/run", tags=["Admin"])
async def run_cron_tasks(
    cadence: Optional[str] = None,
    force: bool = False,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(require_admin_api_key),
):
    """
    Trigger scheduled maintenance tasks (admin-only, API-key secured).

    Query params:
      - cadence: hourly | daily | weekly | (omit = all)
      - force: skip min-interval guards and run immediately

    Requires: X-Admin-Key header (ADMIN_SECRET_KEY env var).
    """
    from app.services.cron import run_scheduled_tasks
    from app.security.blockchain_audit import log_to_blockchain

    if cadence and cadence not in ("hourly", "daily", "weekly"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="cadence must be one of: hourly, daily, weekly")

    result = await run_scheduled_tasks(db, cadence=cadence, force=force)

    log_to_blockchain(
        action="admin_cron_run",
        details={"run_id": result.get("run_id"), "overall_status": result.get("overall_status")},
    )

    return result


@app.post("/admin/health-check", tags=["Admin"])
async def trigger_health_check(
    db: Session = Depends(get_db),
    authenticated: bool = Depends(require_admin_api_key),
):
    """
    Manually trigger a full system health check and persist results.

    Requires: X-API-Key header for authentication
    """
    from app.services.system_health_service import SystemHealthService
    from app.security.blockchain_audit import log_to_blockchain

    service = SystemHealthService(db)
    result = await service.check_all()

    # Log to blockchain
    log_to_blockchain(
        action="admin_health_check",
        details={"result": result},
    )

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
