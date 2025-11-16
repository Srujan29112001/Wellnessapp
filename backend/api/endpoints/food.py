"""
Food Recognition Endpoints
"""
from fastapi import APIRouter, UploadFile, File
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


# Schemas
from typing import Optional

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
    import tempfile
    import os
    from ml.food_recognition.recognizer import get_food_recognizer

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Recognize food
        recognizer = get_food_recognizer()
        result = recognizer.recognize(tmp_path)

        # Convert to FoodItem objects
        detected_foods = [
            FoodItem(
                name=food["name"],
                confidence=food["confidence"],
                calories=food.get("calories"),
                protein_g=food.get("protein"),
                carbs_g=food.get("carbs"),
                fat_g=food.get("fat")
            )
            for food in result["detected_foods"]
        ]

        return FoodRecognitionResponse(
            id=f"food_{user_id}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            timestamp=datetime.now(),
            detected_foods=detected_foods,
            total_calories=result["total_calories"],
            nutritional_summary=result["nutritional_summary"],
            recommendations=result["recommendations"]
        )

    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/ocr-supplement", response_model=dict)
async def ocr_supplement_label(
    file: UploadFile = File(...),
    user_id: str = "demo_user"
):
    """
    Extract supplement information from label using OCR

    Accepts: JPG, PNG images of supplement bottles/labels
    """
    import tempfile
    import os
    from ml.ocr.supplement_ocr import get_supplement_ocr

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Run OCR
        ocr = get_supplement_ocr()
        result = ocr.extract_label_info(tmp_path)

        return {
            "id": f"ocr_{user_id}_{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "timestamp": datetime.now(),
            **result
        }

    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
