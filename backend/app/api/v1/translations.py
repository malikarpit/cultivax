"""
Translations API — Serves i18n translation dictionaries

GET /api/v1/translations/supported  — List supported locales
GET /api/v1/translations/{locale}   — Get translations for a locale

Frontend primarily uses bundled JSON for speed, but this endpoint
provides server-side translations for dynamic content
(alert messages, recommendations, etc.).
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/translations", tags=["Translations"])

SUPPORTED_LOCALES = {
    "en": "English",
    "hi": "हिंदी (Hindi)",
}

# Server-side translation strings for dynamic backend-generated content.
# These complement the frontend's static JSON translation files.
TRANSLATIONS = {
    "en": {
        "alerts": {
            "stress_high": "High stress detected on your {crop_type} crop",
            "risk_elevated": "Risk level elevated for {crop_type} in {region}",
            "weather_warning": "Weather warning: {description}",
            "action_overdue": "Action overdue: {action_type} for {crop_type}",
            "service_accepted": "Your service request has been accepted by {provider}",
            "service_completed": "Service completed by {provider}. Please leave a review.",
            "harvest_ready": "Your {crop_type} crop is ready for harvest!",
        },
        "recommendations": {
            "irrigate": "Consider irrigating your {crop_type}. Soil moisture is low.",
            "fertilize": "Time to apply fertilizer for optimal {stage} growth.",
            "inspect": "Inspect your crop for signs of pest activity.",
            "harvest": "Optimal harvest window approaching for {crop_type}.",
        },
        "states": {
            "Created": "Created",
            "Active": "Active",
            "Delayed": "Delayed",
            "AtRisk": "At Risk",
            "ReadyToHarvest": "Ready to Harvest",
            "Harvested": "Harvested",
            "Closed": "Closed",
        },
        "stages": {
            "germination": "Germination",
            "vegetative": "Vegetative",
            "flowering": "Flowering",
            "grain_filling": "Grain Filling",
            "maturity": "Maturity",
        },
        "roles": {
            "farmer": "Farmer",
            "provider": "Service Provider",
            "admin": "Administrator",
        },
    },
    "hi": {
        "alerts": {
            "stress_high": "आपकी {crop_type} फसल पर उच्च तनाव का पता चला",
            "risk_elevated": "{region} में {crop_type} के लिए जोखिम स्तर बढ़ा",
            "weather_warning": "मौसम चेतावनी: {description}",
            "action_overdue": "कार्रवाई बकाया: {crop_type} के लिए {action_type}",
            "service_accepted": "आपका सेवा अनुरोध {provider} द्वारा स्वीकार किया गया",
            "service_completed": "{provider} द्वारा सेवा पूर्ण। कृपया समीक्षा दें।",
            "harvest_ready": "आपकी {crop_type} फसल कटाई के लिए तैयार है!",
        },
        "recommendations": {
            "irrigate": "अपनी {crop_type} की सिंचाई करें। मिट्टी की नमी कम है।",
            "fertilize": "इष्टतम {stage} विकास के लिए उर्वरक लगाने का समय।",
            "inspect": "कीट गतिविधि के संकेतों के लिए फसल की जांच करें।",
            "harvest": "{crop_type} के लिए इष्टतम कटाई का समय आ रहा है।",
        },
        "states": {
            "Created": "बनाया गया",
            "Active": "सक्रिय",
            "Delayed": "देरी",
            "AtRisk": "जोखिम में",
            "ReadyToHarvest": "कटाई के लिए तैयार",
            "Harvested": "कटाई पूर्ण",
            "Closed": "बंद",
        },
        "stages": {
            "germination": "अंकुरण",
            "vegetative": "वनस्पति",
            "flowering": "फूल आना",
            "grain_filling": "दाना भरना",
            "maturity": "परिपक्वता",
        },
        "roles": {
            "farmer": "किसान",
            "provider": "सेवा प्रदाता",
            "admin": "प्रशासक",
        },
    },
}


@router.get("/supported")
async def list_supported_locales():
    """List all supported locales."""
    return {
        "locales": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LOCALES.items()
        ],
        "default": "en",
    }


@router.get("/{locale}")
async def get_translations(locale: str):
    """Get translation strings for a specific locale."""
    if locale not in TRANSLATIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Locale '{locale}' not supported. "
            f"Available: {list(SUPPORTED_LOCALES.keys())}",
        )
    return {
        "locale": locale,
        "locale_name": SUPPORTED_LOCALES[locale],
        "strings": TRANSLATIONS[locale],
    }
