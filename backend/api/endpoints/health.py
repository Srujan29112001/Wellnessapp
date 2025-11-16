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
    # TODO: Implement database storage
    return HealthMetricResponse(
        id="temp_id",
        user_id=user_id,
        **metrics.dict(),
        created_at=datetime.now()
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
    # TODO: Implement database query
    return []


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
