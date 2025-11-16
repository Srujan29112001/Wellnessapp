"""
Health Metrics Service Layer

Handles all business logic for health metrics tracking
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from backend.models.postgres_models import HealthMetric, User
from backend.database.mongo import get_collection

logger = logging.getLogger(__name__)


class HealthService:
    """Service for managing health metrics"""

    @staticmethod
    async def create_health_metric(
        db: AsyncSession,
        user_id: str,
        date: date,
        **kwargs
    ) -> HealthMetric:
        """
        Create a new health metric entry

        Args:
            db: Database session
            user_id: User ID
            date: Date of the metric
            **kwargs: Additional health metric fields (steps, calories, etc.)

        Returns:
            Created HealthMetric object
        """
        try:
            # Check if entry already exists for this date
            existing = await HealthService.get_health_metric_by_date(db, user_id, date)

            if existing:
                # Update existing entry
                for key, value in kwargs.items():
                    if value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                await db.commit()
                await db.refresh(existing)
                return existing

            # Create new entry
            health_metric = HealthMetric(
                user_id=user_id,
                date=date,
                **kwargs
            )

            db.add(health_metric)
            await db.commit()
            await db.refresh(health_metric)

            logger.info(f"Created health metric for user {user_id} on {date}")
            return health_metric

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating health metric: {e}")
            raise

    @staticmethod
    async def get_health_metric_by_date(
        db: AsyncSession,
        user_id: str,
        date: date
    ) -> Optional[HealthMetric]:
        """Get health metric for a specific date"""
        try:
            stmt = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.date == date
                )
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching health metric: {e}")
            raise

    @staticmethod
    async def get_health_metrics(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30
    ) -> List[HealthMetric]:
        """
        Get health metrics for a user within a date range

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            limit: Maximum number of entries to return

        Returns:
            List of HealthMetric objects
        """
        try:
            # Build query
            conditions = [HealthMetric.user_id == user_id]

            if start_date:
                conditions.append(HealthMetric.date >= start_date)
            if end_date:
                conditions.append(HealthMetric.date <= end_date)

            stmt = (
                select(HealthMetric)
                .where(and_(*conditions))
                .order_by(HealthMetric.date.desc())
                .limit(limit)
            )

            result = await db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error fetching health metrics: {e}")
            raise

    @staticmethod
    async def get_health_metric_by_id(
        db: AsyncSession,
        metric_id: str,
        user_id: str
    ) -> Optional[HealthMetric]:
        """Get a specific health metric by ID"""
        try:
            stmt = select(HealthMetric).where(
                and_(
                    HealthMetric.id == metric_id,
                    HealthMetric.user_id == user_id
                )
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching health metric by ID: {e}")
            raise

    @staticmethod
    async def update_health_metric(
        db: AsyncSession,
        metric_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[HealthMetric]:
        """Update a health metric"""
        try:
            metric = await HealthService.get_health_metric_by_id(db, metric_id, user_id)

            if not metric:
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(metric, key) and value is not None:
                    setattr(metric, key, value)

            metric.updated_at = datetime.now()
            await db.commit()
            await db.refresh(metric)

            logger.info(f"Updated health metric {metric_id}")
            return metric

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating health metric: {e}")
            raise

    @staticmethod
    async def delete_health_metric(
        db: AsyncSession,
        metric_id: str,
        user_id: str
    ) -> bool:
        """Delete a health metric"""
        try:
            metric = await HealthService.get_health_metric_by_id(db, metric_id, user_id)

            if not metric:
                return False

            await db.delete(metric)
            await db.commit()

            logger.info(f"Deleted health metric {metric_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting health metric: {e}")
            raise

    @staticmethod
    async def get_health_trends(
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> dict:
        """
        Calculate health trends over time

        Returns aggregated statistics and trends
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            metrics = await HealthService.get_health_metrics(
                db, user_id, start_date, end_date, limit=days
            )

            if not metrics:
                return {}

            # Calculate averages and trends
            total_metrics = len(metrics)

            trends = {
                "period_days": days,
                "total_entries": total_metrics,
                "averages": {},
                "totals": {},
                "latest": {}
            }

            # Calculate averages for numeric fields
            numeric_fields = [
                "steps", "calories_burned", "distance_km", "active_minutes",
                "heart_rate_avg", "sleep_hours", "weight_kg", "stress_level",
                "focus_level", "mood_score"
            ]

            for field in numeric_fields:
                values = [getattr(m, field) for m in metrics if getattr(m, field) is not None]
                if values:
                    avg = sum(values) / len(values)
                    trends["averages"][field] = round(avg, 2)

                    # Get latest value
                    if hasattr(metrics[0], field):
                        latest_value = getattr(metrics[0], field)
                        if latest_value is not None:
                            trends["latest"][field] = latest_value

            # Calculate totals for cumulative fields
            for field in ["steps", "calories_burned", "distance_km", "active_minutes"]:
                values = [getattr(m, field) for m in metrics if getattr(m, field) is not None]
                if values:
                    trends["totals"][field] = sum(values)

            return trends

        except Exception as e:
            logger.error(f"Error calculating health trends: {e}")
            raise

    @staticmethod
    async def correlate_sleep_stress(
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> dict:
        """
        Analyze correlation between sleep and stress levels
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            metrics = await HealthService.get_health_metrics(
                db, user_id, start_date, end_date, limit=days
            )

            # Extract sleep and stress data
            sleep_stress_pairs = [
                (m.sleep_hours, m.stress_level)
                for m in metrics
                if m.sleep_hours is not None and m.stress_level is not None
            ]

            if len(sleep_stress_pairs) < 2:
                return {"correlation": None, "insight": "Insufficient data"}

            # Simple correlation calculation
            sleep_vals = [p[0] for p in sleep_stress_pairs]
            stress_vals = [p[1] for p in sleep_stress_pairs]

            n = len(sleep_vals)
            sleep_mean = sum(sleep_vals) / n
            stress_mean = sum(stress_vals) / n

            numerator = sum((sleep_vals[i] - sleep_mean) * (stress_vals[i] - stress_mean) for i in range(n))
            sleep_var = sum((s - sleep_mean) ** 2 for s in sleep_vals)
            stress_var = sum((s - stress_mean) ** 2 for s in stress_vals)
            denominator = (sleep_var * stress_var) ** 0.5

            correlation = numerator / denominator if denominator != 0 else 0

            # Generate insight
            if correlation < -0.3:
                insight = f"On days with less than {round(sleep_mean, 1)} hours sleep, your stress level is typically {abs(round(correlation * 100))}% higher."
            elif correlation > 0.3:
                insight = "Interestingly, more sleep correlates with slightly higher stress. Consider sleep quality over quantity."
            else:
                insight = "No strong correlation found between sleep duration and stress levels."

            return {
                "correlation": round(correlation, 3),
                "insight": insight,
                "avg_sleep": round(sleep_mean, 1),
                "avg_stress": round(stress_mean, 2),
                "sample_size": n
            }

        except Exception as e:
            logger.error(f"Error analyzing sleep-stress correlation: {e}")
            raise
