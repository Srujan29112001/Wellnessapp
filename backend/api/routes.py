"""
REST API Routes
"""
from fastapi import APIRouter

from backend.api.endpoints import (
    health,
    eeg,
    voice,
    food,
    coach,
    recommendations,
    users,
    meals,
    supplements,
    auth,
    life_optimization
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health.router, prefix="/health", tags=["Health Metrics"])
api_router.include_router(eeg.router, prefix="/eeg", tags=["EEG Analysis"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice Analysis"])
api_router.include_router(food.router, prefix="/food", tags=["Food Recognition"])
api_router.include_router(coach.router, prefix="/coach", tags=["AI Coach"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(meals.router, prefix="/meals", tags=["Meals & Diet"])
api_router.include_router(supplements.router, prefix="/supplements", tags=["Supplements"])
api_router.include_router(life_optimization.router, tags=["Life Optimization"])
