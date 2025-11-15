"""
GraphQL Schema Definitions
"""
import strawberry
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


# Types
@strawberry.type
class HealthMetric:
    """Daily health metrics"""
    id: str
    user_id: str
    date: datetime
    steps: Optional[int] = None
    calories_burned: Optional[int] = None
    distance_km: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight_kg: Optional[float] = None
    stress_level: Optional[float] = None  # 0-1 from EEG
    focus_level: Optional[float] = None   # 0-1 from EEG


@strawberry.type
class EEGAnalysis:
    """EEG signal analysis results"""
    id: str
    user_id: str
    timestamp: datetime
    stress: float
    focus: float
    relaxation: float
    drowsiness: float
    dominant_band: str  # delta, theta, alpha, beta
    mental_state: str   # stressed, focused, relaxed, drowsy


@strawberry.type
class MealLog:
    """Meal logging entry"""
    id: str
    user_id: str
    timestamp: datetime
    meal_type: str  # breakfast, lunch, dinner, snack
    food_items: List[str]
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    image_url: Optional[str] = None


@strawberry.type
class Recommendation:
    """Personalized recommendation"""
    id: str
    user_id: str
    timestamp: datetime
    category: str  # diet, supplement, lifestyle, exercise
    title: str
    description: str
    reasoning: str
    evidence: List[str]  # Citations/sources
    priority: str  # high, medium, low


@strawberry.type
class ChatMessage:
    """Coach chat message"""
    id: str
    user_id: str
    timestamp: datetime
    role: str  # user, assistant
    content: str
    context: Optional[str] = None  # Additional context used


@strawberry.type
class UserProfile:
    """User profile"""
    id: str
    email: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    dosha_type: Optional[str] = None  # vata, pitta, kapha
    health_goals: List[str]
    dietary_restrictions: List[str]
    medical_conditions: List[str]
    created_at: datetime


# Input Types
@strawberry.input
class HealthMetricInput:
    """Input for creating/updating health metrics"""
    date: datetime
    steps: Optional[int] = None
    calories_burned: Optional[int] = None
    distance_km: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight_kg: Optional[float] = None


@strawberry.input
class MealLogInput:
    """Input for logging a meal"""
    meal_type: str
    food_items: List[str]
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    image_url: Optional[str] = None


@strawberry.input
class ChatMessageInput:
    """Input for chat message"""
    content: str


# Query
@strawberry.type
class Query:
    """GraphQL Query Root"""

    @strawberry.field
    async def health_metrics(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HealthMetric]:
        """Get health metrics for a user within date range"""
        # TODO: Implement database query
        return []

    @strawberry.field
    async def eeg_analysis(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[EEGAnalysis]:
        """Get recent EEG analysis results"""
        # TODO: Implement database query
        return []

    @strawberry.field
    async def meal_logs(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MealLog]:
        """Get meal logs for a user"""
        # TODO: Implement database query
        return []

    @strawberry.field
    async def recommendations(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> List[Recommendation]:
        """Get personalized recommendations"""
        # TODO: Implement recommendation service
        return []

    @strawberry.field
    async def chat_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get chat history with AI coach"""
        # TODO: Implement database query
        return []

    @strawberry.field
    async def user_profile(
        self,
        user_id: str
    ) -> Optional[UserProfile]:
        """Get user profile"""
        # TODO: Implement database query
        return None


# Mutation
@strawberry.type
class Mutation:
    """GraphQL Mutation Root"""

    @strawberry.mutation
    async def log_health_metrics(
        self,
        user_id: str,
        metrics: HealthMetricInput
    ) -> HealthMetric:
        """Log daily health metrics"""
        # TODO: Implement database insert
        return HealthMetric(
            id="temp_id",
            user_id=user_id,
            date=metrics.date,
            steps=metrics.steps,
            calories_burned=metrics.calories_burned,
            distance_km=metrics.distance_km,
            heart_rate_avg=metrics.heart_rate_avg,
            sleep_hours=metrics.sleep_hours,
            weight_kg=metrics.weight_kg
        )

    @strawberry.mutation
    async def log_meal(
        self,
        user_id: str,
        meal: MealLogInput
    ) -> MealLog:
        """Log a meal"""
        # TODO: Implement database insert
        return MealLog(
            id="temp_id",
            user_id=user_id,
            timestamp=datetime.now(),
            meal_type=meal.meal_type,
            food_items=meal.food_items,
            calories=meal.calories,
            protein_g=meal.protein_g,
            carbs_g=meal.carbs_g,
            fat_g=meal.fat_g,
            image_url=meal.image_url
        )

    @strawberry.mutation
    async def chat_with_coach(
        self,
        user_id: str,
        message: ChatMessageInput
    ) -> ChatMessage:
        """Send message to AI wellness coach"""
        # TODO: Implement coach service
        return ChatMessage(
            id="temp_id",
            user_id=user_id,
            timestamp=datetime.now(),
            role="assistant",
            content="This is a placeholder response. The coach will be implemented soon."
        )

    @strawberry.mutation
    async def upload_eeg_data(
        self,
        user_id: str,
        file_url: str
    ) -> EEGAnalysis:
        """Upload and analyze EEG data"""
        # TODO: Implement EEG analysis service
        return EEGAnalysis(
            id="temp_id",
            user_id=user_id,
            timestamp=datetime.now(),
            stress=0.5,
            focus=0.5,
            relaxation=0.5,
            drowsiness=0.5,
            dominant_band="alpha",
            mental_state="relaxed"
        )
