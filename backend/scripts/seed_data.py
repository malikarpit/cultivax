"""
Seed Data Script — Day 28

Creates sample data for demo and development:
- Admin user
- Farmer users
- Provider users + ServiceProvider records
- CropRuleTemplates (wheat, rice, cotton)
- CropInstances for each farmer
- Sample service requests

Usage:
    cd backend
    python -m scripts.seed_data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.crop_rule_template import CropRuleTemplate
from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.security.auth import get_password_hash


# ---------------------------------------------------------------------------
# Crop Rule Templates — real agronomic data for wheat, rice, cotton
# ---------------------------------------------------------------------------

WHEAT_TEMPLATE = {
    "crop_type": "wheat",
    "variety": "HD-2967",
    "region": "Punjab",
    "version_id": "1.0",
    "effective_from_date": date(2025, 10, 1),
    "status": "active",
    "description": "Standard wheat template for North India (Rabi crop). Based on HD-2967 variety.",
    "stage_definitions": [
        {"name": "Germination", "start_day": 1, "end_day": 7, "description": "Seed germination and emergence"},
        {"name": "Seedling", "start_day": 8, "end_day": 21, "description": "Early vegetative growth"},
        {"name": "Tillering", "start_day": 22, "end_day": 45, "description": "Crown root and tiller development"},
        {"name": "Jointing", "start_day": 46, "end_day": 65, "description": "Stem elongation"},
        {"name": "Booting", "start_day": 66, "end_day": 80, "description": "Flag leaf and head development"},
        {"name": "Heading", "start_day": 81, "end_day": 90, "description": "Head emergence and flowering"},
        {"name": "Grain Fill", "start_day": 91, "end_day": 120, "description": "Grain formation and filling"},
        {"name": "Maturity", "start_day": 121, "end_day": 140, "description": "Physiological maturity"},
    ],
    "risk_parameters": {
        "max_stress_threshold": 0.7,
        "critical_risk_index": 0.8,
        "drought_sensitivity": 0.6,
        "pest_risk_stages": ["Tillering", "Heading", "Grain Fill"],
    },
    "irrigation_windows": {
        "Germination": {"frequency_days": 3, "critical": True},
        "Tillering": {"frequency_days": 15, "critical": True},
        "Jointing": {"frequency_days": 20, "critical": False},
        "Heading": {"frequency_days": 10, "critical": True},
        "Grain Fill": {"frequency_days": 15, "critical": True},
    },
    "fertilizer_windows": {
        "Seedling": {"urea_kg_per_acre": 25, "dap_kg_per_acre": 50},
        "Tillering": {"urea_kg_per_acre": 25, "dap_kg_per_acre": 0},
        "Heading": {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
    },
    "harvest_windows": {
        "optimal_moisture_pct": 12,
        "expected_yield_kg_per_acre": 1800,
        "harvest_start_day": 130,
        "harvest_end_day": 145,
    },
    "drift_limits": {
        "max_stage_drift_days": 7,
        "warning_drift_days": 4,
        "auto_atrisk_drift_days": 10,
    },
}

RICE_TEMPLATE = {
    "crop_type": "rice",
    "variety": "Pusa Basmati 1121",
    "region": "Haryana",
    "version_id": "1.0",
    "effective_from_date": date(2025, 6, 1),
    "status": "active",
    "description": "Standard rice template for North India (Kharif crop). Basmati variety.",
    "stage_definitions": [
        {"name": "Nursery", "start_day": 1, "end_day": 25, "description": "Nursery bed raising"},
        {"name": "Transplanting", "start_day": 26, "end_day": 35, "description": "Transplanting to main field"},
        {"name": "Tillering", "start_day": 36, "end_day": 60, "description": "Active tillering phase"},
        {"name": "Panicle Initiation", "start_day": 61, "end_day": 80, "description": "Reproductive stage begins"},
        {"name": "Booting", "start_day": 81, "end_day": 95, "description": "Panicle development"},
        {"name": "Heading", "start_day": 96, "end_day": 105, "description": "Panicle emergence and flowering"},
        {"name": "Grain Fill", "start_day": 106, "end_day": 130, "description": "Grain formation"},
        {"name": "Maturity", "start_day": 131, "end_day": 150, "description": "Grain hardening and maturity"},
    ],
    "risk_parameters": {
        "max_stress_threshold": 0.65,
        "critical_risk_index": 0.75,
        "drought_sensitivity": 0.8,
        "pest_risk_stages": ["Tillering", "Booting", "Heading"],
    },
    "irrigation_windows": {
        "Nursery": {"frequency_days": 2, "critical": True},
        "Transplanting": {"frequency_days": 1, "critical": True},
        "Tillering": {"frequency_days": 5, "critical": True},
        "Heading": {"frequency_days": 5, "critical": True},
        "Grain Fill": {"frequency_days": 7, "critical": False},
    },
    "fertilizer_windows": {
        "Transplanting": {"urea_kg_per_acre": 20, "dap_kg_per_acre": 40},
        "Tillering": {"urea_kg_per_acre": 30, "dap_kg_per_acre": 0},
        "Panicle Initiation": {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
    },
    "harvest_windows": {
        "optimal_moisture_pct": 20,
        "expected_yield_kg_per_acre": 2200,
        "harvest_start_day": 140,
        "harvest_end_day": 160,
    },
    "drift_limits": {
        "max_stage_drift_days": 5,
        "warning_drift_days": 3,
        "auto_atrisk_drift_days": 8,
    },
}

COTTON_TEMPLATE = {
    "crop_type": "cotton",
    "variety": "Bt Cotton",
    "region": "Gujarat",
    "version_id": "1.0",
    "effective_from_date": date(2025, 5, 1),
    "status": "active",
    "description": "Standard cotton template for Western India (Kharif crop). Bt Cotton variety.",
    "stage_definitions": [
        {"name": "Germination", "start_day": 1, "end_day": 10, "description": "Seed germination"},
        {"name": "Seedling", "start_day": 11, "end_day": 30, "description": "Vegetative establishment"},
        {"name": "Squaring", "start_day": 31, "end_day": 60, "description": "Square/bud formation"},
        {"name": "Flowering", "start_day": 61, "end_day": 90, "description": "Bloom period"},
        {"name": "Boll Development", "start_day": 91, "end_day": 130, "description": "Boll formation and growth"},
        {"name": "Boll Opening", "start_day": 131, "end_day": 160, "description": "Boll opening and fiber maturity"},
        {"name": "Harvest", "start_day": 161, "end_day": 180, "description": "Multiple pickings"},
    ],
    "risk_parameters": {
        "max_stress_threshold": 0.6,
        "critical_risk_index": 0.7,
        "drought_sensitivity": 0.5,
        "pest_risk_stages": ["Squaring", "Flowering", "Boll Development"],
    },
    "irrigation_windows": {
        "Seedling": {"frequency_days": 7, "critical": False},
        "Squaring": {"frequency_days": 12, "critical": True},
        "Flowering": {"frequency_days": 10, "critical": True},
        "Boll Development": {"frequency_days": 15, "critical": True},
    },
    "fertilizer_windows": {
        "Seedling": {"urea_kg_per_acre": 20, "dap_kg_per_acre": 30},
        "Squaring": {"urea_kg_per_acre": 25, "dap_kg_per_acre": 0},
        "Flowering": {"urea_kg_per_acre": 15, "dap_kg_per_acre": 0},
    },
    "harvest_windows": {
        "optimal_moisture_pct": 8,
        "expected_yield_kg_per_acre": 800,
        "harvest_start_day": 155,
        "harvest_end_day": 185,
    },
    "drift_limits": {
        "max_stage_drift_days": 10,
        "warning_drift_days": 5,
        "auto_atrisk_drift_days": 15,
    },
}


# ---------------------------------------------------------------------------
# Seed Functions
# ---------------------------------------------------------------------------

def seed_users(db: Session) -> dict:
    """Create sample users: admin, farmers, providers."""
    password_hash = get_password_hash("Test@1234")

    users = {}

    # Admin
    admin = User(
        id=uuid4(),
        full_name="Arpit Kumar (Admin)",
        phone="+919999000001",
        email="admin@cultivax.in",
        password_hash=password_hash,
        role="admin",
        region="National",
        is_active=True,
        is_onboarded=True,
    )
    db.add(admin)
    users["admin"] = admin

    # Farmers
    farmers_data = [
        {"name": "Rajveer Singh", "phone": "+919876543001", "region": "Punjab", "email": "rajveer@demo.in"},
        {"name": "Lakshmi Devi", "phone": "+919876543002", "region": "Haryana", "email": "lakshmi@demo.in"},
        {"name": "Mahesh Patel", "phone": "+919876543003", "region": "Gujarat", "email": "mahesh@demo.in"},
        {"name": "Anand Sharma", "phone": "+919876543004", "region": "Rajasthan", "email": "anand@demo.in"},
    ]

    for i, fd in enumerate(farmers_data):
        farmer = User(
            id=uuid4(),
            full_name=fd["name"],
            phone=fd["phone"],
            email=fd["email"],
            password_hash=password_hash,
            role="farmer",
            region=fd["region"],
            is_active=True,
            is_onboarded=True,
        )
        db.add(farmer)
        users[f"farmer_{i}"] = farmer

    # Providers
    providers_data = [
        {"name": "Gurpreet Equipment", "phone": "+919876543010", "region": "Punjab", "email": "gurpreet@demo.in"},
        {"name": "Haryana Agri Services", "phone": "+919876543011", "region": "Haryana", "email": "haryana_agri@demo.in"},
        {"name": "Gujarat Farm Solutions", "phone": "+919876543012", "region": "Gujarat", "email": "guj_farm@demo.in"},
    ]

    for i, pd in enumerate(providers_data):
        prov_user = User(
            id=uuid4(),
            full_name=pd["name"],
            phone=pd["phone"],
            email=pd["email"],
            password_hash=password_hash,
            role="provider",
            region=pd["region"],
            is_active=True,
            is_onboarded=True,
        )
        db.add(prov_user)
        users[f"provider_{i}"] = prov_user

    db.flush()
    print(f"  ✓ Created {len(users)} users")
    return users


def seed_providers(db: Session, users: dict) -> dict:
    """Create ServiceProvider records for provider users."""
    providers = {}
    provider_configs = [
        {
            "key": "provider_0",
            "business_name": "Gurpreet Equipment Rentals",
            "service_type": "equipment_rental",
            "crop_specializations": ["wheat", "rice"],
            "trust_score": 0.82,
            "is_verified": True,
            "description": "Premium tractor and harvester rental service in Punjab.",
        },
        {
            "key": "provider_1",
            "business_name": "Haryana Agri Services Ltd",
            "service_type": "labor",
            "crop_specializations": ["rice", "sugarcane"],
            "trust_score": 0.75,
            "is_verified": True,
            "description": "Skilled agricultural labor for transplanting and harvesting.",
        },
        {
            "key": "provider_2",
            "business_name": "Gujarat Farm Solutions",
            "service_type": "advisory",
            "crop_specializations": ["cotton", "groundnut"],
            "trust_score": 0.68,
            "is_verified": False,
            "description": "Expert agronomic advisory for cotton and cash crops.",
        },
    ]

    for cfg in provider_configs:
        user = users[cfg["key"]]
        sp = ServiceProvider(
            id=uuid4(),
            user_id=user.id,
            business_name=cfg["business_name"],
            service_type=cfg["service_type"],
            region=user.region,
            crop_specializations=cfg["crop_specializations"],
            trust_score=cfg["trust_score"],
            is_verified=cfg["is_verified"],
            description=cfg["description"],
            contact_name=user.full_name,
            contact_phone=user.phone,
        )
        db.add(sp)
        providers[cfg["key"]] = sp

    db.flush()
    print(f"  ✓ Created {len(providers)} service providers")
    return providers


def seed_rule_templates(db: Session) -> list:
    """Create crop rule templates for wheat, rice, cotton."""
    templates = []

    for template_data in [WHEAT_TEMPLATE, RICE_TEMPLATE, COTTON_TEMPLATE]:
        tpl = CropRuleTemplate(
            id=uuid4(),
            **template_data,
        )
        db.add(tpl)
        templates.append(tpl)

    db.flush()
    print(f"  ✓ Created {len(templates)} crop rule templates (wheat, rice, cotton)")
    return templates


def seed_crops(db: Session, users: dict, templates: list) -> list:
    """Create sample crop instances for each farmer."""
    crops = []
    today = date.today()

    crop_configs = [
        # Farmer 0 (Punjab) — wheat
        {
            "farmer_key": "farmer_0",
            "crop_type": "wheat",
            "variety": "HD-2967",
            "sowing_date": today - timedelta(days=45),
            "state": "Active",
            "stage": "Tillering",
            "current_day_number": 45,
            "baseline_day_number": 45,
            "stress_score": 0.15,
            "risk_index": 0.12,
            "seasonal_window_category": "Optimal",
            "land_area": 5.0,
        },
        # Farmer 0 — second wheat crop, slightly delayed
        {
            "farmer_key": "farmer_0",
            "crop_type": "wheat",
            "variety": "PBW-343",
            "sowing_date": today - timedelta(days=30),
            "state": "Delayed",
            "stage": "Seedling",
            "current_day_number": 28,
            "baseline_day_number": 30,
            "stress_score": 0.35,
            "risk_index": 0.28,
            "seasonal_window_category": "Late",
            "land_area": 3.0,
        },
        # Farmer 1 (Haryana) — rice
        {
            "farmer_key": "farmer_1",
            "crop_type": "rice",
            "variety": "Pusa Basmati 1121",
            "sowing_date": today - timedelta(days=60),
            "state": "Active",
            "stage": "Tillering",
            "current_day_number": 60,
            "baseline_day_number": 58,
            "stress_score": 0.20,
            "risk_index": 0.18,
            "seasonal_window_category": "Optimal",
            "land_area": 8.0,
        },
        # Farmer 2 (Gujarat) — cotton at risk
        {
            "farmer_key": "farmer_2",
            "crop_type": "cotton",
            "variety": "Bt Cotton",
            "sowing_date": today - timedelta(days=75),
            "state": "AtRisk",
            "stage": "Flowering",
            "current_day_number": 72,
            "baseline_day_number": 75,
            "stress_score": 0.72,
            "risk_index": 0.68,
            "seasonal_window_category": "Optimal",
            "land_area": 10.0,
        },
        # Farmer 3 (Rajasthan) — wheat, harvested
        {
            "farmer_key": "farmer_3",
            "crop_type": "wheat",
            "variety": "Raj-4120",
            "sowing_date": today - timedelta(days=140),
            "state": "Harvested",
            "stage": "Maturity",
            "current_day_number": 140,
            "baseline_day_number": 140,
            "stress_score": 0.08,
            "risk_index": 0.05,
            "seasonal_window_category": "Optimal",
            "land_area": 6.0,
        },
    ]

    for cfg in crop_configs:
        farmer = users[cfg.pop("farmer_key")]
        crop = CropInstance(
            id=uuid4(),
            farmer_id=farmer.id,
            region=farmer.region,
            **cfg,
        )
        db.add(crop)
        crops.append(crop)

    db.flush()
    print(f"  ✓ Created {len(crops)} crop instances")
    return crops


def seed_service_requests(db: Session, users: dict, providers: dict) -> list:
    """Create sample service requests."""
    requests = []
    now = datetime.now(timezone.utc)

    request_configs = [
        {
            "farmer_key": "farmer_0",
            "provider_key": "provider_0",
            "service_type": "equipment_rental",
            "crop_type": "wheat",
            "status": "Completed",
            "description": "Need tractor for field preparation",
            "requested_date": now - timedelta(days=10),
            "completed_date": now - timedelta(days=8),
            "agreed_price": 2500.0,
            "final_price": 2500.0,
        },
        {
            "farmer_key": "farmer_1",
            "provider_key": "provider_1",
            "service_type": "labor",
            "crop_type": "rice",
            "status": "Accepted",
            "description": "Need 5 workers for rice transplanting",
            "requested_date": now - timedelta(days=3),
            "agreed_price": 5000.0,
        },
        {
            "farmer_key": "farmer_2",
            "provider_key": "provider_2",
            "service_type": "advisory",
            "crop_type": "cotton",
            "status": "Pending",
            "description": "Cotton showing signs of pest attack — need expert advice",
            "requested_date": now - timedelta(days=1),
        },
    ]

    for cfg in request_configs:
        farmer = users[cfg.pop("farmer_key")]
        provider = providers[cfg.pop("provider_key")]
        sr = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            **cfg,
        )
        if sr.status == "Accepted":
            sr.provider_acknowledged_at = now - timedelta(days=2)
        db.add(sr)
        requests.append(sr)

    db.flush()
    print(f"  ✓ Created {len(requests)} service requests")
    return requests


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_seed():
    """Run the full seed data pipeline."""
    print("\n🌱 CultivaX Seed Data Script")
    print("=" * 50)

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"\n⚠️  Database already has {existing_users} users.")
            response = input("   Continue seeding? (y/N): ").strip().lower()
            if response != "y":
                print("   Aborted.")
                return

        print("\n📦 Seeding data...")
        users = seed_users(db)
        providers = seed_providers(db, users)
        templates = seed_rule_templates(db)
        crops = seed_crops(db, users, templates)
        requests = seed_service_requests(db, users, providers)

        db.commit()
        print("\n✅ Seed data committed successfully!")

        # Summary
        print("\n📋 Summary:")
        print(f"   Users:           {len(users)} (1 admin, 4 farmers, 3 providers)")
        print(f"   Providers:       {len(providers)}")
        print(f"   Rule Templates:  {len(templates)} (wheat, rice, cotton)")
        print(f"   Crop Instances:  {len(crops)}")
        print(f"   Service Requests:{len(requests)}")

        print("\n🔑 Login Credentials (all users):")
        print("   Password: Test@1234")
        print("   Admin:    +919999000001")
        print("   Farmer:   +919876543001 to +919876543004")
        print("   Provider: +919876543010 to +919876543012")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
