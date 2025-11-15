"""
Health Metrics Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

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
    user_id: str = "demo_user"  # TODO: Get from auth
):
    """
    Get specific health metric by ID
    """
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Metric not found")
