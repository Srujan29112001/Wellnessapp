"""
Health Metrics Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db

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
    user_id: str = "demo_user",  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """
    Log daily health metrics
    """
    from backend.services.health_service import HealthService

    health_metric = await HealthService.create_health_metric(
        db,
        user_id=user_id,
        date=metrics.date,
        steps=metrics.steps,
        calories_burned=metrics.calories_burned,
        distance_km=metrics.distance_km,
        heart_rate_avg=metrics.heart_rate_avg,
        sleep_hours=metrics.sleep_hours,
        weight_kg=metrics.weight_kg
    )

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
    user_id: str = "demo_user",  # TODO: Get from auth
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health metrics for a user
    """
    from backend.services.health_service import HealthService

    metrics = await HealthService.get_health_metrics(
        db, user_id, start_date, end_date, limit
    )

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
    user_id: str = "demo_user"  # TODO: Get from auth
):
    """
    Get specific health metric by ID
    """
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Metric not found")
