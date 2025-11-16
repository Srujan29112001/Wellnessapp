"""
AI Wellness Coach Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db
from backend.services.coach_service import wellness_coach

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
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI wellness coach

    The coach has access to:
    - User's health history and metrics
    - Wellness knowledge base (Ayurveda, nutrition, supplements)
    - Recent EEG/voice/diet data
    - Long-term memory of past conversations
    """
    # Use the wellness coach service
    response = await wellness_coach.chat(
        user_id=user_id,
        message=request.message,
        db_session=db if request.include_context else None
    )

    return ChatResponse(
        message=response["content"],
        context_used=response.get("context_used", []),
        recommendations=None,  # Could extract these from response
        sources=response.get("sources", [])
    )


@router.get("/chat/history", response_model=List[ChatMessage])
async def get_chat_history(
    user_id: str = "demo_user",
    limit: int = 50
):
    """
    Get chat history with wellness coach
    """
    history = await wellness_coach.get_conversation_history(user_id, limit)

    return [
        ChatMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp")
        )
        for msg in history
    ]


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
    # TODO: Implement agentic behavior

    return {
        "message": "I noticed you haven't taken a break in 3 hours and your last EEG reading showed declining focus. Would you like to try a 5-minute stretch routine?",
        "urgency": "medium",
        "suggested_action": "take_break",
        "session_type": "stretching"
    }
