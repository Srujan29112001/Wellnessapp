"""
AI Wellness Coach Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db
from backend.services.llm_coach import get_wellness_coach, WellnessCoach
from backend.models.postgres_models import User, HealthMetric, EEGAnalysis
from backend.models.mongo_schemas import ChatMessage as ChatMessageMongo
from backend.database.mongo import get_mongo_db

router = APIRouter()


# Schemas
class ChatMessage(BaseModel):
    role: str  # user or assistant
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    include_context: bool = True


class ChatResponse(BaseModel):
    message: str
    context_used: List[str]
    recommendations: Optional[List[str]] = None
    sources: Optional[List[str]] = None


class GuidedSessionRequest(BaseModel):
    session_type: str  # breathing, meditation, yoga
    duration_minutes: int


class GuidedSessionResponse(BaseModel):
    id: str
    session_type: str
    instructions: List[str]
    duration_minutes: int
    audio_url: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_coach(
    request: ChatRequest,
    user_id: str = "demo_user",
    db: AsyncSession = Depends(get_db),
    coach: WellnessCoach = Depends(get_wellness_coach)
):
    """
    Chat with AI wellness coach

    The coach has access to:
    - User's health history and metrics
    - Wellness knowledge base (Ayurveda, nutrition, supplements)
    - Recent EEG/voice/diet data
    - Long-term memory of past conversations
    """
    try:
        # Build user context from database if requested
        user_context = {}
        if request.include_context:
            user_context = await _build_user_context(db, user_id)

        # Chat with LLM coach
        response = await coach.chat(
            user_message=request.message,
            user_id=user_id,
            user_context=user_context
        )

        # Store conversation in MongoDB
        await _store_chat_message(user_id, request.message, response["answer"])

        # Extract recommendations from response if any
        recommendations = []
        if "recommend" in response["answer"].lower():
            # Simple extraction - could be improved with NLP
            lines = response["answer"].split(".")
            for line in lines:
                if any(keyword in line.lower() for keyword in ["recommend", "suggest", "try", "consider"]):
                    recommendations.append(line.strip())

        return ChatResponse(
            message=response["answer"],
            context_used=[src["metadata"].get("source", "knowledge_base") for src in response.get("sources", [])],
            recommendations=recommendations[:3] if recommendations else None,
            sources=[f"{src['metadata'].get('type', 'source')}: {src['content'][:100]}..."
                    for src in response.get("sources", [])]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting with coach: {str(e)}")


@router.get("/chat/history", response_model=List[ChatMessage])
async def get_chat_history(
    user_id: str = "demo_user",
    limit: int = 50
):
    """
    Get chat history with wellness coach
    """
    # TODO: Implement database query
    return []


@router.post("/session/start", response_model=GuidedSessionResponse)
async def start_guided_session(
    request: GuidedSessionRequest,
    user_id: str = "demo_user"
):
    """
    Start a guided wellness session (breathing, meditation, yoga)
    """
    # TODO: Implement guided session generation

    if request.session_type == "breathing":
        instructions = [
            "Find a comfortable seated position",
            "Close your eyes and relax your shoulders",
            "Breathe in slowly through your nose for 4 counts",
            "Hold your breath for 4 counts",
            "Exhale slowly through your mouth for 4 counts",
            "Hold empty for 4 counts",
            "Repeat this cycle for the session duration"
        ]
    else:
        instructions = ["Session type not yet implemented"]

    return GuidedSessionResponse(
        id="temp_id",
        session_type=request.session_type,
        instructions=instructions,
        duration_minutes=request.duration_minutes
    )


@router.post("/proactive-check-in")
async def proactive_check_in(
    user_id: str = "demo_user",
    db: AsyncSession = Depends(get_db),
    coach: WellnessCoach = Depends(get_wellness_coach)
):
    """
    Proactive AI check-in based on user's current state

    The AI analyzes recent data and may suggest:
    - Taking a break
    - Drinking water
    - Doing a quick exercise
    - Stress management techniques
    """
    try:
        # Build user health context
        user_context = await _build_user_context(db, user_id)

        # Get proactive recommendations from AI coach
        recommendations = await coach.get_proactive_recommendations(
            user_id=user_id,
            user_health_data=user_context
        )

        # Determine urgency based on context
        urgency = "low"
        if user_context.get("stress_level", 0) > 0.7:
            urgency = "high"
        elif user_context.get("stress_level", 0) > 0.5:
            urgency = "medium"

        return {
            "message": recommendations[0] if recommendations else "Keep up the great work!",
            "urgency": urgency,
            "suggested_actions": recommendations,
            "context": user_context
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in proactive check-in: {str(e)}")


# Helper functions
async def _build_user_context(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """Build user context from recent health data"""
    from sqlalchemy import select, desc
    from datetime import timedelta

    context = {}

    try:
        # Get recent health metrics (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(HealthMetric)
            .where(HealthMetric.user_id == user_id)
            .where(HealthMetric.date >= recent_date)
            .order_by(desc(HealthMetric.date))
            .limit(7)
        )
        metrics = result.scalars().all()

        if metrics:
            # Average metrics
            context["avg_sleep_hours"] = sum(m.sleep_hours for m in metrics if m.sleep_hours) / len(metrics)
            context["avg_steps"] = sum(m.steps for m in metrics if m.steps) / len(metrics)
            context["recent_mood"] = metrics[0].mood if metrics[0].mood else "unknown"

        # Get latest EEG analysis
        result = await db.execute(
            select(EEGAnalysis)
            .where(EEGAnalysis.user_id == user_id)
            .order_by(desc(EEGAnalysis.analyzed_at))
            .limit(1)
        )
        eeg = result.scalar_one_or_none()

        if eeg:
            context["stress_level"] = eeg.beta_power / (eeg.alpha_power + 0.01)  # Beta/Alpha ratio
            context["relaxation_level"] = eeg.alpha_power
            context["mental_state"] = eeg.predicted_state

        # Get user profile
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            context["goals"] = user.health_goals
            context["dietary_restrictions"] = user.dietary_restrictions
            context["ayurvedic_dosha"] = user.ayurvedic_dosha

    except Exception as e:
        print(f"Error building user context: {e}")

    return context


async def _store_chat_message(user_id: str, user_message: str, ai_response: str):
    """Store chat message in MongoDB"""
    try:
        mongo_db = get_mongo_db()
        chat_collection = mongo_db["chat_messages"]

        message_doc = {
            "user_id": user_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.utcnow(),
            "metadata": {}
        }

        await chat_collection.insert_one(message_doc)
    except Exception as e:
        print(f"Error storing chat message: {e}")
