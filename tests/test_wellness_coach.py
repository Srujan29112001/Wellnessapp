"""
Tests for Wellness Coach Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.services.wellness_coach import WellnessCoach


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def wellness_coach():
    """Create wellness coach instance"""
    return WellnessCoach()


@pytest.mark.asyncio
async def test_chat_basic(wellness_coach, mock_db):
    """Test basic chat functionality"""
    result = await wellness_coach.chat(
        user_id="test_user",
        message="I feel stressed",
        db=mock_db,
        include_context=False
    )

    assert "message" in result
    assert isinstance(result["message"], str)
    assert len(result["message"]) > 0


@pytest.mark.asyncio
async def test_chat_with_stress_message(wellness_coach, mock_db):
    """Test stress-related response"""
    result = await wellness_coach.chat(
        user_id="test_user",
        message="I'm feeling very anxious and stressed",
        db=mock_db,
        include_context=False
    )

    message_lower = result["message"].lower()
    # Should contain stress-related advice
    assert any(word in message_lower for word in ["stress", "anxious", "breathing", "relax"])


@pytest.mark.asyncio
async def test_chat_with_sleep_message(wellness_coach, mock_db):
    """Test sleep-related response"""
    result = await wellness_coach.chat(
        user_id="test_user",
        message="I can't sleep well",
        db=mock_db,
        include_context=False
    )

    message_lower = result["message"].lower()
    # Should contain sleep-related advice
    assert any(word in message_lower for word in ["sleep", "insomnia", "bed", "rest"])


def test_extract_recommendations(wellness_coach):
    """Test recommendation extraction"""
    response = """Here are my recommendations:
    1. Get more sleep
    2. Exercise daily
    3. Eat healthy foods
    """

    recommendations = wellness_coach._extract_recommendations(response)

    assert len(recommendations) > 0
    assert any("sleep" in rec.lower() for rec in recommendations)


def test_create_context_string(wellness_coach):
    """Test context string creation"""
    context = {
        "sleep_average": 6.5,
        "stress_trend": "increasing",
        "recent_eeg": {
            "mental_state": "stressed",
            "stress_level": 0.75,
            "focus_level": 0.40,
            "relaxation_level": 0.25
        }
    }

    context_string = wellness_coach._create_context_string(context)

    assert "6.5 hours" in context_string
    assert "increasing" in context_string
    assert "stressed" in context_string


@pytest.mark.asyncio
async def test_get_chat_history_empty(wellness_coach):
    """Test getting chat history when empty"""
    with patch('backend.services.wellness_coach.get_mongo_db') as mock_get_db:
        mock_collection = Mock()
        mock_collection.find.return_value.sort.return_value.limit.return_value = AsyncMock(
            __aiter__=lambda x: iter([])
        )
        mock_db = Mock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        history = await wellness_coach.get_chat_history("test_user", limit=10)

        assert isinstance(history, list)
