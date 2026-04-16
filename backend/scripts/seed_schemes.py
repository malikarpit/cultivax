import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.official_scheme import OfficialScheme

SCHEMES = [
    {
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "description": "Financial benefit of Rs. 6000 per year in three equal installments to all landholding farmer families.",
        "portal_url": "https://pmkisan.gov.in/",
        "category": "subsidy",
        "region": "All",
        "crop_type": None,
        "tags": ["financial aid", "income support", "direct transfer"]
    },
    {
        "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
        "description": "Comprehensive crop insurance scheme against non-preventable natural risks from pre-sowing to post-harvest stage.",
        "portal_url": "https://pmfby.gov.in/",
        "category": "insurance",
        "region": "All",
        "crop_type": None,
        "tags": ["insurance", "risk cover", "crop loss"]
    },
    {
        "name": "Kisan Credit Card (KCC)",
        "description": "Adequate and timely credit from banking system to farmers for their short-term credit needs during cultivation.",
        "portal_url": "https://sbi.co.in/web/agri-rural/agriculture-banking/crop-loan/kisan-credit-card",
        "category": "loan",
        "region": "All",
        "crop_type": None,
        "tags": ["credit", "loan", "working capital"]
    },
    {
        "name": "Soil Health Card Scheme (SHC)",
        "description": "Provides farmers with soil nutrient status and recommendations on appropriate dosage of nutrients.",
        "portal_url": "https://soilhealth.dac.gov.in/",
        "category": "advisory",
        "region": "All",
        "crop_type": None,
        "tags": ["soil testing", "nutrients", "fertilizer"]
    },
    {
        "name": "PMKSY (Pradhan Mantri Krishi Sinchayee Yojana)",
        "description": "Focuses on enhancing water use efficiency at farm level through Micro Irrigation (Drip and Sprinkler).",
        "portal_url": "https://pmksy.gov.in/",
        "category": "subsidy",
        "region": "All",
        "crop_type": None,
        "tags": ["irrigation", "water conservation", "drip"]
    },
    {
        "name": "PKVY (Paramparagat Krishi Vikas Yojana)",
        "description": "Aims to promote organic farming and reduce reliance on chemical fertilizers and pesticides.",
        "portal_url": "https://pgsindia-ncof.gov.in/pkvy/",
        "category": "subsidy",
        "region": "All",
        "crop_type": None,
        "tags": ["organic", "pesticides free", "traditional farming"]
    },
    {
        "name": "e-NAM (National Agriculture Market)",
        "description": "Pan-India electronic trading portal linking APMCs to create a unified national market for agricultural commodities.",
        "portal_url": "https://enam.gov.in/",
        "category": "other",
        "region": "All",
        "crop_type": None,
        "tags": ["trading", "market", "apmc"]
    },
    {
        "name": "SMAM (Sub-Mission on Agricultural Mechanization)",
        "description": "Financial assistance to farmers for procurement of agricultural machinery and equipment.",
        "portal_url": "https://agrimachinery.nic.in/",
        "category": "subsidy",
        "region": "All",
        "crop_type": None,
        "tags": ["machinery", "equipment", "tractor"]
    },
    {
        "name": "Agriculture Infrastructure Fund (AIF)",
        "description": "Medium-long term debt financing facility for investment in viable projects for post-harvest management infrastructure.",
        "portal_url": "https://agriinfra.dac.gov.in/",
        "category": "loan",
        "region": "All",
        "crop_type": None,
        "tags": ["infrastructure", "post-harvest", "storage"]
    },
    {
        "name": "MIDH (Mission for Integrated Development of Horticulture)",
        "description": "Holistic growth of the horticulture sector encompassing fruits, vegetables, root & tuber crops, mushrooms, spices, etc.",
        "portal_url": "https://midh.gov.in/",
        "category": "subsidy",
        "region": "All",
        "crop_type": "Horticulture",
        "tags": ["fruits", "vegetables", "spices"]
    },
    {
        "name": "RKVY-RAFTAAR",
        "description": "Remunerative Approaches for Agriculture and Allied Sector Rejuvenation to ensure objective regional development.",
        "portal_url": "https://rkvy.nic.in/",
        "category": "subsidy",
        "region": "All",
        "crop_type": None,
        "tags": ["infrastructure", "allied sector", "state funding"]
    },
    {
        "name": "NABARD Dairy Entrepreneurship Development",
        "description": "Generates self-employment and infrastructure for the dairy sector including milk processing.",
        "portal_url": "https://www.nabard.org/",
        "category": "loan",
        "region": "All",
        "crop_type": "Dairy",
        "tags": ["dairy", "livestock", "milk"]
    },
    {
        "name": "MahaDBT Farmer Schemes",
        "description": "Centralized portal for farmers in Maharashtra to access state subsidies and agriculture inputs.",
        "portal_url": "https://mahadbt.maharashtra.gov.in/",
        "category": "subsidy",
        "region": "Maharashtra",
        "crop_type": None,
        "tags": ["state scheme", "inputs", "maharashtra"]
    },
    {
        "name": "Bhavantar Bhugtan Yojana",
        "description": "Price deficiency payment scheme implemented in Madhya Pradesh to protect farmers against price crashes.",
        "portal_url": "http://mpeuparjan.nic.in/",
        "category": "insurance",
        "region": "MP",
        "crop_type": None,
        "tags": ["price protection", "mandi", "mp"]
    },
    {
        "name": "Rythu Bandhu Scheme",
        "description": "Agriculture Investment Support Scheme by Telangana Govt for initial investment needs of farmers.",
        "portal_url": "https://rythubandhu.telangana.gov.in/",
        "category": "subsidy",
        "region": "All", # generalized
        "crop_type": None,
        "tags": ["investment support", "telangana", "cash transfer"]
    }
]

def run_seed():
    db = SessionLocal()
    try:
        existing = db.query(OfficialScheme).count()
        if existing > 0:
            print(f"Skipping: {existing} schemes already present in database.")
            return

        for s in SCHEMES:
            scheme = OfficialScheme(
                name=s["name"],
                description=s["description"],
                portal_url=s["portal_url"],
                category=s["category"],
                region=s["region"],
                crop_type=s["crop_type"],
                tags=s["tags"],
                is_active=True
            )
            db.add(scheme)
        
        db.commit()
        print(f"Successfully seeded {len(SCHEMES)} government schemes.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding schemes: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
