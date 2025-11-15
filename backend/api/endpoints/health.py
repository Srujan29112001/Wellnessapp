"""
Health Metrics Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from backend.database.postgres import get_db
from backend.models.postgres_models import HealthMetric, User

router = APIRouter()


# Schemas
class HealthMetricCreate(BaseModel):
    date: date
    steps: Optional[int] = None
    calories_burned: Optional[int] = None
    distance_km: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight_kg: Optional[float] = None


class HealthMetricResponse(HealthMetricCreate):
    id: str
    user_id: str
    stress_level: Optional[float] = None
    focus_level: Optional[float] = None
    created_at: datetime


@router.post("/", response_model=HealthMetricResponse)
async def log_health_metrics(
    metrics: HealthMetricCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"  # TODO: Get from auth
):
    """
    Log daily health metrics
    """
    # Check if user exists, create if not
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        # Create demo user
        user = User(
            id=user_id,
            email=f"{user_id}@demo.com",
            name="Demo User"
        )
        db.add(user)
        await db.flush()

    # Create health metric
    health_metric = HealthMetric(
        user_id=user_id,
        **metrics.dict()
    )
    db.add(health_metric)
    await db.commit()
    await db.refresh(health_metric)

    return HealthMetricResponse(
        id=health_metric.id,
        user_id=health_metric.user_id,
        date=health_metric.date,
        steps=health_metric.steps,
        calories_burned=health_metric.calories_burned,
        distance_km=health_metric.distance_km,
        heart_rate_avg=health_metric.heart_rate_avg,
        sleep_hours=health_metric.sleep_hours,
        weight_kg=health_metric.weight_kg,
        stress_level=health_metric.stress_level,
        focus_level=health_metric.focus_level,
        created_at=health_metric.created_at
    )


@router.get("/", response_model=List[HealthMetricResponse])
async def get_health_metrics(
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user",  # TODO: Get from auth
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 30
):
    """
    Get health metrics for a user
    """
    # Build query
    query = select(HealthMetric).where(HealthMetric.user_id == user_id)

    if start_date:
        query = query.where(HealthMetric.date >= start_date)
    if end_date:
        query = query.where(HealthMetric.date <= end_date)

    query = query.order_by(desc(HealthMetric.date)).limit(limit)

    result = await db.execute(query)
    metrics = result.scalars().all()

    return [
        HealthMetricResponse(
            id=m.id,
            user_id=m.user_id,
            date=m.date,
            steps=m.steps,
            calories_burned=m.calories_burned,
            distance_km=m.distance_km,
            heart_rate_avg=m.heart_rate_avg,
            sleep_hours=m.sleep_hours,
            weight_kg=m.weight_kg,
            stress_level=m.stress_level,
            focus_level=m.focus_level,
            created_at=m.created_at
        )
        for m in metrics
    ]


@router.get("/{metric_id}", response_model=HealthMetricResponse)
async def get_health_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"  # TODO: Get from auth
):
    """
    Get specific health metric by ID
    """
    result = await db.execute(
        select(HealthMetric).where(
            and_(
                HealthMetric.id == metric_id,
                HealthMetric.user_id == user_id
            )
        )
    )
    metric = result.scalar_one_or_none()

    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    return HealthMetricResponse(
        id=metric.id,
        user_id=metric.user_id,
        date=metric.date,
        steps=metric.steps,
        calories_burned=metric.calories_burned,
        distance_km=metric.distance_km,
        heart_rate_avg=metric.heart_rate_avg,
        sleep_hours=metric.sleep_hours,
        weight_kg=metric.weight_kg,
        stress_level=metric.stress_level,
        focus_level=metric.focus_level,
        created_at=metric.created_at
    )
