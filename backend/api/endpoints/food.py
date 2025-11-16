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
    user_id: str = "demo_user",
    portion_size: str = "medium"
):
    """
    Recognize food items from image using ViT-DINO model

    Accepts: JPG, PNG image files
    """
    import tempfile
    import os
    from PIL import Image
    from ml.food_recognition import FoodRecognitionModel

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Load image
        image = Image.open(tmp_path)

        # Analyze meal
        model = FoodRecognitionModel()
        result = model.analyze_meal(image=image, portion_size=portion_size)

        # Convert to response format
        detected_foods = [
            FoodItem(
                name=food["name"],
                confidence=food["confidence"],
                calories=None,  # Individual calories not broken down
                protein_g=None,
                carbs_g=None,
                fat_g=None
            )
            for food in result["detected_foods"]
        ]

        return FoodRecognitionResponse(
            id=f"food_{datetime.now().timestamp()}",
            user_id=user_id,
            timestamp=datetime.now(),
            detected_foods=detected_foods,
            total_calories=result["total_calories"],
            nutritional_summary=result["nutritional_summary"],
            recommendations=result["recommendations"]
        )

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


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
    from PIL import Image
    from ml.ocr import SupplementOCR

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Load image
        image = Image.open(tmp_path)

        # Scan supplement label
        scanner = SupplementOCR()
        result = scanner.scan_supplement_label(image=image)

        # Add metadata
        result["id"] = f"supp_{datetime.now().timestamp()}"
        result["user_id"] = user_id
        result["timestamp"] = datetime.now()

        return result

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
