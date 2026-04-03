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
from app.api.v1.land_parcels import router as land_parcels_router
from app.api.v1.weather import router as weather_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.translations import router as translations_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.whatsapp import router as whatsapp_router  # API-0131
from app.api.v1.sync import crops_sync_router  # API-0103 /crops/{id}/sync-batch
from app.api.v1.csp_report import router as csp_report_router  # CSP violation ingestion
from app.api.v1.health import router as health_router  # API-0150 /api/v1/health
from app.api.v1.operations import router as operations_router  # API-0108 operations status

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
from fastapi import Depends
from app.security.feature_flags import require_feature_flag

api_router.include_router(service_requests_router)
api_router.include_router(
    ml_router, 
    dependencies=[Depends(require_feature_flag("ML", enabled_by_default=True))]
)
api_router.include_router(rules_router)
api_router.include_router(features_router)
api_router.include_router(alerts_router)
api_router.include_router(recommendations_router)
api_router.include_router(sync_router)
api_router.include_router(crops_sync_router)  # API-0103: /crops/{id}/sync-batch
api_router.include_router(reviews_router)
api_router.include_router(labor_router)
api_router.include_router(land_parcels_router)
api_router.include_router(weather_router)
api_router.include_router(dashboard_router)
api_router.include_router(translations_router)
api_router.include_router(onboarding_router)
api_router.include_router(whatsapp_router)  # API-0131: WhatsApp webhook
api_router.include_router(csp_report_router)  # CSP violation ingestion (report-to)
api_router.include_router(health_router)  # API-0150: /api/v1/health
api_router.include_router(operations_router)  # API-0108: /api/v1/operations/{id}
