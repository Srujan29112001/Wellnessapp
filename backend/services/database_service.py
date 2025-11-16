"""
Database Service Layer

Provides CRUD operations for PostgreSQL and MongoDB
Handles all database interactions for the API endpoints
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from backend.models.postgres_models import (
    User, HealthMetric, EEGAnalysis, VoiceAnalysis,
    Recommendation, SupplementLog
)


class PostgresService:
    """Service for PostgreSQL operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # User operations
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user"""
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """Update user profile"""
        user = await self.get_user(user_id)
        if not user:
            return None

        for key, value in updates.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # Health Metrics operations
    async def create_health_metric(self, metric_data: Dict[str, Any]) -> HealthMetric:
        """Log daily health metrics"""
        metric = HealthMetric(**metric_data)
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric

    async def get_health_metrics(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 30
    ) -> List[HealthMetric]:
        """Get health metrics for a user"""
        query = select(HealthMetric).where(HealthMetric.user_id == user_id)

        if start_date:
            query = query.where(HealthMetric.date >= start_date)
        if end_date:
            query = query.where(HealthMetric.date <= end_date)

        query = query.order_by(HealthMetric.date.desc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_latest_health_metric(self, user_id: str) -> Optional[HealthMetric]:
        """Get most recent health metric"""
        result = await self.session.execute(
            select(HealthMetric)
            .where(HealthMetric.user_id == user_id)
            .order_by(HealthMetric.date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # EEG Analysis operations
    async def create_eeg_analysis(self, analysis_data: Dict[str, Any]) -> EEGAnalysis:
        """Store EEG analysis result"""
        analysis = EEGAnalysis(**analysis_data)
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def get_eeg_analyses(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[EEGAnalysis]:
        """Get EEG analyses for a user"""
        result = await self.session.execute(
            select(EEGAnalysis)
            .where(EEGAnalysis.user_id == user_id)
            .order_by(EEGAnalysis.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_eeg_analysis(self, user_id: str) -> Optional[EEGAnalysis]:
        """Get most recent EEG analysis"""
        result = await self.session.execute(
            select(EEGAnalysis)
            .where(EEGAnalysis.user_id == user_id)
            .order_by(EEGAnalysis.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # Voice Analysis operations
    async def create_voice_analysis(self, analysis_data: Dict[str, Any]) -> VoiceAnalysis:
        """Store voice analysis result"""
        analysis = VoiceAnalysis(**analysis_data)
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def get_voice_analyses(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[VoiceAnalysis]:
        """Get voice analyses for a user"""
        result = await self.session.execute(
            select(VoiceAnalysis)
            .where(VoiceAnalysis.user_id == user_id)
            .order_by(VoiceAnalysis.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # Recommendation operations
    async def create_recommendation(self, rec_data: Dict[str, Any]) -> Recommendation:
        """Create a new recommendation"""
        rec = Recommendation(**rec_data)
        self.session.add(rec)
        await self.session.commit()
        await self.session.refresh(rec)
        return rec

    async def get_recommendations(
        self,
        user_id: str,
        active_only: bool = True,
        limit: int = 10
    ) -> List[Recommendation]:
        """Get recommendations for a user"""
        query = select(Recommendation).where(Recommendation.user_id == user_id)

        if active_only:
            query = query.where(Recommendation.status == 'active')

        query = query.order_by(Recommendation.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_recommendation_status(
        self,
        rec_id: str,
        status: str,
        adherence_score: Optional[float] = None
    ) -> Optional[Recommendation]:
        """Update recommendation status"""
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.id == rec_id)
        )
        rec = result.scalar_one_or_none()

        if rec:
            rec.status = status
            if adherence_score is not None:
                rec.adherence_score = adherence_score
            await self.session.commit()
            await self.session.refresh(rec)

        return rec

    # Supplement Log operations
    async def log_supplement(self, log_data: Dict[str, Any]) -> SupplementLog:
        """Log supplement intake"""
        log = SupplementLog(**log_data)
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_supplement_logs(
        self,
        user_id: str,
        supplement_name: Optional[str] = None,
        limit: int = 30
    ) -> List[SupplementLog]:
        """Get supplement logs"""
        query = select(SupplementLog).where(SupplementLog.user_id == user_id)

        if supplement_name:
            query = query.where(SupplementLog.supplement_name == supplement_name)

        query = query.order_by(SupplementLog.taken_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_supplement_adherence(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, float]:
        """Calculate supplement adherence rates"""
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(SupplementLog)
            .where(
                SupplementLog.user_id == user_id,
                SupplementLog.taken_at >= start_date
            )
        )
        logs = result.scalars().all()

        # Calculate adherence by supplement
        adherence = {}
        for log in logs:
            name = log.supplement_name
            if name not in adherence:
                adherence[name] = {"taken": 0, "total": 0}

            adherence[name]["total"] += 1
            if log.taken:
                adherence[name]["taken"] += 1

        # Calculate percentages
        return {
            name: (stats["taken"] / stats["total"] * 100)
            for name, stats in adherence.items()
            if stats["total"] > 0
        }


class MongoService:
    """Service for MongoDB operations"""

    def __init__(self, client: AsyncIOMotorClient, db_name: str = "wellness_db"):
        self.client = client
        self.db = client[db_name]

    # Journal entries
    async def create_journal_entry(self, entry_data: Dict[str, Any]) -> str:
        """Create journal entry"""
        result = await self.db.journal_entries.insert_one(entry_data)
        return str(result.inserted_id)

    async def get_journal_entries(
        self,
        user_id: str,
        limit: int = 30
    ) -> List[Dict]:
        """Get journal entries"""
        cursor = self.db.journal_entries.find(
            {"user_id": user_id}
        ).sort("date", -1).limit(limit)

        entries = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for entry in entries:
            entry["_id"] = str(entry["_id"])

        return entries

    # Chat messages
    async def store_chat_message(self, message_data: Dict[str, Any]) -> str:
        """Store chat message"""
        result = await self.db.chat_messages.insert_one(message_data)
        return str(result.inserted_id)

    async def get_chat_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get chat history"""
        cursor = self.db.chat_messages.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        messages = await cursor.to_list(length=limit)

        # Reverse to get chronological order
        messages.reverse()

        # Convert ObjectId to string
        for msg in messages:
            msg["_id"] = str(msg["_id"])

        return messages

    # Meal images
    async def store_meal_image(self, meal_data: Dict[str, Any]) -> str:
        """Store meal image data"""
        result = await self.db.meal_images.insert_one(meal_data)
        return str(result.inserted_id)

    async def get_meal_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get meal history"""
        cursor = self.db.meal_images.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        meals = await cursor.to_list(length=limit)

        for meal in meals:
            meal["_id"] = str(meal["_id"])

        return meals

    # EEG raw data
    async def store_eeg_raw_data(self, eeg_data: Dict[str, Any]) -> str:
        """Store raw EEG data"""
        result = await self.db.eeg_raw_data.insert_one(eeg_data)
        return str(result.inserted_id)

    async def get_eeg_raw_data(self, recording_id: str) -> Optional[Dict]:
        """Get raw EEG data by ID"""
        if not ObjectId.is_valid(recording_id):
            return None

        data = await self.db.eeg_raw_data.find_one({"_id": ObjectId(recording_id)})

        if data:
            data["_id"] = str(data["_id"])

        return data

    # Voice recordings
    async def store_voice_recording(self, voice_data: Dict[str, Any]) -> str:
        """Store voice recording metadata"""
        result = await self.db.voice_recordings.insert_one(voice_data)
        return str(result.inserted_id)

    async def get_voice_recordings(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get voice recordings"""
        cursor = self.db.voice_recordings.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        recordings = await cursor.to_list(length=limit)

        for rec in recordings:
            rec["_id"] = str(rec["_id"])

        return recordings

    # User context (long-term memory)
    async def update_user_context(
        self,
        user_id: str,
        context_updates: Dict[str, Any]
    ) -> None:
        """Update user's context/memory"""
        await self.db.user_contexts.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    **context_updates,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def get_user_context(self, user_id: str) -> Optional[Dict]:
        """Get user's context"""
        context = await self.db.user_contexts.find_one({"user_id": user_id})

        if context:
            context["_id"] = str(context["_id"])

        return context


# Dependency injection helpers
_postgres_service: Optional[PostgresService] = None
_mongo_service: Optional[MongoService] = None


def get_postgres_service(session: AsyncSession) -> PostgresService:
    """Get PostgreSQL service instance"""
    return PostgresService(session)


def get_mongo_service(client: AsyncIOMotorClient) -> MongoService:
    """Get MongoDB service instance"""
    return MongoService(client)
