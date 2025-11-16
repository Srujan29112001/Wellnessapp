"""
Life Optimization API Routes.

FastAPI routes for personalized meal plans and daily schedules.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field

from backend.models.life_optimization_models import (
    ComprehensiveUserProfile,
    DailyMealPlan,
    WeeklyMealPlan,
    DailySchedule
)
from backend.services.nutritional_calculator import (
    get_nutritional_calculator,
    DailyNutritionRequirements
)
from backend.services.global_food_database import get_food_database, FoodCategory
from backend.services.meal_plan_optimizer import get_meal_optimizer
from backend.services.schedule_optimizer import get_schedule_optimizer
from backend.services.currency_location_service import get_currency_service
from backend.services.natal_chart_service import get_natal_chart_service
from backend.services.shopping_list_service import (
    get_shopping_list_generator,
    ShoppingList,
    ShoppingListItem
)
from backend.services.pdf_export_service import get_pdf_service


# Initialize router
router = APIRouter(
    prefix="/api/v1/life-optimization",
    tags=["Life Optimization"]
)


# Request/Response Models
class ProfileCreateRequest(BaseModel):
    """Request to create/update user profile."""
    profile: ComprehensiveUserProfile


class ProfileResponse(BaseModel):
    """Profile response."""
    success: bool
    profile: ComprehensiveUserProfile
    message: str


class NutritionRequirementsResponse(BaseModel):
    """Nutrition requirements response."""
    user_id: str
    requirements: dict  # DailyNutritionRequirements as dict
    calculation_notes: List[str]


class MealPlanGenerateRequest(BaseModel):
    """Request to generate meal plan."""
    user_id: str
    start_date: date
    num_days: int = Field(default=1, ge=1, le=7, description="Number of days (1-7)")
    regenerate: bool = Field(default=False, description="Force regenerate even if exists")


class MealPlanResponse(BaseModel):
    """Meal plan response."""
    success: bool
    meal_plan: DailyMealPlan
    message: str


class WeeklyMealPlanResponse(BaseModel):
    """Weekly meal plan response."""
    success: bool
    weekly_plan: WeeklyMealPlan
    message: str


class ScheduleGenerateRequest(BaseModel):
    """Request to generate schedule."""
    user_id: str
    target_date: date
    include_planetary_hours: bool = Field(default=False)


class ScheduleResponse(BaseModel):
    """Schedule response."""
    success: bool
    schedule: DailySchedule
    message: str


class FoodSearchRequest(BaseModel):
    """Food database search."""
    category: Optional[FoodCategory] = None
    cuisine: Optional[str] = None
    dietary_flags: Optional[List[str]] = None
    exclude_allergens: Optional[List[str]] = None
    dosha_balance: Optional[str] = None
    max_price_usd: Optional[float] = None


# In-memory storage (replace with database in production)
user_profiles = {}
meal_plans = {}
schedules = {}


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.post("/profile", response_model=ProfileResponse)
async def create_or_update_profile(
    request: ProfileCreateRequest
):
    """
    Create or update user profile.

    This is the comprehensive assessment that captures all user data
    for personalized optimization.
    """
    try:
        profile = request.profile

        # Calculate derived data
        nutritional_calc = get_nutritional_calculator()
        nutrition_req = nutritional_calc.calculate_complete_requirements(profile)

        # Calculate natal chart if birth details provided
        if profile.birth_details:
            natal_service = get_natal_chart_service()
            natal_chart = natal_service.calculate_natal_chart(
                birth_date=datetime.combine(profile.birth_details.date, profile.birth_details.time),
                latitude=profile.birth_details.latitude,
                longitude=profile.birth_details.longitude,
                birth_place=profile.birth_details.place
            )
            profile.natal_chart_id = natal_chart.get("chart_id")

        # Detect location
        currency_service = get_currency_service()
        location = currency_service.detect_location_from_ip()
        profile.location_info = {
            "country": location.country,
            "country_code": location.country_code,
            "region": location.region,
            "city": location.city,
            "timezone": location.timezone,
            "currency": location.currency.code
        }

        # Store metabolic profile
        profile.metabolic_profile = {
            "bmr": nutrition_req.bmr,
            "tdee": nutrition_req.tdee,
            "target_calories": nutrition_req.target_calories,
            "protein_g": nutrition_req.protein_g,
            "carbs_g": nutrition_req.carbs_g,
            "fat_g": nutrition_req.fat_g
        }

        # Save profile
        user_profiles[profile.user_id] = profile

        return ProfileResponse(
            success=True,
            profile=profile,
            message=f"Profile {'updated' if profile.user_id in user_profiles else 'created'} successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """Get user profile by ID."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    return ProfileResponse(
        success=True,
        profile=user_profiles[user_id],
        message="Profile retrieved successfully"
    )


@router.get("/profile/{user_id}/nutrition-requirements", response_model=NutritionRequirementsResponse)
async def get_nutrition_requirements(user_id: str):
    """Get calculated nutrition requirements for user."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = user_profiles[user_id]

    nutritional_calc = get_nutritional_calculator()
    requirements = nutritional_calc.calculate_complete_requirements(profile)

    return NutritionRequirementsResponse(
        user_id=user_id,
        requirements={
            "bmr": requirements.bmr,
            "tdee": requirements.tdee,
            "target_calories": requirements.target_calories,
            "protein_g": requirements.protein_g,
            "carbs_g": requirements.carbs_g,
            "fat_g": requirements.fat_g,
            "fiber_g": requirements.fiber_g,
            "protein_percent": requirements.protein_percent,
            "carbs_percent": requirements.carbs_percent,
            "fat_percent": requirements.fat_percent,
            "water_ml": requirements.water_ml,
            "meal_frequency": requirements.meal_frequency,
            "dosha_guidelines": requirements.dosha_dietary_guidelines
        },
        calculation_notes=requirements.calculation_notes
    )


# ============================================================================
# MEAL PLAN ENDPOINTS
# ============================================================================

@router.post("/meal-plan/generate", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanGenerateRequest):
    """
    Generate personalized meal plan for a day.

    Takes all user profile data into account:
    - Nutritional requirements
    - Budget constraints
    - Dosha balance
    - Food preferences/allergies
    - Regional pricing
    - Cooking time available
    """
    if request.user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        profile = user_profiles[request.user_id]

        # Get location for pricing
        currency_service = get_currency_service()
        if profile.location_info:
            location = currency_service.detect_location_from_ip()
        else:
            location = currency_service.detect_location_from_ip()

        # Generate meal plan
        meal_optimizer = get_meal_optimizer()
        meal_plan = meal_optimizer.generate_daily_meal_plan(
            profile=profile,
            target_date=request.start_date,
            location=location
        )

        # Store meal plan
        meal_plans[f"{request.user_id}_{request.start_date}"] = meal_plan

        return MealPlanResponse(
            success=True,
            meal_plan=meal_plan,
            message=f"Meal plan generated for {request.start_date}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating meal plan: {str(e)}")


@router.get("/meal-plan/{user_id}/current", response_model=MealPlanResponse)
async def get_current_meal_plan(user_id: str):
    """Get meal plan for today."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    today = date.today()
    key = f"{user_id}_{today}"

    if key not in meal_plans:
        # Auto-generate if not exists
        profile = user_profiles[user_id]
        currency_service = get_currency_service()
        location = currency_service.detect_location_from_ip()

        meal_optimizer = get_meal_optimizer()
        meal_plan = meal_optimizer.generate_daily_meal_plan(
            profile=profile,
            target_date=today,
            location=location
        )
        meal_plans[key] = meal_plan

    return MealPlanResponse(
        success=True,
        meal_plan=meal_plans[key],
        message=f"Current meal plan for {today}"
    )


@router.post("/meal-plan/{user_id}/regenerate")
async def regenerate_meal_plan(
    user_id: str,
    target_date: date = Body(default=None)
):
    """
    Regenerate meal plan for a specific date.

    Useful for daily variety - user can regenerate until satisfied.
    """
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    if target_date is None:
        target_date = date.today()

    try:
        profile = user_profiles[user_id]
        currency_service = get_currency_service()
        location = currency_service.detect_location_from_ip()

        meal_optimizer = get_meal_optimizer()
        meal_plan = meal_optimizer.generate_daily_meal_plan(
            profile=profile,
            target_date=target_date,
            location=location
        )

        # Store new plan
        key = f"{user_id}_{target_date}"
        meal_plans[key] = meal_plan

        return MealPlanResponse(
            success=True,
            meal_plan=meal_plan,
            message=f"Meal plan regenerated for {target_date}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating meal plan: {str(e)}")


@router.get("/meal-plan/{user_id}/date/{target_date}", response_model=MealPlanResponse)
async def get_meal_plan_by_date(user_id: str, target_date: date):
    """Get meal plan for specific date."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    key = f"{user_id}_{target_date}"

    if key not in meal_plans:
        raise HTTPException(status_code=404, detail=f"No meal plan found for {target_date}")

    return MealPlanResponse(
        success=True,
        meal_plan=meal_plans[key],
        message=f"Meal plan for {target_date}"
    )


# ============================================================================
# SCHEDULE ENDPOINTS
# ============================================================================

@router.post("/schedule/generate", response_model=ScheduleResponse)
async def generate_schedule(request: ScheduleGenerateRequest):
    """
    Generate optimized daily schedule.

    Considers:
    - Chronotype (early bird/night owl)
    - Energy patterns
    - Dosha cycles
    - Work commitments
    - Meal timing (from meal plan)
    - Exercise and meditation goals
    - Planetary hours (optional)
    """
    if request.user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        profile = user_profiles[request.user_id]

        # Get meal plan for the day if exists
        meal_plan_key = f"{request.user_id}_{request.target_date}"
        meal_plan = meal_plans.get(meal_plan_key)

        # Generate schedule
        schedule_optimizer = get_schedule_optimizer()
        schedule = schedule_optimizer.generate_daily_schedule(
            profile=profile,
            target_date=request.target_date,
            meal_plan=meal_plan,
            include_planetary_hours=request.include_planetary_hours
        )

        # Store schedule
        schedules[f"{request.user_id}_{request.target_date}"] = schedule

        return ScheduleResponse(
            success=True,
            schedule=schedule,
            message=f"Schedule generated for {request.target_date}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating schedule: {str(e)}")


@router.get("/schedule/{user_id}/today", response_model=ScheduleResponse)
async def get_today_schedule(user_id: str):
    """Get optimized schedule for today."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    today = date.today()
    key = f"{user_id}_{today}"

    if key not in schedules:
        # Auto-generate
        profile = user_profiles[user_id]
        meal_plan_key = f"{user_id}_{today}"
        meal_plan = meal_plans.get(meal_plan_key)

        schedule_optimizer = get_schedule_optimizer()
        schedule = schedule_optimizer.generate_daily_schedule(
            profile=profile,
            target_date=today,
            meal_plan=meal_plan
        )
        schedules[key] = schedule

    return ScheduleResponse(
        success=True,
        schedule=schedules[key],
        message=f"Today's schedule"
    )


@router.get("/schedule/{user_id}/date/{target_date}", response_model=ScheduleResponse)
async def get_schedule_by_date(user_id: str, target_date: date):
    """Get schedule for specific date."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    key = f"{user_id}_{target_date}"

    if key not in schedules:
        raise HTTPException(status_code=404, detail=f"No schedule found for {target_date}")

    return ScheduleResponse(
        success=True,
        schedule=schedules[key],
        message=f"Schedule for {target_date}"
    )


# ============================================================================
# FOOD DATABASE ENDPOINTS
# ============================================================================

@router.post("/food/search")
async def search_foods(request: FoodSearchRequest):
    """
    Search global food database.

    Filter by category, cuisine, dietary requirements, allergens, dosha, price.
    """
    food_db = get_food_database()

    try:
        results = food_db.search_foods(
            category=request.category,
            cuisine=request.cuisine,
            dietary_flags=request.dietary_flags,
            exclude_allergens=request.exclude_allergens,
            dosha_balance=request.dosha_balance,
            max_price_usd=request.max_price_usd
        )

        # Convert to dict for JSON response
        food_list = [
            {
                "food_id": food.food_id,
                "name": food.name,
                "category": food.category.value,
                "cuisines": food.cuisines,
                "nutrition": {
                    "calories": food.nutrition.calories,
                    "protein_g": food.nutrition.protein_g,
                    "carbs_g": food.nutrition.carbs_g,
                    "fat_g": food.nutrition.fat_g,
                    "fiber_g": food.nutrition.fiber_g
                },
                "base_price_usd_per_kg": food.base_price_usd_per_kg,
                "dietary_flags": food.dietary_flags,
                "allergens": food.allergens
            }
            for food in results
        ]

        return {
            "success": True,
            "count": len(food_list),
            "foods": food_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching foods: {str(e)}")


@router.get("/food/{food_id}")
async def get_food_details(food_id: str):
    """Get detailed food information."""
    food_db = get_food_database()
    food = food_db.get_food(food_id)

    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    return {
        "success": True,
        "food": {
            "food_id": food.food_id,
            "name": food.name,
            "local_names": food.local_names,
            "category": food.category.value,
            "cuisines": food.cuisines,
            "description": food.description,
            "nutrition": {
                "calories": food.nutrition.calories,
                "protein_g": food.nutrition.protein_g,
                "carbs_g": food.nutrition.carbs_g,
                "fat_g": food.nutrition.fat_g,
                "fiber_g": food.nutrition.fiber_g,
                "vitamin_a_mcg": food.nutrition.vitamin_a_mcg,
                "vitamin_c_mg": food.nutrition.vitamin_c_mg,
                "iron_mg": food.nutrition.iron_mg,
                "calcium_mg": food.nutrition.calcium_mg
            },
            "ayurvedic": {
                "rasa": food.ayurvedic.rasa,
                "virya": food.ayurvedic.virya,
                "vipaka": food.ayurvedic.vipaka,
                "dosha_effect": food.ayurvedic.dosha_effect,
                "qualities": food.ayurvedic.qualities
            },
            "regional_prices": [
                {
                    "country_code": p.country_code,
                    "region": p.region,
                    "price_per_kg": p.price_per_kg,
                    "currency": p.currency,
                    "availability": p.availability
                }
                for p in food.regional_prices
            ],
            "base_price_usd_per_kg": food.base_price_usd_per_kg,
            "allergens": food.allergens,
            "dietary_flags": food.dietary_flags,
            "common_preparations": food.common_preparations
        }
    }


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/currency/detect-location")
async def detect_user_location():
    """Auto-detect user location from IP for pricing."""
    currency_service = get_currency_service()
    location = currency_service.detect_location_from_ip()

    return {
        "success": True,
        "location": {
            "country": location.country,
            "country_code": location.country_code,
            "region": location.region,
            "city": location.city,
            "timezone": location.timezone,
            "currency": {
                "code": location.currency.code,
                "symbol": location.currency.symbol,
                "name": location.currency.name
            }
        }
    }


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get user statistics and compliance."""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = user_profiles[user_id]

    # Count meal plans
    user_meal_plans = {k: v for k, v in meal_plans.items() if k.startswith(user_id)}

    # Average compliance
    total_plans = len(user_meal_plans)
    budget_compliant = sum(1 for p in user_meal_plans.values() if p.meets_budget)
    goals_compliant = sum(1 for p in user_meal_plans.values() if p.meets_goals)

    avg_dosha_score = sum(p.dosha_balance_score for p in user_meal_plans.values()) / total_plans if total_plans > 0 else 0

    return {
        "success": True,
        "user_id": user_id,
        "stats": {
            "total_meal_plans_generated": total_plans,
            "budget_compliance_rate": budget_compliant / total_plans if total_plans > 0 else 0,
            "nutrition_compliance_rate": goals_compliant / total_plans if total_plans > 0 else 0,
            "average_dosha_balance_score": round(avg_dosha_score, 1),
            "primary_goal": profile.goals.primary_goal.value,
            "dosha_type": profile.personality.dosha_type
        }
    }


# ============================================================================
# SHOPPING LIST ENDPOINTS
# ============================================================================

class ShoppingListRequest(BaseModel):
    """Request to generate shopping list"""
    user_id: str
    start_date: date
    end_date: date


class ShoppingListResponse(BaseModel):
    """Shopping list response"""
    success: bool
    shopping_list: ShoppingList
    message: str


# In-memory storage for shopping lists
shopping_lists: Dict[str, ShoppingList] = {}


@router.post("/shopping-list/generate", response_model=ShoppingListResponse)
async def generate_shopping_list(request: ShoppingListRequest):
    """
    Generate shopping list from meal plans.

    Aggregates ingredients from all meal plans between start_date and end_date,
    groups by category, calculates total quantities, and estimates costs.
    """
    if request.user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        # Get all meal plans in date range
        meal_plan_list = []
        current_date = request.start_date

        while current_date <= request.end_date:
            key = f"{request.user_id}_{current_date}"
            if key in meal_plans:
                meal_plan_list.append(meal_plans[key])
            current_date += timedelta(days=1)

        if not meal_plan_list:
            raise HTTPException(
                status_code=404,
                detail=f"No meal plans found between {request.start_date} and {request.end_date}"
            )

        # Generate shopping list
        currency_service = get_currency_service()
        location = currency_service.detect_location_from_ip()

        shopping_gen = get_shopping_list_generator()
        shopping_list = shopping_gen.generate_shopping_list(
            meal_plans=meal_plan_list,
            user_id=request.user_id,
            location=location
        )

        # Store shopping list
        list_key = f"{request.user_id}_{request.start_date}_{request.end_date}"
        shopping_lists[list_key] = shopping_list

        return ShoppingListResponse(
            success=True,
            shopping_list=shopping_list,
            message=f"Shopping list generated for {len(meal_plan_list)} days"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating shopping list: {str(e)}")


@router.get("/shopping-list/{user_id}/current", response_model=ShoppingListResponse)
async def get_current_shopping_list(user_id: str):
    """Get shopping list for current week"""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    list_key = f"{user_id}_{start_of_week}_{end_of_week}"

    if list_key not in shopping_lists:
        # Auto-generate if not exists
        try:
            request = ShoppingListRequest(
                user_id=user_id,
                start_date=start_of_week,
                end_date=end_of_week
            )
            return await generate_shopping_list(request)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"No shopping list found and could not generate: {str(e)}")

    return ShoppingListResponse(
        success=True,
        shopping_list=shopping_lists[list_key],
        message=f"Current week shopping list ({start_of_week} to {end_of_week})"
    )


@router.get("/shopping-list/{user_id}/date-range")
async def get_shopping_list_by_range(
    user_id: str,
    start_date: date,
    end_date: date
):
    """Get shopping list for specific date range"""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    list_key = f"{user_id}_{start_date}_{end_date}"

    if list_key not in shopping_lists:
        raise HTTPException(status_code=404, detail=f"No shopping list found for date range")

    return ShoppingListResponse(
        success=True,
        shopping_list=shopping_lists[list_key],
        message=f"Shopping list for {start_date} to {end_date}"
    )


# ============================================================================
# PDF EXPORT ENDPOINTS
# ============================================================================

from fastapi.responses import StreamingResponse


@router.get("/pdf/meal-plan/{user_id}/date/{target_date}")
async def export_meal_plan_pdf(user_id: str, target_date: date):
    """Export meal plan as PDF"""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    key = f"{user_id}_{target_date}"

    if key not in meal_plans:
        raise HTTPException(status_code=404, detail=f"No meal plan found for {target_date}")

    try:
        pdf_service = get_pdf_service()
        profile = user_profiles.get(user_id)

        pdf_buffer = pdf_service.generate_meal_plan_pdf(
            meal_plan=meal_plans[key],
            profile=profile
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=meal_plan_{target_date}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@router.get("/pdf/shopping-list/{user_id}/current")
async def export_shopping_list_pdf(user_id: str):
    """Export current week shopping list as PDF"""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get current week shopping list
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    list_key = f"{user_id}_{start_of_week}_{end_of_week}"

    if list_key not in shopping_lists:
        raise HTTPException(status_code=404, detail="No shopping list found")

    try:
        pdf_service = get_pdf_service()

        pdf_buffer = pdf_service.generate_shopping_list_pdf(
            shopping_list=shopping_lists[list_key]
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=shopping_list_{start_of_week}_to_{end_of_week}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@router.get("/pdf/schedule/{user_id}/date/{target_date}")
async def export_schedule_pdf(user_id: str, target_date: date):
    """Export daily schedule as PDF"""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    key = f"{user_id}_{target_date}"

    if key not in schedules:
        raise HTTPException(status_code=404, detail=f"No schedule found for {target_date}")

    try:
        pdf_service = get_pdf_service()

        pdf_buffer = pdf_service.generate_schedule_pdf(
            schedule=schedules[key]
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=schedule_{target_date}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@router.get("/pdf/wellness-report/{user_id}")
async def export_wellness_report_pdf(user_id: str):
    """Export comprehensive wellness report as PDF"""
    if user_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        profile = user_profiles[user_id]

        # Mock wellness scores (in production, fetch from database)
        wellness_scores = {
            'physical': 75,
            'mental': 72,
            'emotional': 78,
            'spiritual': 68,
            'nutritional': 80,
            'overall': 74
        }

        recent_data = {
            'Sleep Average (7 days)': '7.2 hours',
            'Exercise Frequency': '5 days/week',
            'Meditation': '20 min/day',
            'Stress Level': 'Moderate',
            'Meal Plan Adherence': '85%'
        }

        pdf_service = get_pdf_service()

        pdf_buffer = pdf_service.generate_wellness_report_pdf(
            user_id=user_id,
            profile=profile,
            wellness_scores=wellness_scores,
            recent_data=recent_data
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=wellness_report_{user_id}_{date.today()}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
