"""
AI Wellness Coach Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

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
    from backend.services.llm_coach_service import get_coach

    try:
        coach = get_coach()
        result = await coach.chat(
            user_id=user_id,
            message=request.message,
            user_context=None if request.include_context else {}
        )

        return ChatResponse(
            message=result["message"],
            context_used=result.get("context_used", []),
            recommendations=result.get("recommendations"),
            sources=result.get("sources")
        )

    except Exception as e:
        # Fallback to demo response if LLM not configured
        print(f"Coach service error: {e}. Using demo response.")
        return ChatResponse(
            message="I understand you're seeking wellness guidance. To provide personalized recommendations, I need access to an LLM service (OpenAI or Anthropic). Please configure your API keys in the .env file. In the meantime, I can suggest general wellness practices like regular sleep, balanced nutrition, and stress management techniques.",
            context_used=["Demo mode - LLM not configured"],
            recommendations=[
                "Configure OPENAI_API_KEY or ANTHROPIC_API_KEY in .env",
                "Maintain regular sleep schedule (7-8 hours)",
                "Practice stress management (meditation, breathing)",
                "Eat balanced, whole foods diet"
            ],
            sources=[]
        )


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
