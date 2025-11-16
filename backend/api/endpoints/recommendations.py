"""
Personalized Recommendations Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
import uuid

from backend.database.postgres import get_db
from backend.services.recommendation_engine import get_recommendation_engine

router = APIRouter()


class RecommendationCategory(str, Enum):
    DIET = "diet"
    SUPPLEMENT = "supplement"
    LIFESTYLE = "lifestyle"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    STRESS = "stress"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Schemas
class Recommendation(BaseModel):
    id: str
    user_id: str
    category: RecommendationCategory
    title: str
    description: str
    reasoning: str
    evidence: List[str]  # Citations and sources
    priority: Priority
    created_at: datetime
    completed: bool = False


class RecommendationRequest(BaseModel):
    symptoms: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    category: Optional[RecommendationCategory] = None


@router.post("/", response_model=List[Recommendation])
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"
):
    """
    Get personalized recommendations based on user's current state and goals

    The system analyzes:
    - Recent health metrics and trends
    - EEG/voice/diet data
    - User's health goals and preferences
    - Ayurvedic dosha type
    - Medical conditions and contraindications
    """
    # Get recommendation engine
    engine = get_recommendation_engine()

    # Generate recommendations using our intelligent engine
    raw_recommendations = await engine.generate_recommendations(db, user_id)

    # Convert to API response format
    recommendations = []
    for rec in raw_recommendations:
        recommendations.append(
            Recommendation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                category=RecommendationCategory(rec['category']),
                title=rec['title'],
                description=rec['description'],
                reasoning=rec['reasoning'],
                evidence=rec.get('evidence', []),
                priority=rec['priority'],
                created_at=datetime.now(),
                completed=False
            )
        )

    # Filter by category if specified
    if request.category:
        recommendations = [
            r for r in recommendations
            if r.category == request.category
        ]

    return recommendations


@router.get("/history", response_model=List[Recommendation])
async def get_recommendation_history(
    user_id: str = "demo_user",
    category: Optional[RecommendationCategory] = None,
    limit: int = 50
):
    """
    Get historical recommendations
    """
    # TODO: Implement database query
    return []


@router.patch("/{recommendation_id}/complete")
async def mark_recommendation_complete(
    recommendation_id: str,
    completed: bool,
    user_id: str = "demo_user"
):
    """
    Mark a recommendation as completed or not completed
    """
    # TODO: Implement database update
    return {"id": recommendation_id, "completed": completed}
