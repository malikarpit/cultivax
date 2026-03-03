"""
Models Package

Import all models so Alembic's autogenerate can detect them.
"""

from app.models.base import BaseModel, Base
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.action_log import ActionLog
from app.models.snapshot import CropInstanceSnapshot
from app.models.deviation import DeviationProfile
from app.models.yield_record import YieldRecord
from app.models.event_log import EventLog
from app.models.admin_audit import AdminAuditLog
from app.models.feature_flag import FeatureFlag
from app.models.abuse_flag import AbuseFlag
from app.models.sowing_calendar import RegionalSowingCalendar
from app.models.service_provider import ServiceProvider
from app.models.equipment import Equipment
from app.models.service_request import ServiceRequest
from app.models.service_review import ServiceReview
from app.models.provider_availability import ProviderAvailability
from app.models.ml_model import MLModel
from app.models.ml_training import MLTrainingAudit
from app.models.media_file import MediaFile
from app.models.stress_history import StressHistory
from app.models.regional_cluster import RegionalCluster
from app.models.labor import Labor
from app.models.service_request_event import ServiceRequestEvent
from app.models.pest_alert_history import PestAlertHistory

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "CropInstance",
    "ActionLog",
    "CropInstanceSnapshot",
    "DeviationProfile",
    "YieldRecord",
    "EventLog",
    "AdminAuditLog",
    "FeatureFlag",
    "AbuseFlag",
    "RegionalSowingCalendar",
    "ServiceProvider",
    "Equipment",
    "Labor",
    "ServiceRequest",
    "ServiceReview",
    "ServiceRequestEvent",
    "ProviderAvailability",
    "MLModel",
    "MLTrainingAudit",
    "MediaFile",
    "StressHistory",
    "RegionalCluster",
    "PestAlertHistory",
]
