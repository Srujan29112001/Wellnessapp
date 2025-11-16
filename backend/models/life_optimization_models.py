"""
Data models for Life Optimization System.

Comprehensive user profile for personalized meal plans and schedules.
"""

from datetime import datetime, time, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class DietType(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    PESCATARIAN = "pescatarian"
    NON_VEGETARIAN = "non_vegetarian"
    KETO = "keto"
    PALEO = "paleo"


class GoalType(str, Enum):
    PHYSICAL_STRENGTH = "physical_strength"
    MENTAL_STRENGTH = "mental_strength"
    SPIRITUAL_STRENGTH = "spiritual_strength"
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    FLEXIBILITY = "flexibility"
    ENDURANCE = "endurance"
    LONGEVITY = "longevity"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"  # Little to no exercise
    LIGHT = "light_active"  # 1-3 days/week
    MODERATE = "moderate_active"  # 3-5 days/week
    VERY_ACTIVE = "very_active"  # 6-7 days/week
    EXTREMELY_ACTIVE = "extremely_active"  # Physical job + exercise


class ChronotypeEnum(str, Enum):
    EARLY_BIRD = "early_bird"  # Morning person
    NIGHT_OWL = "night_owl"  # Evening person
    INTERMEDIATE = "intermediate"  # Flexible


class CookingSkill(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Profile Models
class BirthDetails(BaseModel):
    """Birth details for astrological calculations."""
    date: date
    time: time
    place: str
    latitude: float
    longitude: float
    timezone: str


class PersonalityProfile(BaseModel):
    """Personality assessment results."""
    big_five: Dict[str, float] = Field(
        description="Big Five traits (0-1 scale): openness, conscientiousness, extraversion, agreeableness, neuroticism"
    )
    chronotype: ChronotypeEnum
    dosha_type: str = Field(description="Vata, Pitta, Kapha, or combinations")
    dosha_percentages: Dict[str, int] = Field(description="Vata, Pitta, Kapha percentages")


class PhysicalProfile(BaseModel):
    """Physical characteristics and measurements."""
    age: int = Field(ge=1, le=120)
    gender: str = Field(description="male, female, other")
    height_cm: float = Field(ge=50, le=300)
    weight_kg: float = Field(ge=20, le=500)
    body_fat_percent: Optional[float] = Field(None, ge=3, le=60)
    activity_level: ActivityLevel

    # Calculated fields
    bmi: Optional[float] = None
    bmr: Optional[float] = None  # Basal Metabolic Rate
    tdee: Optional[float] = None  # Total Daily Energy Expenditure

    @validator('bmi', always=True)
    def calculate_bmi(cls, v, values):
        if 'height_cm' in values and 'weight_kg' in values:
            height_m = values['height_cm'] / 100
            return round(values['weight_kg'] / (height_m ** 2), 1)
        return v


class HealthProfile(BaseModel):
    """Medical history and health conditions."""
    conditions: List[str] = Field(default_factory=list, description="e.g., diabetes, hypertension")
    allergies: List[str] = Field(default_factory=list, description="Food allergies")
    medications: List[str] = Field(default_factory=list)
    nutrient_deficiencies: List[str] = Field(default_factory=list, description="e.g., vitamin_d, iron")
    digestive_issues: List[str] = Field(default_factory=list)
    family_history: List[str] = Field(default_factory=list)


class DietaryPreferences(BaseModel):
    """Dietary preferences and constraints."""
    diet_type: DietType
    cuisine_preferences: List[str] = Field(description="e.g., indian, italian, mexican")
    disliked_foods: List[str] = Field(default_factory=list)
    favorite_foods: List[str] = Field(default_factory=list)
    budget_per_week: float = Field(description="Weekly food budget in user's currency")
    budget_currency: str = Field(default="USD")
    cooking_skill: CookingSkill
    cooking_time_available: int = Field(description="Minutes available for meal prep per meal")
    meal_prep_preference: str = Field(description="daily, batch_cooking, mix")
    eating_out_frequency: int = Field(default=0, description="Times per week")


class LifestyleProfile(BaseModel):
    """Lifestyle and daily routine information."""
    region: str = Field(description="City, State/Province, Country")
    country_code: str = Field(description="ISO country code")
    timezone: str
    occupation: str
    work_schedule_type: str = Field(description="fixed, flexible, shift_work, remote")
    typical_work_hours: str = Field(description="e.g., 9:00-17:00")
    work_break_preferences: List[str] = Field(default_factory=list)
    commute_time_minutes: int = Field(default=0)
    household_size: int = Field(default=1)
    has_family_meals: bool = Field(default=False)


class SleepPreferences(BaseModel):
    """Sleep habits and preferences."""
    ideal_sleep_duration: float = Field(ge=4, le=12, description="Hours")
    preferred_bedtime: time
    preferred_wake_time: time
    current_sleep_quality: int = Field(ge=1, le=10, description="1=poor, 10=excellent")
    sleep_issues: List[str] = Field(default_factory=list, description="e.g., insomnia, sleep_apnea")


class WellnessGoals(BaseModel):
    """User's wellness and fitness goals."""
    primary_goal: GoalType
    secondary_goals: List[GoalType] = Field(default_factory=list)
    timeline: str = Field(description="1_month, 3_months, 6_months, 1_year")
    urgency: str = Field(description="gradual, balanced, aggressive")

    # Specific targets
    target_weight_kg: Optional[float] = None
    target_body_fat_percent: Optional[float] = None
    meditation_minutes_daily: int = Field(default=0)
    exercise_minutes_daily: int = Field(default=0)

    # Priority weighting (0-10 scale)
    priority_nutrition: int = Field(default=8, ge=0, le=10)
    priority_exercise: int = Field(default=7, ge=0, le=10)
    priority_sleep: int = Field(default=8, ge=0, le=10)
    priority_stress: int = Field(default=7, ge=0, le=10)
    priority_spiritual: int = Field(default=5, ge=0, le=10)
    priority_budget: int = Field(default=6, ge=0, le=10)


class CustomPreferences(BaseModel):
    """Additional custom preferences."""
    intermittent_fasting: bool = Field(default=False)
    fasting_window: Optional[str] = Field(None, description="e.g., 16:8, 18:6")
    caffeine_preference: str = Field(default="moderate", description="none, low, moderate, high")
    alcohol_consumption: str = Field(default="none", description="none, occasional, moderate, frequent")
    supplement_stack: List[str] = Field(default_factory=list)
    exercise_preferences: List[str] = Field(default_factory=list, description="e.g., yoga, running, gym")
    spiritual_practices: List[str] = Field(default_factory=list, description="e.g., meditation, prayer, journaling")
    notes: str = Field(default="", description="Any additional notes or requirements")


class ComprehensiveUserProfile(BaseModel):
    """Complete user profile for life optimization."""
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Profile sections
    birth_details: BirthDetails
    personality: PersonalityProfile
    physical: PhysicalProfile
    health: HealthProfile
    dietary_preferences: DietaryPreferences
    lifestyle: LifestyleProfile
    sleep_preferences: SleepPreferences
    goals: WellnessGoals
    custom_preferences: CustomPreferences

    # Calculated/derived data
    natal_chart_id: Optional[str] = None
    metabolic_profile: Optional[Dict] = None
    location_info: Optional[Dict] = None


# Meal Plan Models
class NutrientInfo(BaseModel):
    """Nutritional information."""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None

    # Micronutrients (optional)
    vitamin_a_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None


class FoodIngredient(BaseModel):
    """Individual food ingredient."""
    name: str
    quantity: float
    unit: str  # g, ml, piece, cup, tbsp
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    cost_local: float
    cost_currency: str
    reason: str = Field(description="Why this ingredient (dosha, goal, health)")
    alternatives: List[Dict[str, str]] = Field(default_factory=list)


class AyurvedicProperties(BaseModel):
    """Ayurvedic properties of food."""
    rasa: List[str] = Field(description="Tastes: sweet, sour, salty, bitter, pungent, astringent")
    virya: str = Field(description="Heating or cooling")
    vipaka: str = Field(description="Post-digestive effect")
    dosha_effect: str = Field(description="Effect on doshas")
    qualities: List[str] = Field(default_factory=list, description="Heavy, light, oily, dry, etc.")


class Meal(BaseModel):
    """Single meal definition."""
    meal_id: str
    day: str  # monday, tuesday, etc.
    meal_type: str  # breakfast, lunch, dinner, snack
    time: time
    name: str
    description: Optional[str] = None

    ingredients: List[FoodIngredient]
    cooking_instructions: List[str] = Field(description="Step-by-step cooking")
    prep_time_minutes: int
    cooking_method: str = Field(description="e.g., boiled, steamed, raw, baked")

    total_nutrients: NutrientInfo
    ayurvedic_properties: AyurvedicProperties

    cost_total: float
    cost_currency: str

    # Metadata
    suitable_for: List[str] = Field(description="vegan, gluten_free, etc.")
    avoid_if: List[str] = Field(default_factory=list, description="Allergies/conditions to avoid")
    timing_reason: str = Field(description="Why this meal at this time")


class DailyMealPlan(BaseModel):
    """Complete meal plan for one day."""
    date: date
    user_id: str

    meals: List[Meal]

    # Daily totals
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    total_cost: float
    cost_currency: str

    # Hydration
    water_ml: int
    hydration_schedule: List[Dict[str, Any]] = Field(description="Time and quantity for water intake")

    # Ayurvedic balance
    dosha_balance_score: float = Field(ge=0, le=100)

    # Compliance
    meets_goals: bool
    meets_budget: bool
    nutrient_gaps: List[str] = Field(default_factory=list)


class WeeklyMealPlan(BaseModel):
    """Complete meal plan for one week."""
    week_start: date
    user_id: str

    daily_plans: List[DailyMealPlan]

    # Weekly summary
    total_cost: float
    cost_currency: str
    avg_daily_calories: float

    shopping_list: Dict[str, List[Dict]] = Field(description="Organized by category")
    meal_prep_schedule: Dict[str, List[str]] = Field(description="When to prep what")

    # Variety metrics
    unique_ingredients: int
    recipe_variety_score: float = Field(ge=0, le=100)

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Schedule Models
class ScheduleActivity(BaseModel):
    """Single activity in daily schedule."""
    time: time
    duration_minutes: int
    activity_type: str  # wake_up, meditation, exercise, work, meal, etc.
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    energy_required: str = Field(description="low, moderate, high")
    priority: int = Field(ge=1, le=10)
    reason: str = Field(description="Why this activity at this time")

    # Links
    meal_id: Optional[str] = None
    related_goal: Optional[str] = None


class DailySchedule(BaseModel):
    """Optimized daily schedule."""
    date: date
    user_id: str

    activities: List[ScheduleActivity]

    # Summary
    sleep_hours: float
    work_hours: float
    exercise_minutes: int
    spiritual_practice_minutes: int
    meal_count: int
    free_time_minutes: int

    # Energy forecast
    energy_forecast: Dict[str, str] = Field(description="morning, afternoon, evening energy levels")

    # Planetary influences (optional)
    planetary_guidance: Optional[List[str]] = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Progress Tracking
class DailyAdherence(BaseModel):
    """Track adherence to plan."""
    date: date
    user_id: str

    meals_followed: int
    meals_total: int
    schedule_adherence_percent: float

    feedback: Optional[str] = None
    energy_level: int = Field(ge=1, le=10)
    mood: int = Field(ge=1, le=10)
    stress_level: int = Field(ge=1, le=10)

    adjustments_needed: List[str] = Field(default_factory=list)
