"""
MongoDB Schemas (Unstructured/Semi-structured Data)

MongoDB is used for:
- Large binary data (EEG raw signals, audio files, images)
- Unstructured text (journals, chat history)
- Flexible schema data

These are PyDantic models for validation, not ORM models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class JournalEntry(BaseModel):
    """User's daily journal/mood entries"""
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    timestamp: datetime
    entry_text: str
    mood_tags: List[str] = []  # happy, anxious, energetic, etc.
    gratitude_items: List[str] = []
    challenges: List[str] = []
    sentiment_score: Optional[float] = None  # Analyzed sentiment
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class EEGRawData(BaseModel):
    """Raw EEG signal data"""
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    timestamp: datetime

    # Signal data
    channels: List[List[float]]  # [[ch1_samples], [ch2_samples], ...]
    channel_names: List[str] = []
    sample_rate: int = 256  # Hz
    duration_seconds: float

    # Metadata
    device_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

    # Reference to analysis
    analysis_id: Optional[str] = None  # Links to EEGAnalysis in PostgreSQL

    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class VoiceRecording(BaseModel):
    """Voice recording metadata and features"""
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    timestamp: datetime

    # Audio file info
    file_path: str  # Path to audio file (could be S3, local, etc.)
    duration_seconds: float
    format: str  # wav, mp3, etc.
    sample_rate: int = 16000

    # Extracted features (for analysis)
    mfcc_features: Optional[List[List[float]]] = None
    pitch_contour: Optional[List[float]] = None
    energy_contour: Optional[List[float]] = None

    # Transcription (if available)
    transcription: Optional[str] = None

    # Reference to analysis
    analysis_id: Optional[str] = None  # Links to VoiceAnalysis in PostgreSQL

    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class ChatMessage(BaseModel):
    """Chat conversation with AI wellness coach"""
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    timestamp: datetime

    role: str  # user, assistant, system
    content: str

    # Context used for this message
    context_used: Optional[List[str]] = None  # What data/knowledge was retrieved
    sources: Optional[List[str]] = None  # Citations

    # Metadata
    model_used: Optional[str] = None  # Which LLM model
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None

    # Feedback
    user_rating: Optional[int] = None  # 1-5 stars
    user_feedback: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class MealImage(BaseModel):
    """Meal images and recognition results"""
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str
    timestamp: datetime

    # Image info
    image_path: str
    image_format: str  # jpg, png

    # Recognition results
    detected_foods: List[Dict[str, Any]] = []  # [{name: "", confidence: 0.9, ...}]

    # OCR results (if supplement label)
    ocr_text: Optional[str] = None
    extracted_info: Optional[Dict[str, Any]] = None

    # Meal log reference
    meal_log_id: Optional[str] = None  # Links to MealLog if created

    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class UserContext(BaseModel):
    """
    User's aggregated context and long-term memory for AI coach

    This is updated periodically to maintain a summary of the user's
    health journey, preferences, and patterns
    """
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: str

    # Health patterns and insights
    patterns: Dict[str, Any] = {}  # Discovered patterns like "stress increases on Mondays"
    insights: List[Dict[str, Any]] = []  # Key insights generated over time

    # Preferences learned over time
    communication_style: Optional[str] = None  # formal, casual, empathetic
    preferred_interventions: List[str] = []  # breathing, meditation, supplements
    topics_of_interest: List[str] = []

    # Goals and progress
    active_goals: List[Dict[str, Any]] = []
    completed_goals: List[Dict[str, Any]] = []
    milestones: List[Dict[str, Any]] = []

    # Key memories (important events, breakthroughs)
    key_memories: List[Dict[str, Any]] = []

    # Last updated
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


# Collection names constants
COLLECTION_JOURNAL_ENTRIES = "journal_entries"
COLLECTION_EEG_RAW_DATA = "eeg_raw_data"
COLLECTION_VOICE_RECORDINGS = "voice_recordings"
COLLECTION_CHAT_MESSAGES = "chat_messages"
COLLECTION_MEAL_IMAGES = "meal_images"
COLLECTION_USER_CONTEXT = "user_context"
