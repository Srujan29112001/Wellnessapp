"""
Health Metrics Service - Database operations for health data
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date, datetime

from backend.models.postgres_models import HealthMetric, User
from backend.database.postgres import get_db


class HealthMetricService:
    """Service for health metrics CRUD operations"""

    @staticmethod
    async def create_health_metric(
        db: AsyncSession,
        user_id: str,
        date_value: date,
        **kwargs
    ) -> HealthMetric:
        """Create a new health metric entry"""
        # Check if entry exists for this date
        existing = await HealthMetricService.get_by_date(db, user_id, date_value)
        if existing:
            # Update existing
            for key, value in kwargs.items():
                if value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            await db.commit()
            await db.refresh(existing)
            return existing

        # Create new
        metric = HealthMetric(
            user_id=user_id,
            date=date_value,
            **kwargs
        )
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        return metric

    @staticmethod
    async def get_by_id(db: AsyncSession, metric_id: str, user_id: str) -> Optional[HealthMetric]:
        """Get health metric by ID"""
        stmt = select(HealthMetric).where(
            and_(
                HealthMetric.id == metric_id,
                HealthMetric.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_date(db: AsyncSession, user_id: str, date_value: date) -> Optional[HealthMetric]:
        """Get health metric for a specific date"""
        stmt = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.date == date_value
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_metrics(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30
    ) -> List[HealthMetric]:
        """Get health metrics for a user with optional date range"""
        stmt = select(HealthMetric).where(HealthMetric.user_id == user_id)

        if start_date:
            stmt = stmt.where(HealthMetric.date >= start_date)
        if end_date:
            stmt = stmt.where(HealthMetric.date <= end_date)

        stmt = stmt.order_by(HealthMetric.date.desc()).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_stress_focus(
        db: AsyncSession,
        metric_id: str,
        stress_level: Optional[float] = None,
        focus_level: Optional[float] = None
    ) -> Optional[HealthMetric]:
        """Update mental state metrics from EEG/voice analysis"""
        stmt = select(HealthMetric).where(HealthMetric.id == metric_id)
        result = await db.execute(stmt)
        metric = result.scalar_one_or_none()

        if metric:
            if stress_level is not None:
                metric.stress_level = stress_level
            if focus_level is not None:
                metric.focus_level = focus_level
            metric.updated_at = datetime.now()
            await db.commit()
            await db.refresh(metric)

        return metric

    @staticmethod
    async def delete_metric(db: AsyncSession, metric_id: str, user_id: str) -> bool:
        """Delete a health metric"""
        metric = await HealthMetricService.get_by_id(db, metric_id, user_id)
        if metric:
            await db.delete(metric)
            await db.commit()
            return True
        return False
