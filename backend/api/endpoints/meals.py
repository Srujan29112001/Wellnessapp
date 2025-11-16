"""
Meal and Diet Logging Endpoints
"""
from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from enum import Enum

from backend.services.meal_service import MealService

router = APIRouter()


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


# Schemas
class MealLog(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    meal_type: MealType
    food_items: List[str]
    portion_sizes: Optional[List[str]] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None


class MealLogCreate(BaseModel):
    meal_type: MealType
    food_items: List[str]
    portion_sizes: Optional[List[str]] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    notes: Optional[str] = None


class NutritionalSummary(BaseModel):
    date: date
    total_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    meals_logged: int
    recommendations: List[str]


@router.post("/", response_model=MealLog)
async def log_meal(
    meal: MealLogCreate,
    user_id: str = "demo_user"
):
    """
    Log a meal
    """
    # Convert food items to food dicts
    foods = []
    for i, food_name in enumerate(meal.food_items):
        food_dict = {
            "name": food_name,
            "calories": meal.calories // len(meal.food_items) if meal.calories else 0,
            "protein_g": meal.protein_g / len(meal.food_items) if meal.protein_g else 0,
            "carbs_g": meal.carbs_g / len(meal.food_items) if meal.carbs_g else 0,
            "fat_g": meal.fat_g / len(meal.food_items) if meal.fat_g else 0,
            "fiber_g": meal.fiber_g / len(meal.food_items) if meal.fiber_g else 0,
        }
        if meal.portion_sizes and i < len(meal.portion_sizes):
            food_dict["portion"] = meal.portion_sizes[i]
        foods.append(food_dict)

    meal_log = await MealService.log_meal(
        user_id=user_id,
        meal_type=meal.meal_type.value,
        foods=foods,
        notes=meal.notes
    )

    return MealLog(
        id=meal_log["_id"],
        user_id=meal_log["user_id"],
        timestamp=meal_log["timestamp"],
        meal_type=MealType(meal_log["meal_type"]),
        food_items=meal.food_items,
        portion_sizes=meal.portion_sizes,
        calories=meal.calories,
        protein_g=meal.protein_g,
        carbs_g=meal.carbs_g,
        fat_g=meal.fat_g,
        fiber_g=meal.fiber_g,
        notes=meal.notes
    )


@router.get("/", response_model=List[MealLog])
async def get_meal_logs(
    user_id: str = "demo_user",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    meal_type: Optional[MealType] = None,
    limit: int = 50
):
    """
    Get meal logs with optional filtering
    """
    meals = await MealService.get_meal_logs(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        meal_type=meal_type.value if meal_type else None,
        limit=limit
    )

    # Convert to response format
    result = []
    for m in meals:
        foods = m.get("foods", [])
        result.append(MealLog(
            id=m["_id"],
            user_id=m["user_id"],
            timestamp=m["timestamp"],
            meal_type=MealType(m["meal_type"]),
            food_items=[f.get("name", "") for f in foods],
            calories=m.get("nutrition_totals", {}).get("calories"),
            protein_g=m.get("nutrition_totals", {}).get("protein_g"),
            carbs_g=m.get("nutrition_totals", {}).get("carbs_g"),
            fat_g=m.get("nutrition_totals", {}).get("fat_g"),
            fiber_g=m.get("nutrition_totals", {}).get("fiber_g"),
            notes=m.get("notes")
        ))

    return result


@router.get("/summary/{date}", response_model=NutritionalSummary)
async def get_daily_nutrition_summary(
    date: date,
    user_id: str = "demo_user"
):
    """
    Get nutritional summary for a specific date
    """
    summary = await MealService.get_nutrition_summary(
        user_id=user_id,
        start_date=date,
        days=1
    )

    totals = summary.get("totals", {})
    insights = summary.get("insights", [])

    return NutritionalSummary(
        date=date,
        total_calories=int(totals.get("calories", 0)),
        protein_g=totals.get("protein_g", 0),
        carbs_g=totals.get("carbs_g", 0),
        fat_g=totals.get("fat_g", 0),
        fiber_g=totals.get("fiber_g", 0),
        meals_logged=summary.get("total_meals", 0),
        recommendations=insights if insights else ["Log more meals to get insights!"]
    )


@router.get("/trends")
async def get_nutrition_trends(
    user_id: str = "demo_user",
    days: int = 7
):
    """
    Get nutrition trends over time
    """
    analysis = await MealService.analyze_dietary_patterns(
        user_id=user_id,
        days=days
    )

    summary = analysis.get("summary", {})
    daily_avg = summary.get("daily_averages", {})
    insights = analysis.get("insights", [])

    return {
        "period_days": days,
        "average_daily_calories": daily_avg.get("calories", 0),
        "average_protein_g": daily_avg.get("protein_g", 0),
        "average_carbs_g": daily_avg.get("carbs_g", 0),
        "average_fat_g": daily_avg.get("fat_g", 0),
        "macronutrient_balance": analysis.get("macronutrient_balance"),
        "recommendations": insights,
        "total_meals_logged": summary.get("total_meals", 0)
    }
