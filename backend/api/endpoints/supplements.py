"""
Supplement Tracking and Information Endpoints
"""
from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

router = APIRouter()


# Schemas
class SupplementInfo(BaseModel):
    id: str
    name: str
    common_names: List[str]
    category: str  # herb, vitamin, mineral, etc.
    benefits: List[str]
    dosage_range: str
    contraindications: List[str]
    interactions: List[str]
    evidence_level: str  # strong, moderate, limited
    sources: List[str]
    ayurvedic_properties: Optional[dict] = None


class SupplementLog(BaseModel):
    id: str
    user_id: str
    supplement_id: str
    supplement_name: str
    dosage: str
    frequency: str  # daily, twice_daily, etc.
    start_date: date
    end_date: Optional[date] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None


class SupplementLogCreate(BaseModel):
    supplement_name: str
    dosage: str
    frequency: str
    start_date: date
    purpose: Optional[str] = None
    notes: Optional[str] = None


@router.get("/database/search")
async def search_supplements(
    query: str,
    category: Optional[str] = None,
    limit: int = 20
):
    """
    Search supplement database
    """
    # TODO: Implement knowledge base search
    return [
        SupplementInfo(
            id="supp_1",
            name="Ashwagandha",
            common_names=["Indian Ginseng", "Withania somnifera"],
            category="herb",
            benefits=[
                "Reduces stress and anxiety",
                "Improves sleep quality",
                "Supports cognitive function",
                "Balances cortisol levels"
            ],
            dosage_range="300-600mg daily",
            contraindications=[
                "Pregnancy and breastfeeding",
                "Autoimmune conditions (may stimulate immune system)"
            ],
            interactions=[
                "May enhance effects of sedatives",
                "May lower blood pressure"
            ],
            evidence_level="strong",
            sources=[
                "PubMed: 23439798 - RCT showing cortisol reduction",
                "PubMed: 24497737 - Meta-analysis on anxiety"
            ],
            ayurvedic_properties={
                "rasa": "bitter, astringent",
                "virya": "heating",
                "dosha_effect": "Balances Vata and Kapha"
            }
        )
    ]


@router.post("/log", response_model=SupplementLog)
async def log_supplement(
    log: SupplementLogCreate,
    user_id: str = "demo_user"
):
    """
    Log a supplement that user is taking
    """
    # TODO: Implement database storage and check for interactions
    return SupplementLog(
        id="temp_id",
        user_id=user_id,
        supplement_id="supp_1",
        **log.dict()
    )


@router.get("/log", response_model=List[SupplementLog])
async def get_supplement_logs(
    user_id: str = "demo_user",
    active_only: bool = True
):
    """
    Get user's supplement logs
    """
    # TODO: Implement database query
    return []


@router.get("/interactions")
async def check_interactions(
    user_id: str = "demo_user"
):
    """
    Check for potential interactions between user's supplements and medications
    """
    # TODO: Implement interaction checking logic
    return {
        "interactions_found": 0,
        "warnings": [],
        "recommendations": [
            "Always consult healthcare provider before starting new supplements"
        ]
    }


@router.get("/recommendations")
async def get_supplement_recommendations(
    user_id: str = "demo_user"
):
    """
    Get personalized supplement recommendations based on user's health data
    """
    # TODO: Implement recommendation engine
    return [
        {
            "supplement": "Magnesium",
            "reason": "Your sleep quality is suboptimal and diet logs show low magnesium intake",
            "evidence": ["Study: Magnesium improves sleep (PubMed: 23853635)"],
            "priority": "high"
        }
    ]
