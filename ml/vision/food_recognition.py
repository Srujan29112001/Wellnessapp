"""
Food Recognition using Vision Transformers (ViT-DINO)
Identifies food items and estimates nutritional information
"""

import torch
import torch.nn as nn
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging

from transformers import ViTImageProcessor, ViTForImageClassification
from transformers import AutoFeatureExtractor, AutoModelForImageClassification
import torchvision.transforms as transforms

logger = logging.getLogger(__name__)


class FoodRecognitionModel:
    """
    Food recognition using Vision Transformer

    Uses pretrained ViT model fine-tuned on food datasets
    """

    def __init__(
        self,
        model_name: str = "nateraw/food",  # Food101 ViT model
        use_gpu: bool = True,
        confidence_threshold: float = 0.3
    ):
        """
        Initialize food recognition model

        Args:
            model_name: HuggingFace model name
            use_gpu: Whether to use GPU
            confidence_threshold: Minimum confidence for predictions
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.confidence_threshold = confidence_threshold

        logger.info(f"Food recognition using device: {self.device}")

        # Load model and processor
        try:
            self.processor = AutoFeatureExtractor.from_pretrained(model_name)
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()

            logger.info(f"Loaded food recognition model: {model_name}")

            # Get label names
            self.labels = list(self.model.config.id2label.values())
            logger.info(f"Model recognizes {len(self.labels)} food categories")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

        # Nutritional database (simplified - in production, use comprehensive DB)
        self.nutrition_db = self._load_nutrition_database()

    def _load_nutrition_database(self) -> Dict[str, Dict[str, float]]:
        """
        Load nutritional information for food items

        Format: food_name -> {calories, protein, carbs, fat, fiber}
        per 100g
        """
        # Simplified database - in production, load from comprehensive source
        nutrition_db = {
            "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4},
            "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6},
            "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6},
            "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
            "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0},
            "salad": {"calories": 15, "protein": 1, "carbs": 3, "fat": 0.2, "fiber": 1.5},
            "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8},
            "pizza": {"calories": 266, "protein": 11, "carbs": 33, "fat": 10, "fiber": 2.3},
            "burger": {"calories": 295, "protein": 17, "carbs": 28, "fat": 13, "fiber": 1.5},
            "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
            "yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4, "fiber": 0},
            "cheese": {"calories": 402, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0},
            "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7},
            "strawberry": {"calories": 32, "protein": 0.7, "carbs": 7.7, "fat": 0.3, "fiber": 2},
            # Add more as needed
        }

        return nutrition_db

    def load_image(self, image_path: str) -> Image.Image:
        """Load and preprocess image"""
        try:
            image = Image.open(image_path).convert("RGB")
            return image
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise

    def recognize_food(
        self,
        image_path: str,
        top_k: int = 5,
        estimate_portion: bool = True
    ) -> Dict[str, any]:
        """
        Recognize food items in image

        Args:
            image_path: Path to image file
            top_k: Number of top predictions to return
            estimate_portion: Whether to estimate portion size

        Returns:
            Recognition results with nutritional estimates
        """
        # Load image
        image = self.load_image(image_path)

        # Preprocess
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits

        # Get probabilities
        probs = torch.nn.functional.softmax(logits, dim=-1)
        top_probs, top_indices = torch.topk(probs, top_k)

        # Format predictions
        predictions = []
        for prob, idx in zip(top_probs[0], top_indices[0]):
            label = self.labels[idx.item()]
            confidence = prob.item()

            if confidence >= self.confidence_threshold:
                predictions.append({
                    "food_name": label,
                    "confidence": confidence,
                    "category": self._categorize_food(label)
                })

        # Get top prediction
        if not predictions:
            return {
                "recognized": False,
                "message": "No food items recognized with sufficient confidence"
            }

        top_food = predictions[0]["food_name"]

        # Estimate nutrition
        nutrition = self._estimate_nutrition(
            food_name=top_food,
            portion_size=1.0  # Default 1 serving
        )

        result = {
            "recognized": True,
            "primary_food": top_food,
            "confidence": predictions[0]["confidence"],
            "all_predictions": predictions,
            "nutrition_estimate": nutrition,
            "recommendations": self._get_food_recommendations(top_food, predictions)
        }

        return result

    def _categorize_food(self, food_name: str) -> str:
        """Categorize food into macro categories"""
        food_lower = food_name.lower()

        # Protein sources
        if any(word in food_lower for word in ["chicken", "beef", "pork", "fish", "salmon", "tuna", "egg", "tofu"]):
            return "protein"

        # Carbs
        elif any(word in food_lower for word in ["rice", "pasta", "bread", "potato", "noodle"]):
            return "carbohydrate"

        # Fruits
        elif any(word in food_lower for word in ["apple", "banana", "orange", "berry", "strawberry", "grape"]):
            return "fruit"

        # Vegetables
        elif any(word in food_lower for word in ["broccoli", "spinach", "carrot", "lettuce", "tomato", "salad"]):
            return "vegetable"

        # Dairy
        elif any(word in food_lower for word in ["milk", "cheese", "yogurt", "cream"]):
            return "dairy"

        # Processed/fast food
        elif any(word in food_lower for word in ["pizza", "burger", "fries", "chips"]):
            return "processed"

        else:
            return "other"

    def _estimate_nutrition(
        self,
        food_name: str,
        portion_size: float = 1.0
    ) -> Dict[str, float]:
        """
        Estimate nutritional content

        Args:
            food_name: Recognized food name
            portion_size: Portion size multiplier

        Returns:
            Nutritional estimates
        """
        # Find closest match in database
        food_lower = food_name.lower()
        nutrition = None

        # Exact match
        if food_lower in self.nutrition_db:
            nutrition = self.nutrition_db[food_lower].copy()

        # Partial match
        else:
            for db_food in self.nutrition_db:
                if db_food in food_lower or food_lower in db_food:
                    nutrition = self.nutrition_db[db_food].copy()
                    break

        # Default if not found
        if nutrition is None:
            logger.warning(f"No nutrition data for {food_name}, using generic estimate")
            nutrition = {
                "calories": 150,
                "protein": 5,
                "carbs": 20,
                "fat": 5,
                "fiber": 2
            }

        # Apply portion size
        nutrition = {k: v * portion_size for k, v in nutrition.items()}

        return nutrition

    def _get_food_recommendations(
        self,
        primary_food: str,
        all_predictions: List[Dict]
    ) -> List[str]:
        """Generate dietary recommendations based on recognized food"""
        recommendations = []

        category = all_predictions[0]["category"]

        if category == "processed":
            recommendations.append("Consider healthier alternatives to processed foods")
            recommendations.append("Add more vegetables to balance the meal")

        elif category == "protein":
            recommendations.append("Great protein source! Pair with vegetables for balanced meal")

        elif category == "carbohydrate":
            recommendations.append("Add protein source to balance blood sugar")
            recommendations.append("Choose whole grain versions when possible")

        elif category == "fruit" or category == "vegetable":
            recommendations.append("Excellent choice! Rich in vitamins and fiber")

        else:
            recommendations.append("Ensure balanced macros (protein, carbs, healthy fats)")

        return recommendations

    def analyze_meal(
        self,
        image_paths: List[str]
    ) -> Dict[str, any]:
        """
        Analyze complete meal from multiple images

        Args:
            image_paths: List of image paths showing meal components

        Returns:
            Complete meal analysis
        """
        meal_components = []
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0
        }

        for image_path in image_paths:
            try:
                result = self.recognize_food(image_path)
                if result["recognized"]:
                    meal_components.append(result)

                    # Add to total nutrition
                    nutrition = result["nutrition_estimate"]
                    for nutrient in total_nutrition:
                        total_nutrition[nutrient] += nutrition.get(nutrient, 0)

            except Exception as e:
                logger.error(f"Error analyzing {image_path}: {e}")

        # Analyze meal balance
        meal_analysis = self._analyze_meal_balance(total_nutrition)

        return {
            "meal_components": meal_components,
            "total_nutrition": total_nutrition,
            "meal_balance": meal_analysis,
            "overall_recommendation": self._get_meal_recommendation(meal_analysis)
        }

    def _analyze_meal_balance(
        self,
        nutrition: Dict[str, float]
    ) -> Dict[str, any]:
        """Analyze if meal is balanced"""
        total_calories = nutrition["calories"]

        if total_calories == 0:
            return {"balanced": False, "reason": "No food detected"}

        # Calculate macro percentages
        protein_cals = nutrition["protein"] * 4
        carb_cals = nutrition["carbs"] * 4
        fat_cals = nutrition["fat"] * 9

        protein_pct = (protein_cals / total_calories) * 100 if total_calories > 0 else 0
        carb_pct = (carb_cals / total_calories) * 100 if total_calories > 0 else 0
        fat_pct = (fat_cals / total_calories) * 100 if total_calories > 0 else 0

        # Check if balanced (rough guidelines)
        is_balanced = (
            15 <= protein_pct <= 35 and
            45 <= carb_pct <= 65 and
            20 <= fat_pct <= 35
        )

        return {
            "balanced": is_balanced,
            "protein_percent": round(protein_pct, 1),
            "carb_percent": round(carb_pct, 1),
            "fat_percent": round(fat_pct, 1),
            "fiber_grams": round(nutrition["fiber"], 1),
            "total_calories": round(total_calories, 0)
        }

    def _get_meal_recommendation(
        self,
        meal_balance: Dict[str, any]
    ) -> str:
        """Get recommendation based on meal balance"""
        if meal_balance["balanced"]:
            return "Well-balanced meal! Good distribution of macronutrients."

        recommendations = []

        if meal_balance["protein_percent"] < 15:
            recommendations.append("Add more protein (lean meats, eggs, legumes)")

        if meal_balance["carb_percent"] > 65:
            recommendations.append("Reduce carbohydrates, add more protein or vegetables")

        if meal_balance["fat_percent"] < 20:
            recommendations.append("Add healthy fats (nuts, avocado, olive oil)")

        if meal_balance["fiber_grams"] < 5:
            recommendations.append("Increase fiber with vegetables, fruits, or whole grains")

        return "; ".join(recommendations) if recommendations else "Consider a more balanced distribution of nutrients"


def create_food_recognition_model(use_gpu: bool = True) -> FoodRecognitionModel:
    """Factory function to create food recognition model"""
    return FoodRecognitionModel(use_gpu=use_gpu)
