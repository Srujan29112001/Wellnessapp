"""
Health Metrics Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db
from backend.services.health_service import HealthMetricService

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
    # Create or update health metric
    metric = await HealthMetricService.create_health_metric(
        db=db,
        user_id=user_id,
        date_value=metrics.date,
        **metrics.dict(exclude={'date'})
    )

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
    metrics = await HealthMetricService.get_metrics(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
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
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"  # TODO: Get from auth
):
    """
    Get specific health metric by ID
    """
    metric = await HealthMetricService.get_by_id(db, metric_id, user_id)

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
