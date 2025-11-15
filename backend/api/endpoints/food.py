"""
Food Recognition Endpoints
"""
from fastapi import APIRouter, UploadFile, File
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


# Schemas
class FoodItem(BaseModel):
    name: str
    confidence: float
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class FoodRecognitionResponse(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    detected_foods: List[FoodItem]
    total_calories: int
    nutritional_summary: Dict[str, float]
    recommendations: List[str]


@router.post("/recognize", response_model=FoodRecognitionResponse)
async def recognize_food(
    file: UploadFile = File(...),
    user_id: str = "demo_user"
):
    """
    Recognize food items from image using ViT-DINO model

    Accepts: JPG, PNG image files
    """
    from backend.services.food_vision_service import get_food_service

    # Read file bytes
    file_bytes = await file.read()

    # Recognize food
    service = get_food_service()
    result = await service.recognize_food(file_bytes, user_id)

    return FoodRecognitionResponse(
        id=result["id"],
        user_id=result["user_id"],
        timestamp=result["timestamp"],
        detected_foods=[FoodItem(**food) for food in result["detected_foods"]],
        total_calories=result["total_calories"],
        nutritional_summary=result["nutritional_summary"],
        recommendations=result["recommendations"]
    )


@router.post("/ocr-supplement", response_model=dict)
async def ocr_supplement_label(
    file: UploadFile = File(...),
    user_id: str = "demo_user"
):
    """
    Extract supplement information from label using OCR

    Accepts: JPG, PNG images of supplement bottles/labels
    """
    from backend.services.food_vision_service import get_food_service

    # Read file bytes
    file_bytes = await file.read()

    # Extract supplement info
    service = get_food_service()
    result = await service.ocr_supplement(file_bytes, user_id)

    # Convert datetime to string for JSON serialization
    if "timestamp" in result:
        result["timestamp"] = result["timestamp"].isoformat()

    return result
