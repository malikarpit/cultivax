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
from app.api.v1.media import router as media_router
from app.api.v1.admin import router as admin_router
from app.api.v1.simulation import router as simulation_router
import importlib as _il
_yield_mod = _il.import_module("app.api.v1.yield")
yield_router = _yield_mod.router
from app.api.v1.service_requests import router as service_requests_router
from app.api.v1.ml import router as ml_router
from app.api.v1.rules import router as rules_router
from app.api.v1.features import router as features_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.sync import router as sync_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.labor import router as labor_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(crops_router)
api_router.include_router(actions_router)
api_router.include_router(providers_router)
api_router.include_router(equipment_router)
api_router.include_router(media_router)
api_router.include_router(admin_router)
api_router.include_router(simulation_router)
api_router.include_router(yield_router)
api_router.include_router(service_requests_router)
api_router.include_router(ml_router)
api_router.include_router(rules_router)
api_router.include_router(features_router)
api_router.include_router(alerts_router)
api_router.include_router(recommendations_router)
api_router.include_router(sync_router)
api_router.include_router(reviews_router)
api_router.include_router(labor_router)
