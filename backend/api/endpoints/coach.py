"""
AI Wellness Coach Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from backend.database.postgres import get_db
from backend.services.llm_coach_service import get_coach

# Initialize wellness coach
wellness_coach = get_coach()

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
    db: AsyncSession = Depends(get_db),
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
        # Use the wellness coach service
        response = await wellness_coach.chat(
            user_id=user_id,
            message=request.message,
            user_context=None if not request.include_context else None  # Will use default context from DB
        )

        return ChatResponse(
            message=response["message"],
            context_used=response.get("context_used", []),
            recommendations=response.get("recommendations"),
            sources=response.get("sources", [])
        )
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
        history = await wellness_coach.get_conversation_history(user_id, limit)

        return [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp")
            )
            for msg in history
        ]
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

    if request.session_type == "breathing":
        instructions = [
            "🧘 Find a comfortable seated position with your spine straight",
            "👁️ Close your eyes gently and relax your shoulders",
            "🌬️ Inhale slowly through your nose for 4 counts (1... 2... 3... 4...)",
            "⏸️ Hold your breath gently for 4 counts",
            "💨 Exhale slowly through your mouth for 4 counts",
            "⏸️ Hold empty for 4 counts",
            "🔄 Repeat this box breathing cycle for the session duration",
            "💭 If your mind wanders, gently bring your attention back to your breath",
            "✨ When complete, slowly open your eyes and notice how you feel"
        ]

    elif request.session_type == "meditation":
        instructions = [
            "🪷 Sit comfortably with a straight but relaxed posture",
            "👁️ Close your eyes or maintain a soft downward gaze",
            "🌬️ Begin by taking 3 deep, cleansing breaths",
            "🎯 Bring your attention to your breath - notice the natural rhythm",
            "💭 When thoughts arise, acknowledge them without judgment",
            "🌊 Imagine thoughts passing like clouds in the sky",
            "💫 Return your focus gently to your breath each time",
            "❤️ Cultivate a sense of compassion for yourself",
            f"⏱️ Continue for {request.duration_minutes} minutes",
            "🙏 When ready, slowly return your awareness to the room"
        ]

    elif request.session_type == "yoga":
        instructions = [
            "🧘 Stand in Mountain Pose (Tadasana) - feet hip-width apart",
            "🙏 Bring hands to heart center, take 3 deep breaths",
            "🌅 Inhale, raise arms overhead - Upward Salute",
            "🤸 Exhale, fold forward - Standing Forward Bend",
            "🦎 Inhale, halfway lift - Flat Back",
            "🐕 Exhale, step back to Downward Facing Dog",
            "🪱 Lower to Plank, then Cobra or Upward Dog",
            "🐕 Push back to Downward Dog (hold for 5 breaths)",
            "🚶 Step or jump feet forward",
            "🙏 Inhale to stand, hands to heart - Mountain Pose",
            f"🔄 Repeat sequence for {request.duration_minutes} minutes"
        ]

    else:
        instructions = [
            f"Session type '{request.session_type}' is coming soon!",
            "Try 'breathing', 'meditation', or 'yoga' for now."
        ]

    return GuidedSessionResponse(
        id=session_id,
        session_type=request.session_type,
        instructions=instructions,
        duration_minutes=request.duration_minutes
    )


@router.post("/proactive-check-in")
async def proactive_check_in(
    db: AsyncSession = Depends(get_db),
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
        from sqlalchemy import select, desc
        from backend.models.postgres_models import EEGAnalysis, HealthMetric

        # Get latest EEG analysis
        eeg_result = await db.execute(
            select(EEGAnalysis)
            .where(EEGAnalysis.user_id == user_id)
            .order_by(desc(EEGAnalysis.timestamp))
            .limit(1)
        )
        latest_eeg = eeg_result.scalar_one_or_none()

        # Get today's metrics
        today = datetime.now().date()
        health_result = await db.execute(
            select(HealthMetric)
            .where(HealthMetric.user_id == user_id)
            .where(HealthMetric.date == today)
        )
        today_metrics = health_result.scalar_one_or_none()

        # Determine proactive message
        if latest_eeg and latest_eeg.stress_level > 0.7:
            return {
                "message": f"I noticed your stress levels are elevated ({latest_eeg.stress_level:.0%}). Would you like to try a 5-minute breathing exercise to help calm your nervous system?",
                "urgency": "high",
                "suggested_action": "breathing_exercise",
                "session_type": "breathing",
                "timestamp": datetime.now()
            }
        elif latest_eeg and latest_eeg.focus_level < 0.3:
            return {
                "message": f"Your focus seems low ({latest_eeg.focus_level:.0%}). Consider taking a short break or trying a brief meditation to reset your mind.",
                "urgency": "medium",
                "suggested_action": "take_break",
                "session_type": "meditation",
                "timestamp": datetime.now()
            }
        elif latest_eeg and latest_eeg.drowsiness_level > 0.6:
            return {
                "message": f"You seem drowsy. Consider a short walk, some water, or a power nap to recharge.",
                "urgency": "medium",
                "suggested_action": "energy_boost",
                "timestamp": datetime.now()
            }
        elif today_metrics and today_metrics.steps and today_metrics.steps < 2000:
            return {
                "message": f"You've only taken {today_metrics.steps} steps today. How about a quick walk to boost your energy?",
                "urgency": "low",
                "suggested_action": "take_walk",
                "session_type": "activity",
                "timestamp": datetime.now()
            }
        else:
            return {
                "message": "You're doing great! Keep up the healthy habits. Remember to stay hydrated!",
                "urgency": "low",
                "suggested_action": "drink_water",
                "session_type": "reminder",
                "timestamp": datetime.now()
            }

    except Exception as e:
        logger.error(f"Error in proactive check-in: {e}")
        return {
            "message": "Stay mindful of your wellness throughout the day!",
            "urgency": "low",
            "suggested_action": "general_reminder",
            "session_type": "reminder",
            "timestamp": datetime.now()
        }
