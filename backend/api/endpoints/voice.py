"""
Voice Emotion Analysis Endpoints
"""
from fastapi import APIRouter, UploadFile, File
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


# Schemas
class VoiceEmotionResponse(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    emotion: str  # neutral, happy, sad, angry, anxious, stressed
    confidence: float
    emotional_state: Dict[str, float]  # probabilities for all emotions
    stress_indicators: List[str]


@router.post("/analyze", response_model=VoiceEmotionResponse)
async def analyze_voice(
    file: UploadFile = File(...),
    user_id: str = "demo_user"
):
    """
    Analyze voice recording for emotion and stress detection

    Accepts: WAV, MP3, M4A audio files
    """
    from backend.services.voice_service import get_voice_service

    # Read file bytes
    file_bytes = await file.read()

    # Analyze voice
    service = get_voice_service()
    result = await service.analyze_voice_file(file_bytes, user_id)

    return VoiceEmotionResponse(
        id=result["id"],
        user_id=result["user_id"],
        timestamp=result["timestamp"],
        emotion=result["emotion"],
        confidence=result["confidence"],
        emotional_state=result["emotional_state"],
        stress_indicators=result["stress_indicators"]
    )


@router.get("/history", response_model=List[VoiceEmotionResponse])
async def get_voice_analysis_history(
    user_id: str = "demo_user",
    limit: int = 20
):
    """
    Get voice emotion analysis history
    """
    # TODO: Implement database query
    return []
