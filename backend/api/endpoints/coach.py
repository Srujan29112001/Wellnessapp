"""
AI Wellness Coach Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
import logging

from backend.services.llm_coach import get_wellness_coach
from backend.database.mongo import get_mongo_db

router = APIRouter()
logger = logging.getLogger(__name__)


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
    user_id: str = "demo_user"
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
        # Get wellness coach for this user
        coach = get_wellness_coach(user_id)

        # Chat with the coach
        response = await coach.chat(
            message=request.message,
            include_context=request.include_context
        )

        return ChatResponse(**response)

    except Exception as e:
        logger.error(f"Error in coach chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history", response_model=List[ChatMessage])
async def get_chat_history(
    user_id: str = "demo_user",
    limit: int = 50
):
    """
    Get chat history with wellness coach
    """
    try:
        db = get_mongo_db()

        cursor = db.chat_messages.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        messages = []
        async for msg in cursor:
            messages.append(ChatMessage(
                role=msg.get("role"),
                content=msg.get("content"),
                timestamp=msg.get("timestamp")
            ))

        # Reverse to get chronological order
        messages.reverse()

        return messages

    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return []


@router.post("/session/start", response_model=GuidedSessionResponse)
async def start_guided_session(
    request: GuidedSessionRequest,
    user_id: str = "demo_user"
):
    """
    Start a guided wellness session (breathing, meditation, yoga)
    """
    session_id = str(uuid.uuid4())

    # Session templates
    sessions = {
        "breathing": [
            "Find a comfortable seated position with your back straight",
            "Close your eyes and relax your shoulders",
            "Take a deep breath in through your nose for 4 counts",
            "Hold your breath for 4 counts",
            "Exhale slowly through your mouth for 4 counts",
            "Hold empty for 4 counts",
            "Repeat this cycle for the session duration",
            "Focus on the sensation of your breath",
            "If your mind wanders, gently bring it back to your breathing"
        ],
        "meditation": [
            "Sit comfortably with your spine straight",
            "Close your eyes or maintain a soft gaze",
            "Bring awareness to your breath without changing it",
            "Notice the natural rhythm of inhalation and exhalation",
            "When thoughts arise, acknowledge them without judgment",
            "Gently return your focus to your breath",
            "Continue this practice for the session duration",
            "Gradually expand your awareness to your whole body",
            "When ready, slowly open your eyes"
        ],
        "yoga": [
            "Start in a standing position (Mountain Pose)",
            "Raise your arms overhead as you inhale deeply",
            "Exhale and fold forward from the hips",
            "Inhale, lift halfway with a flat back",
            "Exhale and fold forward again",
            "Inhale and rise up, reaching arms overhead",
            "Exhale and return to standing",
            "Repeat this sun salutation sequence",
            "Move slowly and mindfully with your breath"
        ]
    }

    instructions = sessions.get(
        request.session_type,
        ["Session type not yet implemented. Please try: breathing, meditation, or yoga"]
    )

    return GuidedSessionResponse(
        id=session_id,
        session_type=request.session_type,
        instructions=instructions,
        duration_minutes=request.duration_minutes
    )


@router.post("/proactive-check-in")
async def proactive_check_in(
    user_id: str = "demo_user"
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
        from sqlalchemy import select
        from backend.models.postgres_models import EEGAnalysis, HealthMetric
        from backend.database.postgres import AsyncSessionLocal
        from datetime import timedelta

        async with AsyncSessionLocal() as session:
            # Get latest EEG
            result = await session.execute(
                select(EEGAnalysis)
                .where(EEGAnalysis.user_id == user_id)
                .order_by(EEGAnalysis.timestamp.desc())
                .limit(1)
            )
            latest_eeg = result.scalar_one_or_none()

            # Get today's metrics
            today = datetime.now().date()
            result = await session.execute(
                select(HealthMetric)
                .where(HealthMetric.user_id == user_id)
                .where(HealthMetric.date == today)
            )
            today_metrics = result.scalar_one_or_none()

            # Determine proactive message
            if latest_eeg and latest_eeg.stress_level > 0.7:
                return {
                    "message": f"I noticed your stress levels are elevated ({latest_eeg.stress_level:.0%}). Would you like to try a 5-minute breathing exercise to help you relax?",
                    "urgency": "high",
                    "suggested_action": "breathing_exercise",
                    "session_type": "breathing"
                }
            elif latest_eeg and latest_eeg.focus_level < 0.4:
                return {
                    "message": f"Your focus seems to be declining ({latest_eeg.focus_level:.0%}). Taking a short break or doing some light stretching might help!",
                    "urgency": "medium",
                    "suggested_action": "take_break",
                    "session_type": "stretching"
                }
            elif today_metrics and today_metrics.steps and today_metrics.steps < 2000:
                return {
                    "message": f"You've only taken {today_metrics.steps} steps today. How about a quick walk to boost your energy?",
                    "urgency": "low",
                    "suggested_action": "take_walk",
                    "session_type": "activity"
                }
            else:
                return {
                    "message": "You're doing great! Keep up the healthy habits. Remember to stay hydrated!",
                    "urgency": "low",
                    "suggested_action": "drink_water",
                    "session_type": "reminder"
                }

    except Exception as e:
        logger.error(f"Error in proactive check-in: {e}")
        return {
            "message": "Stay mindful of your wellness throughout the day!",
            "urgency": "low",
            "suggested_action": "general_reminder",
            "session_type": "reminder"
        }
