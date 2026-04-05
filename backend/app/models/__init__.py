"""
Models Package

Import all models so Alembic's autogenerate can detect them.
"""

from app.models.abuse_flag import AbuseFlag
from app.models.active_session import ActiveSession
from app.models.otp_code import OTPCode
from app.models.action_log import ActionLog
from app.models.admin_audit import AdminAuditLog
from app.models.alert import Alert
from app.models.backup_log import BackupLog
from app.models.base import Base, BaseModel
from app.models.crop_instance import CropInstance
from app.models.crop_rule_template import CropRuleTemplate
from app.models.deviation import DeviationProfile
from app.models.deviation_archive import DeviationArchive
from app.models.equipment import Equipment
from app.models.event_log import EventLog
from app.models.exposure_log import ExposureLog
from app.models.farmer_audit import FarmerAudit
from app.models.feature_flag import FeatureFlag
from app.models.labor import Labor
from app.models.land_parcel import LandParcel
from app.models.market_price import MarketPrice
from app.models.media_file import MediaFile
from app.models.ml_feedback import MLFeedback
from app.models.ml_inference_audit import MLInferenceAudit
from app.models.ml_model import MLModel
from app.models.ml_training import MLTrainingAudit
from app.models.pest_alert_history import PestAlertHistory
from app.models.provider_availability import ProviderAvailability
from app.models.recommendation import Recommendation
from app.models.region_config import RegionConfig
from app.models.regional_cluster import RegionalCluster
from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.service_request_event import ServiceRequestEvent
from app.models.service_review import ServiceReview
from app.models.snapshot import CropInstanceSnapshot
from app.models.sowing_calendar import RegionalSowingCalendar
from app.models.stress_history import StressHistory
from app.models.system_health import SystemHealth
from app.models.user import User
from app.models.user_report import UserReport
from app.models.weather_snapshot import WeatherSnapshot
from app.models.whatsapp_session import WhatsAppSession
from app.models.yield_record import YieldRecord

from app.models.dispute_case import DisputeCase
from app.models.official_scheme import OfficialScheme
from app.models.scheme_redirect_log import SchemeRedirectLog
from app.models.user_consent import UserConsent
from app.models.sms_delivery_log import SmsDeliveryLog

__all__ = [
    "Base",
    "BaseModel",
    "ActiveSession",
    "OTPCode",
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
    "MLInferenceAudit",
    "MLTrainingAudit",
    "MediaFile",
    "StressHistory",
    "RegionalCluster",
    "PestAlertHistory",
    "CropRuleTemplate",
    "Alert",
    "Recommendation",
    "MLFeedback",
    "SystemHealth",
    "MarketPrice",
    "DeviationArchive",
    "BackupLog",
    "LandParcel",
    "WhatsAppSession",
    "FarmerAudit",
    "WeatherSnapshot",
    "ExposureLog",
    "UserReport",
    "RegionConfig",
    "DisputeCase",
    "OfficialScheme",
    "SchemeRedirectLog",
    "UserConsent",
    "SmsDeliveryLog",
]
