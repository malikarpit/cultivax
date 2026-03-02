"""
CultivaX — Main Application Entry Point

FastAPI application with CORS, middleware, and API router registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.idempotency import IdempotencyMiddleware
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Crop Lifecycle Management & Service Orchestration Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware (order matters — outermost first)
app.add_middleware(ErrorHandlerMiddleware)
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


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring and Cloud Run."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }
