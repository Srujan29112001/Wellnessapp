"""
Food Recognition Service using Vision Transformer (ViT)

Identifies foods in images and estimates nutritional content
"""
import logging
from typing import Dict, List, Any
from pathlib import Path
import torch
from PIL import Image
from transformers import ViTForImageClassification, ViTImageProcessor
import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)


# Nutrition database (simplified - in production, use comprehensive DB)
NUTRITION_DB = {
    "apple": {"calories": 95, "protein": 0.5, "carbs": 25, "fat": 0.3},
    "banana": {"calories": 105, "protein": 1.3, "carbs": 27, "fat": 0.4},
    "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    "broccoli": {"calories": 55, "protein": 3.7, "carbs": 11, "fat": 0.6},
    "rice": {"calories": 206, "protein": 4.3, "carbs": 45, "fat": 0.4},
    "salmon": {"calories": 208, "protein": 22, "carbs": 0, "fat": 13},
    "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2},
    "egg": {"calories": 72, "protein": 6.3, "carbs": 0.4, "fat": 4.8},
    "salad": {"calories": 15, "protein": 1, "carbs": 3, "fat": 0.2},
    "pasta": {"calories": 200, "protein": 7, "carbs": 40, "fat": 1.5},
}


class FoodRecognizer:
    """
    Food recognition using Vision Transformer
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.confidence_threshold = settings.FOOD_CONFIDENCE_THRESHOLD

        # Try to load pretrained model
        try:
            # Using Food-101 pretrained ViT
            model_name = "nateraw/food"
            self.processor = ViTImageProcessor.from_pretrained(
                model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            self.model = ViTForImageClassification.from_pretrained(
                model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            ).to(self.device)
            self.model.eval()

            # Get label names
            self.labels = list(self.model.config.id2label.values())
            logger.info(f"Loaded food recognition model with {len(self.labels)} classes")

        except Exception as e:
            logger.warning(f"Could not load pretrained food model: {e}")
            logger.info("Using fallback classification")
            self.processor = None
            self.model = None
            self.labels = list(NUTRITION_DB.keys())

    def load_image(self, file_path: str) -> Image.Image:
        """Load and preprocess image"""
        image = Image.open(file_path).convert("RGB")
        return image

    def recognize(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Recognize foods in image

        Returns:
            List of detected foods with confidence scores
        """
        try:
            # Load image
            image = self.load_image(file_path)

            if self.model is not None and self.processor is not None:
                # Use ViT model
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Inference
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits

                # Get probabilities
                probs = torch.nn.functional.softmax(logits, dim=-1)
                probs = probs.cpu().numpy()[0]

                # Get top-k predictions
                top_k = 5
                top_indices = np.argsort(probs)[::-1][:top_k]

                detected_foods = []
                for idx in top_indices:
                    confidence = float(probs[idx])
                    if confidence >= self.confidence_threshold:
                        food_name = self.labels[idx]
                        detected_foods.append({
                            "name": food_name,
                            "confidence": confidence
                        })

                logger.info(f"Detected {len(detected_foods)} foods in image")
                return detected_foods

            else:
                # Fallback: return a mock detection
                logger.warning("Using fallback food recognition")
                return [{
                    "name": "mixed_salad",
                    "confidence": 0.75
                }]

        except Exception as e:
            logger.error(f"Error recognizing food: {e}")
            return []

    def estimate_nutrition(self, detected_foods: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Estimate nutritional content from detected foods

        Args:
            detected_foods: List of detected foods with confidence scores

        Returns:
            Dict with estimated nutrition (calories, protein, carbs, fat)
        """
        total_nutrition = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0
        }

        for food in detected_foods:
            food_name = food["name"].lower().replace("_", " ")
            confidence = food["confidence"]

            # Look up nutrition (try exact match first, then fuzzy match)
            nutrition = None
            if food_name in NUTRITION_DB:
                nutrition = NUTRITION_DB[food_name]
            else:
                # Try to find partial match
                for key in NUTRITION_DB.keys():
                    if key in food_name or food_name in key:
                        nutrition = NUTRITION_DB[key]
                        break

            if nutrition:
                # Weight by confidence
                for nutrient, value in nutrition.items():
                    total_nutrition[nutrient] += value * confidence
            else:
                # Default estimate
                logger.warning(f"No nutrition data for {food_name}, using defaults")
                total_nutrition["calories"] += 100 * confidence
                total_nutrition["protein"] += 5 * confidence
                total_nutrition["carbs"] += 15 * confidence
                total_nutrition["fat"] += 3 * confidence

        return total_nutrition

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Complete food analysis

        Args:
            file_path: Path to food image

        Returns:
            Dict with detected foods and estimated nutrition
        """
        try:
            # Recognize foods
            detected_foods = self.recognize(file_path)

            if not detected_foods:
                return {
                    "detected_foods": [],
                    "nutrition": {
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "success": False,
                    "message": "No food detected in image"
                }

            # Estimate nutrition
            nutrition = self.estimate_nutrition(detected_foods)

            result = {
                "detected_foods": detected_foods,
                "nutrition": nutrition,
                "success": True,
                "message": f"Detected {len(detected_foods)} food items"
            }

            logger.info(f"Food analysis complete: {len(detected_foods)} items, {nutrition['calories']:.0f} cal")

            return result

        except Exception as e:
            logger.error(f"Error in food analysis: {e}")
            return {
                "detected_foods": [],
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                "success": False,
                "message": f"Error: {str(e)}"
            }


# Global recognizer instance
_recognizer = None


def get_food_recognizer() -> FoodRecognizer:
    """Get or create food recognizer"""
    global _recognizer
    if _recognizer is None:
        _recognizer = FoodRecognizer()
    return _recognizer
