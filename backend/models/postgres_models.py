"""
SQLAlchemy Models for PostgreSQL (Structured Data)
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from backend.database.postgres import Base


def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())


# Enums
class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class Dosha(str, enum.Enum):
    VATA = "vata"
    PITTA = "pitta"
    KAPHA = "kapha"
    VATA_PITTA = "vata_pitta"
    PITTA_KAPHA = "pitta_kapha"
    VATA_KAPHA = "vata_kapha"


class MentalState(str, enum.Enum):
    STRESSED = "stressed"
    FOCUSED = "focused"
    RELAXED = "relaxed"
    DROWSY = "drowsy"
    ANXIOUS = "anxious"


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Models
class User(Base):
    """User profile and account information"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String)  # For authentication

    # Demographics
    age = Column(Integer)
    gender = Column(SQLEnum(Gender))

    # Ayurvedic
    dosha_type = Column(SQLEnum(Dosha))

    # Health profile
    health_goals = Column(JSON, default=list)  # ["reduce_stress", "improve_sleep"]
    dietary_restrictions = Column(JSON, default=list)  # ["vegetarian", "gluten_free"]
    medical_conditions = Column(JSON, default=list)
    current_medications = Column(JSON, default=list)

    # Preferences
    preferences = Column(JSON, default=dict)  # Notification settings, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete-orphan")
    eeg_analyses = relationship("EEGAnalysis", back_populates="user", cascade="all, delete-orphan")
    voice_analyses = relationship("VoiceAnalysis", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    supplement_logs = relationship("SupplementLog", back_populates="user", cascade="all, delete-orphan")


class HealthMetric(Base):
    """Daily health and fitness metrics"""
    __tablename__ = "health_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Date
    date = Column(Date, nullable=False)

    # Fitness tracking
    steps = Column(Integer)
    calories_burned = Column(Integer)
    distance_km = Column(Float)
    active_minutes = Column(Integer)

    # Vitals
    heart_rate_avg = Column(Integer)
    heart_rate_max = Column(Integer)
    heart_rate_min = Column(Integer)
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)

    # Sleep
    sleep_hours = Column(Float)
    sleep_quality_score = Column(Float)  # 0-1

    # Weight
    weight_kg = Column(Float)
    body_fat_percentage = Column(Float)

    # Mental state (aggregated from EEG/voice)
    stress_level = Column(Float)  # 0-1, averaged from EEG analyses
    focus_level = Column(Float)
    mood_score = Column(Float)  # Self-reported or derived

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="health_metrics")

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )


class EEGAnalysis(Base):
    """EEG brainwave analysis results"""
    __tablename__ = "eeg_analyses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Mental state classification
    mental_state = Column(SQLEnum(MentalState), nullable=False)

    # Probabilities (0-1)
    stress_level = Column(Float, nullable=False)
    focus_level = Column(Float, nullable=False)
    relaxation_level = Column(Float, nullable=False)
    drowsiness_level = Column(Float, nullable=False)

    # Band powers (µV²/Hz)
    delta_power = Column(Float)  # 0.5-4 Hz
    theta_power = Column(Float)  # 4-8 Hz
    alpha_power = Column(Float)  # 8-13 Hz
    beta_power = Column(Float)   # 13-30 Hz
    gamma_power = Column(Float)  # 30-100 Hz

    # Dominant frequency band
    dominant_band = Column(String)  # delta, theta, alpha, beta, gamma

    # Raw data reference (stored in MongoDB)
    mongo_data_id = Column(String)  # Reference to MongoDB document

    # Analysis metadata
    duration_seconds = Column(Float)
    channels_used = Column(Integer)
    sample_rate = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="eeg_analyses")


class VoiceAnalysis(Base):
    """Voice emotion and stress analysis"""
    __tablename__ = "voice_analyses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Primary emotion
    emotion = Column(String, nullable=False)  # neutral, happy, sad, angry, anxious, stressed
    confidence = Column(Float, nullable=False)

    # Emotion probabilities
    emotion_scores = Column(JSON)  # {"neutral": 0.1, "happy": 0.2, ...}

    # Stress indicators
    stress_level = Column(Float)  # 0-1
    voice_tremor_detected = Column(Boolean, default=False)
    pitch_variability = Column(Float)
    speech_rate = Column(Float)  # words per minute

    # Audio metadata
    duration_seconds = Column(Float)
    mongo_audio_id = Column(String)  # Reference to MongoDB audio file

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="voice_analyses")


class Recommendation(Base):
    """Personalized wellness recommendations"""
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Content
    category = Column(String, nullable=False)  # diet, supplement, lifestyle, exercise, sleep, stress
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    reasoning = Column(Text)  # Why this recommendation

    # Evidence and sources
    evidence = Column(JSON, default=list)  # List of citations
    sources = Column(JSON, default=list)  # References

    # Priority and status
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))

    # Effectiveness tracking
    user_feedback = Column(String)  # helpful, not_helpful
    adherence_score = Column(Float)  # How well user followed it

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # Some recommendations may be time-limited

    # Relationships
    user = relationship("User", back_populates="recommendations")


class SupplementLog(Base):
    """User's supplement tracking"""
    __tablename__ = "supplement_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Supplement info
    supplement_name = Column(String, nullable=False)
    supplement_id = Column(String)  # Reference to knowledge base

    # Dosage
    dosage = Column(String, nullable=False)  # e.g., "500mg"
    frequency = Column(String)  # daily, twice_daily, weekly, etc.

    # Duration
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Purpose and notes
    purpose = Column(String)  # Why taking it
    notes = Column(Text)

    # Adherence tracking
    adherence_logs = Column(JSON, default=list)  # [{date: "2024-01-01", taken: true}, ...]

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="supplement_logs")
