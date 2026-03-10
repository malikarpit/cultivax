"""
API v1 Router

Aggregates all v1 API routers into a single router.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.crops import router as crops_router
from app.api.v1.actions import router as actions_router
from app.api.v1.providers import router as providers_router
from app.api.v1.equipment import router as equipment_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(crops_router)
api_router.include_router(actions_router)
api_router.include_router(providers_router)
api_router.include_router(equipment_router)
