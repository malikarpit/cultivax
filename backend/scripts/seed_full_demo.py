"""
CultivaX — Full Demo Data Seed Script
======================================

Populates the database with realistic, comprehensive demo data:

  • 1  Admin
  • 20 Farmers   (across Punjab, Haryana, UP, MP, Rajasthan, Gujarat, Maharashtra)
  • 15 Providers  (equipment rental, labor, advisory, pest control, soil testing)
  • 6  Crop Rule Templates  (wheat, rice, cotton, sugarcane, maize, mustard)
  • ~2 Crops per farmer  (40 crops total, various states)
  • ~10 Actions per crop (400 actions total)
  • ~5 Services per provider (service requests linked to farmers)
  • Service reviews for completed requests
  • Yield records for harvested crops

Usage:
    cd backend
    python -m scripts.seed_full_demo

    Force re-seed (skip prompt):
    python -m scripts.seed_full_demo --force
"""

import sys
import os
import random
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session

from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.crop_rule_template import CropRuleTemplate
from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.service_review import ServiceReview
from app.models.action_log import ActionLog
from app.models.yield_record import YieldRecord
from app.security.auth import hash_password as get_password_hash

PASSWORD_HASH = get_password_hash("Demo@12345")
TODAY = date.today()


# ─────────────────────────────────────────────────────────────────────────────
# CROP RULE TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "crop_type": "wheat",
        "variety": "HD-2967",
        "region": "Punjab",
        "version_id": "1.0",
        "effective_from_date": date(2025, 10, 1),
        "status": "active",
        "description": "Standard wheat template for North India (Rabi). HD-2967 variety.",
        "stage_definitions": [
            {"name": "Germination",  "start_day": 1,   "end_day": 7,   "description": "Seed germination and emergence"},
            {"name": "Seedling",     "start_day": 8,   "end_day": 21,  "description": "Early vegetative growth"},
            {"name": "Tillering",    "start_day": 22,  "end_day": 45,  "description": "Crown root and tiller development"},
            {"name": "Jointing",     "start_day": 46,  "end_day": 65,  "description": "Stem elongation"},
            {"name": "Booting",      "start_day": 66,  "end_day": 80,  "description": "Flag leaf development"},
            {"name": "Heading",      "start_day": 81,  "end_day": 90,  "description": "Head emergence and flowering"},
            {"name": "Grain Fill",   "start_day": 91,  "end_day": 120, "description": "Grain formation"},
            {"name": "Maturity",     "start_day": 121, "end_day": 140, "description": "Physiological maturity"},
        ],
        "risk_parameters": {
            "max_stress_threshold": 0.70, "critical_risk_index": 0.80,
            "drought_sensitivity": 0.60,
            "pest_risk_stages": ["Tillering", "Heading", "Grain Fill"],
        },
        "irrigation_windows": {
            "Germination": {"frequency_days": 3, "critical": True},
            "Tillering":   {"frequency_days": 15, "critical": True},
            "Jointing":    {"frequency_days": 20, "critical": False},
            "Heading":     {"frequency_days": 10, "critical": True},
            "Grain Fill":  {"frequency_days": 15, "critical": True},
        },
        "fertilizer_windows": {
            "Seedling":  {"urea_kg_per_acre": 25, "dap_kg_per_acre": 50},
            "Tillering": {"urea_kg_per_acre": 25, "dap_kg_per_acre": 0},
            "Heading":   {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
        },
        "harvest_windows": {
            "optimal_moisture_pct": 12, "expected_yield_kg_per_acre": 1800,
            "harvest_start_day": 130,   "harvest_end_day": 145,
        },
        "drift_limits": {
            "max_stage_drift_days": 7, "warning_drift_days": 4, "auto_atrisk_drift_days": 10,
        },
    },
    {
        "crop_type": "rice",
        "variety": "Pusa Basmati 1121",
        "region": "Haryana",
        "version_id": "1.0",
        "effective_from_date": date(2025, 6, 1),
        "status": "active",
        "description": "Standard Basmati rice for North India (Kharif).",
        "stage_definitions": [
            {"name": "Nursery",             "start_day": 1,   "end_day": 25,  "description": "Nursery bed raising"},
            {"name": "Transplanting",        "start_day": 26,  "end_day": 35,  "description": "Transplanting to main field"},
            {"name": "Tillering",           "start_day": 36,  "end_day": 60,  "description": "Active tillering"},
            {"name": "Panicle Initiation",  "start_day": 61,  "end_day": 80,  "description": "Reproductive stage"},
            {"name": "Booting",             "start_day": 81,  "end_day": 95,  "description": "Panicle development"},
            {"name": "Heading",             "start_day": 96,  "end_day": 105, "description": "Panicle emergence"},
            {"name": "Grain Fill",          "start_day": 106, "end_day": 130, "description": "Grain formation"},
            {"name": "Maturity",            "start_day": 131, "end_day": 150, "description": "Grain hardening"},
        ],
        "risk_parameters": {
            "max_stress_threshold": 0.65, "critical_risk_index": 0.75,
            "drought_sensitivity": 0.80,
            "pest_risk_stages": ["Tillering", "Booting", "Heading"],
        },
        "irrigation_windows": {
            "Nursery":       {"frequency_days": 2, "critical": True},
            "Transplanting": {"frequency_days": 1, "critical": True},
            "Tillering":     {"frequency_days": 5, "critical": True},
            "Heading":       {"frequency_days": 5, "critical": True},
            "Grain Fill":    {"frequency_days": 7, "critical": False},
        },
        "fertilizer_windows": {
            "Transplanting":       {"urea_kg_per_acre": 20, "dap_kg_per_acre": 40},
            "Tillering":           {"urea_kg_per_acre": 30, "dap_kg_per_acre": 0},
            "Panicle Initiation":  {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
        },
        "harvest_windows": {
            "optimal_moisture_pct": 20, "expected_yield_kg_per_acre": 2200,
            "harvest_start_day": 140,   "harvest_end_day": 160,
        },
        "drift_limits": {
            "max_stage_drift_days": 5, "warning_drift_days": 3, "auto_atrisk_drift_days": 8,
        },
    },
    {
        "crop_type": "cotton",
        "variety": "Bt Cotton",
        "region": "Gujarat",
        "version_id": "1.0",
        "effective_from_date": date(2025, 5, 1),
        "status": "active",
        "description": "Bt Cotton template for Western India (Kharif).",
        "stage_definitions": [
            {"name": "Germination",      "start_day": 1,   "end_day": 10,  "description": "Seed germination"},
            {"name": "Seedling",         "start_day": 11,  "end_day": 30,  "description": "Vegetative establishment"},
            {"name": "Squaring",         "start_day": 31,  "end_day": 60,  "description": "Square/bud formation"},
            {"name": "Flowering",        "start_day": 61,  "end_day": 90,  "description": "Bloom period"},
            {"name": "Boll Development", "start_day": 91,  "end_day": 130, "description": "Boll growth"},
            {"name": "Boll Opening",     "start_day": 131, "end_day": 160, "description": "Fiber maturity"},
            {"name": "Harvest",          "start_day": 161, "end_day": 180, "description": "Multiple pickings"},
        ],
        "risk_parameters": {
            "max_stress_threshold": 0.60, "critical_risk_index": 0.70,
            "drought_sensitivity": 0.50,
            "pest_risk_stages": ["Squaring", "Flowering", "Boll Development"],
        },
        "irrigation_windows": {
            "Seedling":         {"frequency_days": 7,  "critical": False},
            "Squaring":         {"frequency_days": 12, "critical": True},
            "Flowering":        {"frequency_days": 10, "critical": True},
            "Boll Development": {"frequency_days": 15, "critical": True},
        },
        "fertilizer_windows": {
            "Seedling":  {"urea_kg_per_acre": 20, "dap_kg_per_acre": 30},
            "Squaring":  {"urea_kg_per_acre": 25, "dap_kg_per_acre": 0},
            "Flowering": {"urea_kg_per_acre": 15, "dap_kg_per_acre": 0},
        },
        "harvest_windows": {
            "optimal_moisture_pct": 8, "expected_yield_kg_per_acre": 800,
            "harvest_start_day": 155,  "harvest_end_day": 185,
        },
        "drift_limits": {
            "max_stage_drift_days": 10, "warning_drift_days": 5, "auto_atrisk_drift_days": 15,
        },
    },
    {
        "crop_type": "sugarcane",
        "variety": "Co-238",
        "region": "Uttar Pradesh",
        "version_id": "1.0",
        "effective_from_date": date(2025, 2, 1),
        "status": "active",
        "description": "Long-duration sugarcane for UP and Bihar.",
        "stage_definitions": [
            {"name": "Germination",     "start_day": 1,   "end_day": 30,  "description": "Germination of setts"},
            {"name": "Tillering",       "start_day": 31,  "end_day": 90,  "description": "Tiller formation"},
            {"name": "Grand Growth",    "start_day": 91,  "end_day": 270, "description": "Rapid elongation"},
            {"name": "Maturation",      "start_day": 271, "end_day": 330, "description": "Sugar accumulation"},
            {"name": "Ripening",        "start_day": 331, "end_day": 360, "description": "Final ripening before harvest"},
        ],
        "risk_parameters": {
            "max_stress_threshold": 0.55, "critical_risk_index": 0.65,
            "drought_sensitivity": 0.70,
            "pest_risk_stages": ["Tillering", "Grand Growth"],
        },
        "irrigation_windows": {
            "Germination":  {"frequency_days": 7,  "critical": True},
            "Tillering":    {"frequency_days": 10, "critical": True},
            "Grand Growth": {"frequency_days": 14, "critical": True},
            "Maturation":   {"frequency_days": 21, "critical": False},
        },
        "fertilizer_windows": {
            "Tillering":    {"urea_kg_per_acre": 40, "dap_kg_per_acre": 60},
            "Grand Growth": {"urea_kg_per_acre": 50, "dap_kg_per_acre": 0},
            "Maturation":   {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
        },
        "harvest_windows": {
            "optimal_moisture_pct": 14, "expected_yield_kg_per_acre": 30000,
            "harvest_start_day": 330,   "harvest_end_day": 365,
        },
        "drift_limits": {
            "max_stage_drift_days": 14, "warning_drift_days": 7, "auto_atrisk_drift_days": 21,
        },
    },
    {
        "crop_type": "maize",
        "variety": "DKC-7074",
        "region": "Madhya Pradesh",
        "version_id": "1.0",
        "effective_from_date": date(2025, 6, 15),
        "status": "active",
        "description": "Hybrid maize for Central India Kharif season.",
        "stage_definitions": [
            {"name": "Germination",     "start_day": 1,  "end_day": 7,  "description": "Seed germination"},
            {"name": "Seedling",        "start_day": 8,  "end_day": 20, "description": "Early growth"},
            {"name": "Vegetative",      "start_day": 21, "end_day": 45, "description": "Rapid vegetative growth"},
            {"name": "Tasseling",       "start_day": 46, "end_day": 60, "description": "Tassel development"},
            {"name": "Silking",         "start_day": 61, "end_day": 70, "description": "Silk emergence and pollination"},
            {"name": "Grain Fill",      "start_day": 71, "end_day": 95, "description": "Kernel development"},
            {"name": "Maturity",        "start_day": 96, "end_day": 110,"description": "Kernel black layer"},
        ],
        "risk_parameters": {
            "max_stress_threshold": 0.60, "critical_risk_index": 0.72,
            "drought_sensitivity": 0.75,
            "pest_risk_stages": ["Vegetative", "Tasseling", "Grain Fill"],
        },
        "irrigation_windows": {
            "Germination": {"frequency_days": 4,  "critical": True},
            "Vegetative":  {"frequency_days": 10, "critical": True},
            "Tasseling":   {"frequency_days": 7,  "critical": True},
            "Silking":     {"frequency_days": 5,  "critical": True},
            "Grain Fill":  {"frequency_days": 10, "critical": False},
        },
        "fertilizer_windows": {
            "Seedling":   {"urea_kg_per_acre": 30, "dap_kg_per_acre": 50},
            "Vegetative": {"urea_kg_per_acre": 40, "dap_kg_per_acre": 0},
            "Tasseling":  {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
        },
        "harvest_windows": {
            "optimal_moisture_pct": 15, "expected_yield_kg_per_acre": 2000,
            "harvest_start_day": 100,   "harvest_end_day": 115,
        },
        "drift_limits": {
            "max_stage_drift_days": 5, "warning_drift_days": 3, "auto_atrisk_drift_days": 8,
        },
    },
    {
        "crop_type": "mustard",
        "variety": "RH-749",
        "region": "Rajasthan",
        "version_id": "1.0",
        "effective_from_date": date(2025, 10, 15),
        "status": "active",
        "description": "Mustard (Rabi) for arid and semi-arid zones of Rajasthan.",
        "stage_definitions": [
            {"name": "Germination", "start_day": 1,  "end_day": 7,  "description": "Germination"},
            {"name": "Rosette",     "start_day": 8,  "end_day": 25, "description": "Leaf rosette stage"},
            {"name": "Bolting",     "start_day": 26, "end_day": 45, "description": "Stem elongation"},
            {"name": "Flowering",   "start_day": 46, "end_day": 65, "description": "Yellow flower bloom"},
            {"name": "Pod Fill",    "start_day": 66, "end_day": 90, "description": "Siliqua development"},
            {"name": "Maturity",    "start_day": 91, "end_day": 105,"description": "Ripening and harvest"},
        ],
        "risk_parameters": {
            "max_stress_threshold": 0.55, "critical_risk_index": 0.65,
            "drought_sensitivity": 0.45,
            "pest_risk_stages": ["Bolting", "Flowering", "Pod Fill"],
        },
        "irrigation_windows": {
            "Germination": {"frequency_days": 5, "critical": True},
            "Bolting":     {"frequency_days": 20, "critical": True},
            "Flowering":   {"frequency_days": 15, "critical": True},
            "Pod Fill":    {"frequency_days": 20, "critical": False},
        },
        "fertilizer_windows": {
            "Rosette":   {"urea_kg_per_acre": 20, "dap_kg_per_acre": 40},
            "Bolting":   {"urea_kg_per_acre": 20, "dap_kg_per_acre": 0},
            "Flowering": {"urea_kg_per_acre": 10, "dap_kg_per_acre": 0},
        },
        "harvest_windows": {
            "optimal_moisture_pct": 10, "expected_yield_kg_per_acre": 600,
            "harvest_start_day": 98,    "harvest_end_day": 110,
        },
        "drift_limits": {
            "max_stage_drift_days": 5, "warning_drift_days": 3, "auto_atrisk_drift_days": 7,
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# FARMER DATA — 20 realistic Indian farmers
# ─────────────────────────────────────────────────────────────────────────────

FARMERS = [
    # Punjab — 5 farmers
    {"full_name": "Rajveer Singh",      "phone": "+919876540101", "email": "rajveer.s@demo.in",    "region": "Punjab",         "lang": "pa"},
    {"full_name": "Gurinder Kaur",      "phone": "+919876540102", "email": "gurinder.k@demo.in",   "region": "Punjab",         "lang": "pa"},
    {"full_name": "Harpreet Dhaliwal",  "phone": "+919876540103", "email": "harpreet.d@demo.in",   "region": "Punjab",         "lang": "pa"},
    {"full_name": "Kuldeep Sandhu",     "phone": "+919876540104", "email": "kuldeep.sa@demo.in",   "region": "Punjab",         "lang": "pa"},
    {"full_name": "Mandeep Gill",       "phone": "+919876540105", "email": "mandeep.g@demo.in",    "region": "Punjab",         "lang": "pa"},
    # Haryana — 4 farmers
    {"full_name": "Rakesh Yadav",       "phone": "+919876540106", "email": "rakesh.y@demo.in",     "region": "Haryana",        "lang": "hi"},
    {"full_name": "Savita Devi",        "phone": "+919876540107", "email": "savita.d@demo.in",     "region": "Haryana",        "lang": "hi"},
    {"full_name": "Surender Kumar",     "phone": "+919876540108", "email": "surender.k@demo.in",   "region": "Haryana",        "lang": "hi"},
    {"full_name": "Pooja Rani",         "phone": "+919876540109", "email": "pooja.ra@demo.in",     "region": "Haryana",        "lang": "hi"},
    # Uttar Pradesh — 3 farmers
    {"full_name": "Ram Kishun Gupta",   "phone": "+919876540110", "email": "ramkishun.g@demo.in",  "region": "Uttar Pradesh",  "lang": "hi"},
    {"full_name": "Sushila Shukla",     "phone": "+919876540111", "email": "sushila.sh@demo.in",   "region": "Uttar Pradesh",  "lang": "hi"},
    {"full_name": "Munna Lal Tiwari",   "phone": "+919876540112", "email": "munnalal.t@demo.in",   "region": "Uttar Pradesh",  "lang": "hi"},
    # Madhya Pradesh — 2 farmers
    {"full_name": "Rajendra Patidar",   "phone": "+919876540113", "email": "rajendra.p@demo.in",   "region": "Madhya Pradesh", "lang": "hi"},
    {"full_name": "Geeta Bai Verma",    "phone": "+919876540114", "email": "geeta.v@demo.in",      "region": "Madhya Pradesh", "lang": "hi"},
    # Rajasthan — 2 farmers
    {"full_name": "Anand Bhati",        "phone": "+919876540115", "email": "anand.bh@demo.in",     "region": "Rajasthan",      "lang": "hi"},
    {"full_name": "Meera Kumari",       "phone": "+919876540116", "email": "meera.ku@demo.in",     "region": "Rajasthan",      "lang": "hi"},
    # Gujarat — 2 farmers
    {"full_name": "Mahesh Patel",       "phone": "+919876540117", "email": "mahesh.pa@demo.in",    "region": "Gujarat",        "lang": "gu"},
    {"full_name": "Bhavna Desai",       "phone": "+919876540118", "email": "bhavna.de@demo.in",    "region": "Gujarat",        "lang": "gu"},
    # Maharashtra — 2 farmers
    {"full_name": "Vitthal Jadhav",     "phone": "+919876540119", "email": "vitthal.j@demo.in",    "region": "Maharashtra",    "lang": "mr"},
    {"full_name": "Anjali Patil",       "phone": "+919876540120", "email": "anjali.pa@demo.in",    "region": "Maharashtra",    "lang": "mr"},
]


# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER DATA — 15 realistic Indian agri service providers
# ─────────────────────────────────────────────────────────────────────────────

PROVIDERS = [
    # Punjab — equipment rental
    {
        "user": {"full_name": "Gurpreet Singh Equipment",   "phone": "+919876540201", "email": "gurpreet.eq@demo.in",   "region": "Punjab"},
        "profile": {"business_name": "Gurpreet Equipment Rentals",  "service_type": "equipment_rental","region": "Punjab",        "sub_region": "Ludhiana","service_radius_km": 60, "crop_specializations": ["wheat", "rice"],           "trust_score": 0.88, "is_verified": True,  "description": "Premium tractor and combine harvester rentals for Punjab wheat and paddy farmers."},
    },
    {
        "user": {"full_name": "Amritsar Agri Rentals",      "phone": "+919876540202", "email": "amritsar.agri@demo.in", "region": "Punjab"},
        "profile": {"business_name": "Amritsar Farm Machine Hub",   "service_type": "equipment_rental","region": "Punjab",        "sub_region": "Amritsar","service_radius_km": 50, "crop_specializations": ["wheat","cotton"],           "trust_score": 0.82, "is_verified": True,  "description": "ISO-certified equipment rental with GPS-enabled tractors and scheduled maintenance."},
    },
    # Haryana — labor + advisory
    {
        "user": {"full_name": "Haryana Agri Services",      "phone": "+919876540203", "email": "haryana.agri@demo.in",  "region": "Haryana"},
        "profile": {"business_name": "Haryana Agri Services Ltd",   "service_type": "labor",            "region": "Haryana",       "sub_region": "Karnal", "service_radius_km": 80, "crop_specializations": ["rice","sugarcane","wheat"], "trust_score": 0.80, "is_verified": True,  "description": "1500+ skilled seasonal workers for transplanting, weeding, and harvesting operations."},
    },
    {
        "user": {"full_name": "Panipat Crop Advisors",      "phone": "+919876540204", "email": "panipat.adv@demo.in",   "region": "Haryana"},
        "profile": {"business_name": "Panipat Crop Advisory Center","service_type": "advisory",          "region": "Haryana",       "sub_region": "Panipat","service_radius_km": 100,"crop_specializations": ["wheat","rice","mustard"],   "trust_score": 0.76, "is_verified": True,  "description": "IIT-Ag graduate team offering soil health, pest scouting, and agronomic advisory."},
    },
    # Uttar Pradesh — sugarcane + labor
    {
        "user": {"full_name": "Meerut Cane Services",       "phone": "+919876540205", "email": "meerut.cane@demo.in",   "region": "Uttar Pradesh"},
        "profile": {"business_name": "Meerut Sugarcane Solutions",  "service_type": "labor",            "region": "Uttar Pradesh", "sub_region": "Meerut", "service_radius_km": 70, "crop_specializations": ["sugarcane","wheat"],        "trust_score": 0.74, "is_verified": True,  "description": "Specialised sugarcane harvesting crews with OFS-compatible payment systems."},
    },
    {
        "user": {"full_name": "Lucknow Agri Advisors",      "phone": "+919876540206", "email": "lucknow.adv@demo.in",   "region": "Uttar Pradesh"},
        "profile": {"business_name": "Lucknow Precision Agriculture","service_type": "advisory",         "region": "Uttar Pradesh", "sub_region": "Lucknow","service_radius_km": 120,"crop_specializations": ["rice","sugarcane","maize"], "trust_score": 0.71, "is_verified": False, "description": "Remote and on-field agronomic consultancy with drone-based crop monitoring."},
    },
    # Madhya Pradesh — pest control + soil testing
    {
        "user": {"full_name": "MP Pest Shield",             "phone": "+919876540207", "email": "mp.pest@demo.in",       "region": "Madhya Pradesh"},
        "profile": {"business_name": "MP Pest Control Services",    "service_type": "pest_control",     "region": "Madhya Pradesh","sub_region": "Bhopal", "service_radius_km": 90, "crop_specializations": ["maize","soybean","wheat"], "trust_score": 0.79, "is_verified": True,  "description": "Licensed pest management with integrated pest management (IPM) protocols across Central India."},
    },
    {
        "user": {"full_name": "Indore Soil Lab",            "phone": "+919876540208", "email": "indore.soil@demo.in",   "region": "Madhya Pradesh"},
        "profile": {"business_name": "Indore Soil Analysis Labs",   "service_type": "soil_testing",     "region": "Madhya Pradesh","sub_region": "Indore", "service_radius_km": 150,"crop_specializations": ["maize","cotton","soybean"], "trust_score": 0.85, "is_verified": True,  "description": "NABL-accredited soil and water testing lab with 48-hour report turnaround and fertilizer recommendations."},
    },
    # Rajasthan — equipment rental + advisory
    {
        "user": {"full_name": "Jaipur Farm Rentals",        "phone": "+919876540209", "email": "jaipur.farm@demo.in",   "region": "Rajasthan"},
        "profile": {"business_name": "Jaipur Agricultural Equipment","service_type": "equipment_rental","region": "Rajasthan",     "sub_region": "Jaipur", "service_radius_km": 110,"crop_specializations": ["mustard","wheat"],          "trust_score": 0.77, "is_verified": True,  "description": "Large fleet of drills, sprayers, and threshers for Rabi crops in the arid zones."},
    },
    {
        "user": {"full_name": "Desert Agri Advisory",       "phone": "+919876540210", "email": "desert.agri@demo.in",   "region": "Rajasthan"},
        "profile": {"business_name": "Desert Zone Crop Advisory",   "service_type": "advisory",         "region": "Rajasthan",     "sub_region": "Jodhpur","service_radius_km": 200,"crop_specializations": ["mustard","bajra","cumin"],  "trust_score": 0.69, "is_verified": False, "description": "Expert advisory for arid-zone drought-tolerant crops including precision irrigation scheduling."},
    },
    # Gujarat — cotton + pest control
    {
        "user": {"full_name": "Gujarat Farm Solutions",     "phone": "+919876540211", "email": "guj.farm@demo.in",      "region": "Gujarat"},
        "profile": {"business_name": "Gujarat Farm Solutions Pvt",  "service_type": "advisory",         "region": "Gujarat",       "sub_region": "Rajkot", "service_radius_km": 130,"crop_specializations": ["cotton","groundnut"],       "trust_score": 0.72, "is_verified": True,  "description": "End-to-end cotton crop management including variety selection, pest scouting, and output marketing linkages."},
    },
    {
        "user": {"full_name": "Ahmedabad Pest Control",     "phone": "+919876540212", "email": "ahmedabad.pest@demo.in","region": "Gujarat"},
        "profile": {"business_name": "Ahmedabad Crop Protect Co",   "service_type": "pest_control",     "region": "Gujarat",       "sub_region": "Ahmedabad","service_radius_km": 100,"crop_specializations": ["cotton","rice","groundnut"],"trust_score": 0.81, "is_verified": True,  "description": "Certified agrochem applicators using drone-assisted spray for large cotton and groundnut farms."},
    },
    # Maharashtra — labor + soil testing
    {
        "user": {"full_name": "Pune AgriLabour",            "phone": "+919876540213", "email": "pune.labour@demo.in",   "region": "Maharashtra"},
        "profile": {"business_name": "Pune AgriLabour Solutions",   "service_type": "labor",            "region": "Maharashtra",   "sub_region": "Pune",   "service_radius_km": 75, "crop_specializations": ["sugarcane","cotton","soybean"],"trust_score": 0.73, "is_verified": True, "description": "Reliable sugarcane and soybean harvesting labor with GPS attendance tracking and daily attendance reports."},
    },
    {
        "user": {"full_name": "Nashik Farm Testing",        "phone": "+919876540214", "email": "nashik.test@demo.in",   "region": "Maharashtra"},
        "profile": {"business_name": "Nashik Soil & Water Analytics","service_type": "soil_testing",    "region": "Maharashtra",   "sub_region": "Nashik", "service_radius_km": 120,"crop_specializations": ["grapes","onion","cotton"],  "trust_score": 0.87, "is_verified": True,  "description": "Advanced micro-nutrient and heavy metal testing for horticultural and cotton soils in Nashik district."},
    },
    # Cross-regional — equipment
    {
        "user": {"full_name": "AgriTech Equipment Hub",     "phone": "+919876540215", "email": "agritech.hub@demo.in",  "region": "Punjab"},
        "profile": {"business_name": "AgriTech National Equipment", "service_type": "equipment_rental","region": "Punjab",        "sub_region": "Chandigarh","service_radius_km": 300,"crop_specializations": ["wheat","rice","maize","cotton"],"trust_score": 0.91,"is_verified": True, "description": "Pan-India equipment rental with 400+ machines: combine harvesters, zero-till drills, rotavators. GST-compliant invoicing."},
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# CROP CONFIGS — 2 crops per farmer (40 total)
# Maps farmer index → list of crop specs
# ─────────────────────────────────────────────────────────────────────────────

def build_crop_configs():
    """Return a list of crop config dicts for all 20 farmers × 2 crops each."""
    configs = []

    crop_specs = [
        # --- Punjab farmers (0-4) ---
        # Farmer 0: Rajveer Singh — wheat (active, Tillering) + rice (harvested)
        ("farmer_0", "wheat",     "HD-2967",           TODAY - timedelta(days=50), "Active",    "Tillering",          50, 50, 0.18, 0.14, "Optimal", 6.0),
        ("farmer_0", "rice",      "Pusa Basmati 1121", TODAY - timedelta(days=155), "Harvested", "Maturity",           150, 148, 0.09, 0.07, "Optimal",8.5),

        # Farmer 1: Gurinder Kaur — wheat (delayed, Seedling) + cotton
        ("farmer_1", "wheat",     "PBW-343",           TODAY - timedelta(days=32), "Delayed",   "Seedling",           28, 32, 0.38, 0.30, "Late",   4.0),
        ("farmer_1", "cotton",    "Kaveri-189",        TODAY - timedelta(days=80), "Active",    "Squaring",           78, 80, 0.25, 0.20, "Optimal",5.0),

        # Farmer 2: Harpreet Dhaliwal — wheat (active, Jointing) + mustard (harvested)
        ("farmer_2", "wheat",     "HD-3086",           TODAY - timedelta(days=55), "Active",    "Jointing",           55, 55, 0.12, 0.10, "Optimal",7.5),
        ("farmer_2", "mustard",   "RH-749",            TODAY - timedelta(days=110),"Harvested", "Maturity",           105, 105, 0.06, 0.05, "Optimal", 3.0),

        # Farmer 3: Kuldeep Sandhu — wheat (AtRisk, Heading) + maize
        ("farmer_3", "wheat",     "WH-1105",           TODAY - timedelta(days=88), "AtRisk",    "Heading",            84, 88, 0.75, 0.70, "Optimal",9.0),
        ("farmer_3", "maize",     "DKC-7074",          TODAY - timedelta(days=40), "Active",    "Vegetative",         40, 40, 0.16, 0.12, "Optimal",4.5),

        # Farmer 4: Mandeep Gill — wheat (active, Grain Fill) + rice (active)
        ("farmer_4", "wheat",     "PBW-752",           TODAY - timedelta(days=98), "Active",    "Grain Fill",         98, 95, 0.22, 0.18, "Optimal",11.0),
        ("farmer_4", "rice",      "Punjab-11",         TODAY - timedelta(days=65), "Active",    "Tillering",          65, 62, 0.20, 0.16, "Optimal",6.5),

        # --- Haryana farmers (5-8) ---
        # Farmer 5: Rakesh Yadav — rice (panicle initiation) + wheat (seedling)
        ("farmer_5", "rice",      "Pusa Basmati 1509", TODAY - timedelta(days=68), "Active",    "Panicle Initiation", 68, 65, 0.21, 0.17, "Optimal",10.0),
        ("farmer_5", "wheat",     "HD-2967",           TODAY - timedelta(days=18), "Active",    "Seedling",           18, 18, 0.08, 0.06, "Optimal",5.0),

        # Farmer 6: Savita Devi — rice (booting, delayed) + mustard
        ("farmer_6", "rice",      "HKR-47",            TODAY - timedelta(days=92), "Delayed",   "Booting",            88, 92, 0.42, 0.35, "Late",   8.0),
        ("farmer_6", "mustard",   "Vardan",            TODAY - timedelta(days=50), "Active",    "Bolting",            50, 50, 0.14, 0.11, "Optimal",3.5),

        # Farmer 7: Surender Kumar — wheat (closed) + rice (active, tillering)
        ("farmer_7", "wheat",     "WH-711",            TODAY - timedelta(days=145),"Closed",    "Maturity",           140, 140, 0.07, 0.05, "Optimal",7.0),
        ("farmer_7", "rice",      "Pusa Basmati 1121", TODAY - timedelta(days=55), "Active",    "Tillering",          55, 52, 0.19, 0.15, "Optimal",6.0),

        # Farmer 8: Pooja Rani — wheat (active, Booting) + sugarcane
        ("farmer_8", "wheat",     "PBW-343",           TODAY - timedelta(days=72), "Active",    "Booting",            72, 70, 0.17, 0.13, "Optimal",4.5),
        ("farmer_8", "sugarcane", "Co-238",            TODAY - timedelta(days=120),"Active",    "Tillering",          120, 118, 0.23, 0.19, "Optimal",18.0),

        # --- Uttar Pradesh farmers (9–11) ---
        # Farmer 9: Ram Kishun Gupta — sugarcane (Grand Growth) + wheat (Closed)
        ("farmer_9",  "sugarcane","Co-0238",           TODAY - timedelta(days=200),"Active",    "Grand Growth",       200, 195, 0.25, 0.21, "Optimal",25.0),
        ("farmer_9",  "wheat",    "HD-2967",           TODAY - timedelta(days=135),"Closed",    "Maturity",           135, 133, 0.08, 0.06, "Optimal",8.0),

        # Farmer 10: Sushila Shukla — rice (heading) + maize (Grain Fill)
        ("farmer_10", "rice",     "NDR-80",            TODAY - timedelta(days=100),"Active",    "Heading",            100, 98, 0.24, 0.19, "Optimal",7.5),
        ("farmer_10", "maize",    "NMH-803",           TODAY - timedelta(days=88), "Active",    "Grain Fill",         88, 85, 0.18, 0.14, "Optimal",5.0),

        # Farmer 11: Munna Lal Tiwari — sugarcane (Maturation) + wheat (Harvested)
        ("farmer_11", "sugarcane","Co-238",            TODAY - timedelta(days=300),"Active",    "Maturation",         300, 298, 0.15, 0.12, "Optimal",30.0),
        ("farmer_11", "wheat",    "K-307",             TODAY - timedelta(days=132),"Harvested", "Maturity",           130, 128, 0.07, 0.05, "Optimal",9.5),

        # --- Madhya Pradesh farmers (12–13) ---
        # Farmer 12: Rajendra Patidar — maize (AtRisk, Tasseling) + wheat (Closed)
        ("farmer_12", "maize",    "HQPM-1",            TODAY - timedelta(days=52), "AtRisk",    "Tasseling",          50, 52, 0.77, 0.72, "Optimal",6.0),
        ("farmer_12", "wheat",    "Sujata",            TODAY - timedelta(days=130),"Closed",    "Maturity",           128, 126, 0.06, 0.05, "Late",   5.0),

        # Farmer 13: Geeta Bai Verma — maize (Vegetative) + cotton (Squaring)
        ("farmer_13", "maize",    "DKC-9120",          TODAY - timedelta(days=35), "Active",    "Vegetative",         35, 33, 0.13, 0.10, "Optimal",4.5),
        ("farmer_13", "cotton",   "RCH-2",             TODAY - timedelta(days=48), "Active",    "Squaring",           47, 48, 0.28, 0.22, "Optimal",7.0),

        # --- Rajasthan farmers (14–15) ---
        # Farmer 14: Anand Bhati — mustard (Heading, harvested) + wheat (Grain Fill)
        ("farmer_14", "mustard",  "RH-30",             TODAY - timedelta(days=100),"Harvested", "Maturity",           98, 96, 0.07, 0.05, "Optimal",3.0),
        ("farmer_14", "wheat",    "Raj-4120",          TODAY - timedelta(days=95), "Active",    "Grain Fill",         94, 95, 0.20, 0.16, "Optimal",7.5),

        # Farmer 15: Meera Kumari — mustard (Flowering) + wheat (Booting)
        ("farmer_15", "mustard",  "Pusa Mustard-25",  TODAY - timedelta(days=52), "Active",    "Flowering",          52, 50, 0.16, 0.13, "Optimal",2.5),
        ("farmer_15", "wheat",    "Raj-3765",          TODAY - timedelta(days=75), "Active",    "Booting",            75, 73, 0.18, 0.14, "Optimal",5.0),

        # --- Gujarat farmers (16–17) ---
        # Farmer 16: Mahesh Patel — cotton (Boll Dev, AtRisk) + groundnut
        ("farmer_16", "cotton",   "Arjun BG-II",       TODAY - timedelta(days=105),"AtRisk",    "Boll Development",   100, 105, 0.74, 0.69, "Optimal",12.0),
        ("farmer_16", "cotton",   "Durga Cotton",      TODAY - timedelta(days=62), "Active",    "Squaring",           60, 62, 0.26, 0.21, "Late",   8.0),

        # Farmer 17: Bhavna Desai — cotton (Flowering) + rice (Tillering)
        ("farmer_17", "cotton",   "Rasi-773",          TODAY - timedelta(days=75), "Active",    "Flowering",          74, 75, 0.30, 0.26, "Optimal",9.5),
        ("farmer_17", "rice",     "GR-11",             TODAY - timedelta(days=50), "Active",    "Tillering",          50, 48, 0.21, 0.17, "Optimal",5.0),

        # --- Maharashtra farmers (18–19) ---
        # Farmer 18: Vitthal Jadhav — sugarcane (Grand Growth) + cotton (Boll Opening)
        ("farmer_18", "sugarcane","Co-86032",          TODAY - timedelta(days=240),"Active",    "Grand Growth",       240, 238, 0.22, 0.18, "Optimal",35.0),
        ("farmer_18", "cotton",   "MRC-7351",          TODAY - timedelta(days=140),"Active",    "Boll Opening",       138, 140, 0.27, 0.22, "Optimal",10.0),

        # Farmer 19: Anjali Patil — sugarcane (Ripening) + wheat (Active, Seedling)
        ("farmer_19", "sugarcane","Co-238",            TODAY - timedelta(days=345),"Active",    "Ripening",           342, 345, 0.18, 0.15, "Optimal",40.0),
        ("farmer_19", "cotton",   "VCH-1/11",          TODAY - timedelta(days=58), "Active",    "Squaring",           57, 58, 0.24, 0.19, "Optimal",6.5),
    ]
    return crop_specs


# ─────────────────────────────────────────────────────────────────────────────
# Actions — 10 per crop
# ─────────────────────────────────────────────────────────────────────────────

ACTION_TYPES = {
    "wheat": [
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 55, "source": "tube_well"}),
        ("irrigation",    "Operational",   {"method": "sprinkler","water_mm": 40, "source": "canal"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 25, "stage": "Seedling"}),
        ("fertilizer",    "Stress-Affecting",{"product": "DAP",     "quantity_kg": 50, "stage": "Seedling", "N_kg": 9, "P2O5_kg": 23}),
        ("pesticide",     "Stress-Affecting",{"product": "Propiconazole", "dose_lit": 0.5, "target": "Yellow Rust"}),
        ("weeding",       "Operational",   {"method": "manual",   "area_acres": 2.0, "workers": 5}),
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 60, "source": "tube_well"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 20, "stage": "Heading"}),
        ("observation",   "Informational", {"notes": "Good canopy cover, no visible lodging", "score": 0.85}),
        ("pesticide",     "Stress-Affecting",{"product": "Chlorpyrifos","dose_lit": 0.8,"target": "Aphids"}),
    ],
    "rice": [
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 80, "source": "canal"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 20, "stage": "Transplanting"}),
        ("fertilizer",    "Stress-Affecting",{"product": "DAP",     "quantity_kg": 40, "stage": "Transplanting"}),
        ("pesticide",     "Stress-Affecting",{"product": "Carbofuran","dose_kg": 4, "target": "Stem Borer"}),
        ("irrigation",    "Operational",   {"method": "SRI",      "water_mm": 30, "source": "pump"}),
        ("weeding",       "Operational",   {"method": "chemical", "herbicide": "Butachlor", "dose_lit": 1.5}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 30, "stage": "Tillering"}),
        ("observation",   "Informational", {"notes": "15 tillers per plant, BLB sign on 3 plants", "score": 0.75}),
        ("pesticide",     "Stress-Affecting",{"product": "Monocrotophos","dose_lit": 0.5,"target": "BPH"}),
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 60, "source": "canal"}),
    ],
    "cotton": [
        ("irrigation",    "Operational",   {"method": "drip",     "water_lit_per_plant": 5, "source": "bore_well"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 20, "stage": "Seedling"}),
        ("pesticide",     "Stress-Affecting",{"product": "Imidacloprid","dose_ml": 5, "target": "Whitefly"}),
        ("irrigation",    "Operational",   {"method": "drip",     "water_lit_per_plant": 6, "source": "bore_well"}),
        ("weeding",       "Operational",   {"method": "inter-culture","area_acres": 4.0, "rounds": 2}),
        ("observation",   "Informational", {"notes": "2-3 squares per plant, good vigor", "score": 0.80}),
        ("pesticide",     "Stress-Affecting",{"product": "Spinosad",  "dose_ml": 10, "target": "Bollworm"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Potassium Nitrate","quantity_kg": 8,"stage": "Flowering"}),
        ("irrigation",    "Operational",   {"method": "drip",     "water_lit_per_plant": 7, "source": "bore_well"}),
        ("observation",   "Informational", {"notes": "Red-cotton bug spotted in row 12", "score": 0.60}),
    ],
    "sugarcane": [
        ("irrigation",    "Operational",   {"method": "furrow",   "water_mm": 100, "source": "canal"}),
        ("fertilizer",    "Stress-Affecting",{"product": "FYM",     "quantity_tonnes": 10, "stage": "Germination"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 40, "stage": "Tillering"}),
        ("pesticide",     "Stress-Affecting",{"product": "Chlorantraniliprole","dose_ml": 60,"target": "Top Shoot Borer"}),
        ("irrigation",    "Operational",   {"method": "furrow",   "water_mm": 80, "source": "canal"}),
        ("weeding",       "Operational",   {"method": "manual",   "area_acres": 5.0, "workers": 10}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 50, "stage": "Grand Growth"}),
        ("observation",   "Informational", {"notes": "Average cane height 150cm, good girth", "score": 0.85}),
        ("pesticide",     "Stress-Affecting",{"product": "Trichogramma","units": 50000,"target": "Borers (biocontrol)"}),
        ("irrigation",    "Operational",   {"method": "furrow",   "water_mm": 70, "source": "canal"}),
    ],
    "maize": [
        ("irrigation",    "Operational",   {"method": "sprinkler","water_mm": 45, "source": "bore_well"}),
        ("fertilizer",    "Stress-Affecting",{"product": "NPK 12-32-16","quantity_kg": 50,"stage": "Seedling"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 40, "stage": "Vegetative"}),
        ("pesticide",     "Stress-Affecting",{"product": "Lambda Cyhalothrin","dose_ml": 20,"target": "FAW"}),
        ("irrigation",    "Operational",   {"method": "sprinkler","water_mm": 50, "source": "bore_well"}),
        ("weeding",       "Operational",   {"method": "atrazine", "dose_kg": 1.0, "timing": "pre-emergence"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 20, "stage": "Tasseling"}),
        ("observation",   "Informational", {"notes": "Good silk emergence, no stunting observed", "score": 0.82}),
        ("pesticide",     "Stress-Affecting",{"product": "Emamectin Benzoate","dose_gm": 11,"target": "FAW"}),
        ("irrigation",    "Operational",   {"method": "sprinkler","water_mm": 40, "source": "bore_well"}),
    ],
    "mustard": [
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 50, "source": "tube_well"}),
        ("fertilizer",    "Stress-Affecting",{"product": "DAP",     "quantity_kg": 40, "stage": "Rosette"}),
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 45, "source": "tube_well"}),
        ("pesticide",     "Stress-Affecting",{"product": "Dimethoate","dose_ml": 300,"target": "Aphid"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Urea",    "quantity_kg": 20, "stage": "Bolting"}),
        ("observation",   "Informational", {"notes": "Uniform canopy, yellow flowers at 30% field", "score": 0.83}),
        ("pesticide",     "Stress-Affecting",{"product": "Fenvalerate","dose_ml": 200,"target": "Painted Bug"}),
        ("fertilizer",    "Stress-Affecting",{"product": "Sulphur (Bentonite)","quantity_kg": 10,"stage": "Pod Fill"}),
        ("irrigation",    "Operational",   {"method": "flood",    "water_mm": 40, "source": "tube_well"}),
        ("observation",   "Informational", {"notes": "Pods turning yellow — near harvest", "score": 0.90}),
    ],
}


def get_actions_for_crop(crop_type, sowing_date, n=10):
    """Return n action dicts with correct chronological effective_dates."""
    base = ACTION_TYPES.get(crop_type, ACTION_TYPES["wheat"])
    actions = (base * ((n // len(base)) + 1))[:n]
    results = []
    current_date = sowing_date + timedelta(days=3)
    for i, (atype, category, meta) in enumerate(actions):
        results.append({
            "action_type": atype,
            "category": category,
            "effective_date": current_date,
            "metadata_json": meta,
            "notes": f"{atype.title()} operation #{i+1} — {crop_type}",
            "source": random.choice(["web", "web", "web", "whatsapp", "offline"]),
            "applied_in_replay": "applied",
        })
        current_date += timedelta(days=random.randint(3, 10))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE REQUESTS — ~5 per provider
# ─────────────────────────────────────────────────────────────────────────────

SERVICE_REQUEST_SPECS = [
    # provider_idx, farmer_idx, service_type, crop_type, status, description, days_ago, price
    # Provider 0 (Gurpreet Equipment Rentals)
    (0,  0,  "equipment_rental", "wheat",    "Completed", "Tractor for wheat field preparation and sowing",      25, 3500.0),
    (0,  1,  "equipment_rental", "cotton",   "Completed", "Sprayer attachment for cotton pest control spray",    18, 1800.0),
    (0,  2,  "equipment_rental", "wheat",    "Accepted",  "Harvester combine rental for wheat crop",              5, 8000.0),
    (0,  3,  "equipment_rental", "wheat",    "InProgress","Rotavator for field preparation before wheat sowing",  2, 2200.0),
    (0,  4,  "equipment_rental", "rice",     "Pending",   "Paddy transplanter for 6 acres of nursery",           0, 5500.0),
    # Provider 1 (Amritsar Farm Machine Hub)
    (1,  1,  "equipment_rental", "wheat",    "Completed", "Zero-till drill for direct seeding of wheat",        30, 3000.0),
    (1,  4,  "equipment_rental", "rice",     "Completed", "Combine harvester for paddy — 6.5 acres",            20, 9000.0),
    (1,  3,  "equipment_rental", "maize",    "Accepted",  "GPS tractor for precision maize planting",            7, 4500.0),
    (1,  2,  "equipment_rental", "wheat",    "Pending",   "Multi-crop thresher for wheat harvest",               1, 2800.0),
    (1,  0,  "equipment_rental", "rice",     "Declined",  "Power weeder for paddy fields — request declined",   10, 1500.0),
    # Provider 2 (Haryana Agri Services)
    (2,  5,  "labor",           "rice",     "Completed", "5 workers for rice transplanting — 10 acres",        15, 6000.0),
    (2,  6,  "labor",           "rice",     "Completed", "8 workers for paddy harvesting assistance",          10, 7500.0),
    (2,  7,  "labor",           "wheat",    "Accepted",  "3 workers for wheat thinning and bundling",           4, 2700.0),
    (2,  8,  "labor",           "sugarcane","InProgress","12 workers for sugarcane planting ratoon",             2, 9500.0),
    (2,  9,  "labor",           "sugarcane","Pending",   "10 workers for sugarcane detrashing operation",        1, 8000.0),
    # Provider 3 (Panipat Crop Advisory)
    (3,  5,  "advisory",        "rice",     "Completed", "Soil health analysis and fertilizer schedule for rice",20, 1500.0),
    (3,  6,  "advisory",        "rice",     "Completed", "Pest scouting report — BLB management plan",          14, 1800.0),
    (3,  7,  "advisory",        "wheat",    "Accepted",  "Crop stand assessment and yield estimation",           6, 1200.0),
    (3,  8,  "advisory",        "sugarcane","Pending",   "Variety recommendation for new sugarcane plot",        1, 2000.0),
    (3, 10,  "advisory",        "rice",     "Completed", "Late blight management advisory for paddy Kharif",   25, 1600.0),
    # Provider 4 (Meerut Sugarcane Solutions)
    (4,  9,  "labor",           "sugarcane","Completed", "20 laborers for cane cutting and loading",           35, 15000.0),
    (4, 11,  "labor",           "sugarcane","Completed", "15 laborers for ratoon management and earthy mound", 22, 12000.0),
    (4, 18,  "labor",           "sugarcane","InProgress","18 laborers for main season harvesting operation",    3, 14000.0),
    (4, 19,  "labor",           "sugarcane","Accepted",  "12 laborers for detrashing and inter-cultivation",   5, 9500.0),
    (4,  8,  "labor",           "sugarcane","Pending",   "10 laborers for bud-chip planting in ratoon field",  0, 8000.0),
    # Provider 5 (Lucknow Precision Agriculture)
    (5, 10,  "advisory",        "rice",     "Completed", "Drone-based crop health mapping — 7.5 acres",        18, 3500.0),
    (5, 11,  "advisory",        "sugarcane","Completed", "Yield forecast model for coming season",              14, 2800.0),
    (5,  9,  "advisory",        "maize",    "Pending",   "Custom fertilizer schedule for drip-irrigated maize", 1, 1800.0),
    (5, 12,  "advisory",        "maize",    "Accepted",  "Disease management plan for maize — FAW alert",       4, 2200.0),
    (5, 13,  "advisory",        "maize",    "Completed", "Soil micronutrient report and correction plan",       20, 2500.0),
    # Provider 6 (MP Pest Shield)
    (6, 12,  "pest_control",    "maize",    "Completed", "Fall Armyworm chemical application — 6 acres",       12, 4200.0),
    (6, 13,  "pest_control",    "maize",    "Completed", "Spray for stem borer using drippers",                 8, 3800.0),
    (6, 14,  "pest_control",    "wheat",    "InProgress","Aphid management spray — pre-flowering wheat",         2, 2500.0),
    (6, 15,  "pest_control",    "wheat",    "Pending",   "Herbicide application for broad-leaf weeds in wheat",  1, 1800.0),
    (6, 16,  "pest_control",    "cotton",   "Accepted",  "Bollworm spray — 12 acres Bt Cotton",                3, 5200.0),
    # Provider 7 (Indore Soil Lab)
    (7, 12,  "soil_testing",    "maize",    "Completed", "Full soil analysis: pH, N, P, K, micronutrients",    20, 1200.0),
    (7, 13,  "soil_testing",    "cotton",   "Completed", "Heavy metal and micro-nutrient panel + report",      15, 1800.0),
    (7, 16,  "soil_testing",    "cotton",   "Accepted",  "Pre-season soil fertility test for cotton field",     3, 1200.0),
    (7, 17,  "soil_testing",    "rice",     "Pending",   "Soil salinity and water quality combined test",        1, 2200.0),
    (7, 18,  "soil_testing",    "sugarcane","Completed", "Brix and juice quality analysis for cane crop",      25, 1500.0),
    # Provider 8 (Jaipur Agricultural Equipment)
    (8, 14,  "equipment_rental","mustard",  "Completed", "Broadcast spreader for mustard field — 3 acres",    30, 1200.0),
    (8, 15,  "equipment_rental","wheat",    "Completed", "Seed drill for wheat sowing — 5 acres late sowing",  22, 1800.0),
    (8, 14,  "equipment_rental","wheat",    "InProgress","Harvesting thresher combo for Grain Fill stage",       2, 3500.0),
    (8, 15,  "equipment_rental","mustard",  "Accepted",  "Combine for mustard harvest — 2.5 acres",             4, 2200.0),
    (8, 16,  "equipment_rental","cotton",   "Pending",   "Cotton picker machine for Boll Opening stage",         1, 12000.0),
    # Provider 9 (Desert Zone Crop Advisory)
    (9, 14,  "advisory",        "mustard",  "Completed", "Irrigation scheduling for deficit irrigation mustard",18, 1000.0),
    (9, 15,  "advisory",        "mustard",  "Completed", "Pod fill optimization advisory — Rajasthan dry zone", 12, 1000.0),
    (9, 15,  "advisory",        "wheat",    "Pending",   "Winter stress management plan for late wheat",         0,  900.0),
    (9, 14,  "advisory",        "wheat",    "Accepted",  "Yield-gap analysis and targeted input recommendation", 3, 1500.0),
    (9, 16,  "advisory",        "cotton",   "Completed", "Pink bollworm scouting and trap based monitoring",    20, 1200.0),
    # Provider 10 (Gujarat Farm Solutions)
    (10, 16, "advisory",        "cotton",   "Completed", "Integrated crop management — variety to market",      28, 2500.0),
    (10, 17, "advisory",        "cotton",   "Completed", "Pest load assessment and spray calendar",             20, 2200.0),
    (10, 16, "advisory",        "cotton",   "InProgress","Pre-harvest advisory — moisture and timing",           2, 1800.0),
    (10, 17, "advisory",        "rice",     "Accepted",  "Bt cotton market linkage and procurement advisory",   4, 3000.0),
    (10, 18, "advisory",        "sugarcane","Pending",   "Cotton intercropping advisory for sugarcane belts",    0, 1500.0),
    # Provider 11 (Ahmedabad Crop Protect)
    (11, 16, "pest_control",    "cotton",   "Completed", "Drone spray — thrips and jassid control cotton A",   15, 6000.0),
    (11, 17, "pest_control",    "cotton",   "Completed", "Chemical spray for whitefly management — 9.5 acres", 10, 5400.0),
    (11, 17, "pest_control",    "rice",     "Accepted",  "BPH management drone spray for paddy field",          4, 4200.0),
    (11, 18, "pest_control",    "cotton",   "Pending",   "Boll weevil preventive spray at pod stage",           0, 5800.0),
    (11, 16, "pest_control",    "cotton",   "InProgress","Second round bollworm spray — cotton B field",         2, 5200.0),
    # Provider 12 (Pune AgriLabour)
    (12, 18, "labor",           "sugarcane","Completed", "30 harvesters for main sugarcane cutting — 35 acres",30, 22000.0),
    (12, 19, "labor",           "sugarcane","Completed", "25 workers for cane trash mulching",                 22, 18000.0),
    (12, 18, "labor",           "cotton",   "InProgress","15 cotton pickers for Boll Opening stage",             2, 11000.0),
    (12, 19, "labor",           "cotton",   "Accepted",  "10 cotton pickers — VCH-1/11 variety manual harvest",  4, 8000.0),
    (12, 17, "labor",           "rice",     "Pending",   "8 workers for rice harvest and threshing",             0, 6000.0),
    # Provider 13 (Nashik Soil & Water Analytics)
    (13, 17, "soil_testing",    "rice",     "Completed", "Soil NPK + pH test with fertilizer advisory",        25, 1500.0),
    (13, 18, "soil_testing",    "sugarcane","Completed", "Juice quality and Brix-Pol test for FRP calculation", 20, 2000.0),
    (13, 19, "soil_testing",    "cotton",   "Accepted",  "Pre-season soil fertility mapping — 6.5 acre plot",   3, 1800.0),
    (13, 18, "soil_testing",    "cotton",   "Completed", "Nematode density test for cotton replanting field",   18, 2200.0),
    (13, 17, "soil_testing",    "cotton",   "Pending",   "Heavy metal contamination screening — drip field",    0, 2800.0),
    # Provider 14 (AgriTech National Equipment)
    (14,  0, "equipment_rental","wheat",    "Completed", "Combine harvester for premium wheat — 6 acres",      40, 12000.0),
    (14,  5, "equipment_rental","rice",     "Completed", "Paddy harvester for 10-acre Basmati paddy",          30, 14000.0),
    (14,  9, "equipment_rental","sugarcane","Accepted",  "Chain-cutter harvester for 25-acre cane block",      6, 25000.0),
    (14, 12, "equipment_rental","maize",    "InProgress","Multi-row maize harvester for 6 acres",               2, 10000.0),
    (14, 18, "equipment_rental","sugarcane","Completed", "Cane harvester + transporter combo — 35 acres",      35, 30000.0),
]


# ─────────────────────────────────────────────────────────────────────────────
# Seed functions
# ─────────────────────────────────────────────────────────────────────────────

def seed_admin(db: Session) -> User:
    admin = db.query(User).filter(User.email == "admin@cultivax.in").first()
    if admin:
        return admin

    admin = User(
        id=uuid4(),
        full_name="Arpit Kumar (Admin)",
        phone="+919999000001",
        email="admin@cultivax.in",
        password_hash=PASSWORD_HASH,
        role="admin",
        region="National",
        is_active=True,
        is_onboarded=True,
        preferred_language="en",
    )
    db.add(admin)
    db.flush()
    print(f"  ✓ Admin created: {admin.full_name}")
    return admin


def seed_farmers(db: Session) -> list:
    farmer_users = []
    for i, fd in enumerate(FARMERS):
        u = User(
            id=uuid4(),
            full_name=fd["full_name"],
            phone=fd["phone"],
            email=fd["email"],
            password_hash=PASSWORD_HASH,
            role="farmer",
            region=fd["region"],
            preferred_language=fd.get("lang", "en"),
            is_active=True,
            is_onboarded=(i != 0),  # First farmer left un-onboarded for onboarding flow test
        )
        db.add(u)
        farmer_users.append(u)
    db.flush()
    print(f"  ✓ {len(farmer_users)} farmers created")
    return farmer_users


def seed_providers(db: Session) -> tuple:
    """Return (provider_users, service_providers)."""
    provider_users = []
    service_providers = []
    for p in PROVIDERS:
        ud = p["user"]
        u = User(
            id=uuid4(),
            full_name=ud["full_name"],
            phone=ud["phone"],
            email=ud["email"],
            password_hash=PASSWORD_HASH,
            role="provider",
            region=ud["region"],
            is_active=True,
            is_onboarded=True,
            preferred_language="en",
        )
        db.add(u)
        provider_users.append(u)

    db.flush()

    for i, (u, p) in enumerate(zip(provider_users, PROVIDERS)):
        pd = p["profile"]
        sp = ServiceProvider(
            id=uuid4(),
            user_id=u.id,
            business_name=pd["business_name"],
            service_type=pd["service_type"],
            region=pd["region"],
            sub_region=pd.get("sub_region"),
            service_radius_km=pd.get("service_radius_km", 50),
            crop_specializations=pd["crop_specializations"],
            trust_score=pd["trust_score"],
            is_verified=pd["is_verified"],
            description=pd["description"],
            contact_name=u.full_name,
            contact_phone=u.phone,
        )
        db.add(sp)
        service_providers.append(sp)

    db.flush()
    print(f"  ✓ {len(provider_users)} providers created (users + profiles)")
    return provider_users, service_providers


def seed_templates(db: Session) -> list:
    tpls = []
    for t in TEMPLATES:
        tpl = CropRuleTemplate(id=uuid4(), **t)
        db.add(tpl)
        tpls.append(tpl)
    db.flush()
    print(f"  ✓ {len(tpls)} crop rule templates created")
    return tpls


def seed_crops_and_actions(db: Session, farmer_users: list, templates: list) -> list:
    template_map = {t.crop_type: t for t in templates}
    crop_specs = build_crop_configs()
    crops = []

    for spec in crop_specs:
        (
            farmer_key, crop_type, variety, sowing_date, state, stage,
            current_day, baseline_day, stress, risk, window, land_area,
        ) = spec

        farmer_idx = int(farmer_key.split("_")[1])
        farmer = farmer_users[farmer_idx]
        template = template_map.get(crop_type)

        crop = CropInstance(
            id=uuid4(),
            farmer_id=farmer.id,
            crop_type=crop_type,
            variety=variety,
            sowing_date=sowing_date,
            state=state,
            stage=stage,
            current_day_number=current_day,
            baseline_day_number=baseline_day,
            stress_score=stress,
            risk_index=risk,
            seasonal_window_category=window,
            land_area=land_area,
            region=farmer.region,
            rule_template_id=template.id if template else None,
            stage_offset_days=abs(current_day - baseline_day),
            max_allowed_drift=template.drift_limits.get("max_stage_drift_days", 7) if template and template.drift_limits else 7,
        )
        db.add(crop)
        crops.append(crop)

    db.flush()

    # Add actions for each crop
    total_actions = 0
    for crop, spec in zip(crops, crop_specs):
        crop_type = spec[1]
        sowing_date = spec[3]
        state = spec[4]
        farmer_idx = int(spec[0].split("_")[1])
        farmer = farmer_users[farmer_idx]

        n_actions = 10
        actions_data = get_actions_for_crop(crop_type, sowing_date, n_actions)

        for adata in actions_data:
            al = ActionLog(
                id=uuid4(),
                crop_instance_id=crop.id,
                action_type=adata["action_type"],
                category=adata["category"],
                effective_date=adata["effective_date"],
                metadata_json=adata["metadata_json"],
                notes=adata["notes"],
                source=adata["source"],
                applied_in_replay=adata["applied_in_replay"],
                action_impact_type=adata["category"],
            )
            db.add(al)
            total_actions += 1

        # Add yield record for harvested / closed crops
        if state in ("Harvested", "Closed"):
            yield_map = {
                "wheat": 1750.0, "rice": 2150.0, "cotton": 780.0,
                "sugarcane": 28000.0, "maize": 1850.0, "mustard": 580.0,
            }
            yr = YieldRecord(
                id=uuid4(),
                crop_instance_id=crop.id,
                reported_yield=yield_map.get(crop_type, 1500.0) + random.uniform(-100, 200),
                yield_unit="kg/acre",
                harvest_date=sowing_date + timedelta(days=spec[6] + 5),
                bio_cap_applied=False,
            )
            db.add(yr)

    db.flush()
    print(f"  ✓ {len(crops)} crops created")
    print(f"  ✓ {total_actions} actions logged")
    return crops


def seed_service_requests_and_reviews(
    db: Session,
    farmer_users: list,
    service_providers: list,
) -> list:
    now = datetime.now(timezone.utc)
    requests = []

    for spec in SERVICE_REQUEST_SPECS:
        prov_idx, farmer_idx, svc_type, crop_type, status, desc, days_ago, price = spec

        if farmer_idx >= len(farmer_users) or prov_idx >= len(service_providers):
            continue

        farmer = farmer_users[farmer_idx]
        provider = service_providers[prov_idx]
        created = now - timedelta(days=days_ago)

        sr = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type=svc_type,
            status=status,
            description=desc,
            preferred_date=created,
            agreed_price=price,
            region=farmer.region,
            metadata_json={"crop_type": crop_type},  # store crop_type in metadata
        )

        if status in ("Accepted", "InProgress", "Completed", "Declined"):
            sr.provider_acknowledged_at = created + timedelta(hours=random.randint(2, 24))
        if status == "Completed":
            sr.completed_at = created + timedelta(days=random.randint(1, 4))
            sr.final_price = price

        db.add(sr)
        requests.append((sr, farmer, provider, status, price))

    db.flush()

    # Add reviews for completed requests
    reviews = 0
    for sr, farmer, provider, status, price in requests:
        if status == "Completed":
            rating = round(random.uniform(3.5, 5.0), 1)
            comments = [
                "Very professional service, completed work on time.",
                "Good quality work, would recommend to other farmers.",
                "Satisfied with the service, timely and effective.",
                "Excellent work, the team was skilled and efficient.",
                "Service was good. Minor delay but overall happy.",
                "Value for money. Will hire again next season.",
                "The worker team was disciplined and hard-working.",
            ]
            review = ServiceReview(
                id=uuid4(),
                request_id=sr.id,
                reviewer_id=farmer.id,
                provider_id=provider.id,
                rating=rating,
                comment=random.choice(comments),
            )
            db.add(review)
            reviews += 1

    db.flush()
    print(f"  ✓ {len(requests)} service requests created")
    print(f"  ✓ {reviews} service reviews created")
    return requests


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

def run_seed(force: bool = False):
    print("\n🌾 CultivaX — Full Demo Data Seed Script")
    print("=" * 55)

    db = SessionLocal()

    try:
        existing = db.query(User).count()
        if existing > 0:
            if not force:
                print(f"\n⚠️  Database already has {existing} users. Skipping demo seed.")
                print("   (Run with --force to seed additional data anyway)")
                return
            else:
                print(f"\n⚠️  {existing} existing users found — forcing re-seed (--force).")

        print("\n📦 Step 1: Admin")
        admin = seed_admin(db)

        print("\n📦 Step 2: Farmers")
        farmer_users = seed_farmers(db)

        print("\n📦 Step 3: Service Providers")
        provider_users, service_providers = seed_providers(db)

        print("\n📦 Step 4: Crop Rule Templates")
        templates = seed_templates(db)

        print("\n📦 Step 5: Crops & Actions")
        crops = seed_crops_and_actions(db, farmer_users, templates)

        print("\n📦 Step 6: Service Requests & Reviews")
        requests = seed_service_requests_and_reviews(db, farmer_users, service_providers)

        db.commit()

        print("\n✅ All demo data committed!")
        print("\n📋 Summary:")
        total_requests = len(requests)
        completed_req = sum(1 for r in requests if r[3] == "Completed")
        print(f"   Admin:              1")
        print(f"   Farmers:            {len(farmer_users)}")
        print(f"   Providers:          {len(provider_users)}")
        print(f"   Crop Templates:     {len(templates)} (wheat, rice, cotton, sugarcane, maize, mustard)")
        print(f"   Crop Instances:     {len(crops)} (~2 per farmer)")
        print(f"   Actions:            {len(crops) * 10} (~10 per crop)")
        print(f"   Service Requests:   {total_requests}")
        print(f"   Reviews:            {completed_req} (all completed requests)")

        print("\n🔑 Login Credentials (ALL users — password: Demo@12345)")
        print("   Admin:    +919999000001")
        print("   Farmers:  +919876540101 to +919876540120")
        print("   Providers:+919876540201 to +919876540215")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    run_seed(force=force)
