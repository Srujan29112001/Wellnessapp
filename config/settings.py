"""
Application Settings using Pydantic
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Wellness AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "wellness_db"
    POSTGRES_USER: str = "wellness_user"
    POSTGRES_PASSWORD: str = "change-me"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MongoDB
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = "wellness_mongo"
    MONGODB_USER: str = "wellness_user"
    MONGODB_PASSWORD: str = "change-me"

    @property
    def MONGODB_URL(self) -> str:
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}?authSource=admin"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "change-me"

    # Vector Database
    VECTOR_DB_TYPE: str = "chroma"
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""

    # LLM Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    USE_LOCAL_LLM: bool = True
    LOCAL_LLM_MODEL: str = "meta-llama/Llama-2-7b-chat-hf"
    HF_TOKEN: str = ""
    MODEL_CACHE_DIR: str = "./data/models"

    # LoRA/QLoRA
    USE_QUANTIZATION: bool = True
    QUANTIZATION_BITS: int = 4
    LORA_RANK: int = 8
    LORA_ALPHA: int = 32

    # ML Models
    EEG_SAMPLE_RATE: int = 256
    EEG_CHANNELS: int = 14
    EEG_MODEL_PATH: str = "./data/models/eeg_classifier.pt"

    VOICE_MODEL_PATH: str = "./data/models/voice_emotion.pt"
    AUDIO_SAMPLE_RATE: int = 16000

    FOOD_MODEL_PATH: str = "./data/models/food_recognition.pt"
    FOOD_CONFIDENCE_THRESHOLD: float = 0.7

    OCR_ENGINE: str = "easyocr"
    OCR_LANGUAGES: str = "en"

    # MLOps
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "wellness-ai"

    WANDB_API_KEY: str = ""
    WANDB_PROJECT: str = "wellness-ai"
    WANDB_ENTITY: str = ""

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    METRICS_PORT: int = 9091
    GRAFANA_PORT: int = 3000

    # Security
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ENCRYPTION_KEY: str = "change-me-32-bytes-long-key-here"
    ENCRYPT_HEALTH_DATA: bool = True

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./data/uploads"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/wellness_ai.log"

    # Feature Flags
    ENABLE_EEG_ANALYSIS: bool = True
    ENABLE_VOICE_ANALYSIS: bool = True
    ENABLE_FOOD_RECOGNITION: bool = True
    ENABLE_OCR: bool = True
    ENABLE_AYURVEDA: bool = True
    ENABLE_GRAPHRAG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
