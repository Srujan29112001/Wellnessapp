"""
Food Recognition using Vision Transformers

This module implements food classification and nutrition estimation using:
- ViT-DINO or similar vision transformer models
- Food-101 dataset knowledge
- Nutrition database integration
"""

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path


class FoodRecognitionModel:
    """
    Food recognition using Vision Transformer (ViT) models
    """

    def __init__(
        self,
        model_name: str = "facebook/dino-vits16",
        use_pretrained: bool = True
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.model = None
        self.processor = None

        # Food categories (subset of Food-101 dataset)
        self.food_categories = self._load_food_categories()

        # Load nutrition database
        self.nutrition_db = self._load_nutrition_database()

        if use_pretrained:
            self._load_pretrained_model()
        else:
            self._create_custom_model()

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def _load_food_categories(self) -> List[str]:
        """Load food categories"""
        # Common food categories (simplified Food-101)
        return [
            "apple_pie", "baby_back_ribs", "baklava", "beef_carpaccio", "beef_tartare",
            "beet_salad", "beignets", "bibimbap", "bread_pudding", "breakfast_burrito",
            "bruschetta", "caesar_salad", "cannoli", "caprese_salad", "carrot_cake",
            "ceviche", "cheese_plate", "cheesecake", "chicken_curry", "chicken_quesadilla",
            "chicken_wings", "chocolate_cake", "chocolate_mousse", "churros", "clam_chowder",
            "club_sandwich", "crab_cakes", "creme_brulee", "croque_madame", "cup_cakes",
            "deviled_eggs", "donuts", "dumplings", "edamame", "eggs_benedict",
            "escargots", "falafel", "filet_mignon", "fish_and_chips", "foie_gras",
            "french_fries", "french_onion_soup", "french_toast", "fried_calamari", "fried_rice",
            "frozen_yogurt", "garlic_bread", "gnocchi", "greek_salad", "grilled_cheese_sandwich",
            "grilled_salmon", "guacamole", "gyoza", "hamburger", "hot_and_sour_soup",
            "hot_dog", "huevos_rancheros", "hummus", "ice_cream", "lasagna",
            "lobster_bisque", "lobster_roll_sandwich", "macaroni_and_cheese", "macarons", "miso_soup",
            "mussels", "nachos", "omelette", "onion_rings", "oysters",
            "pad_thai", "paella", "pancakes", "panna_cotta", "peking_duck",
            "pho", "pizza", "pork_chop", "poutine", "prime_rib",
            "pulled_pork_sandwich", "ramen", "ravioli", "red_velvet_cake", "risotto",
            "samosa", "sashimi", "scallops", "seaweed_salad", "shrimp_and_grits",
            "spaghetti_bolognese", "spaghetti_carbonara", "spring_rolls", "steak", "strawberry_shortcake",
            "sushi", "tacos", "takoyaki", "tiramisu", "tuna_tartare", "waffles"
        ]

    def _load_nutrition_database(self) -> Dict:
        """Load nutrition information for common foods"""
        # Simplified nutrition database (calories per 100g)
        return {
            "salad": {"calories": 50, "protein": 2, "carbs": 8, "fat": 2},
            "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
            "fish": {"calories": 150, "protein": 25, "carbs": 0, "fat": 5},
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
            "pasta": {"calories": 150, "protein": 5, "carbs": 30, "fat": 1},
            "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2},
            "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15},
            "pizza": {"calories": 266, "protein": 11, "carbs": 33, "fat": 10},
            "burger": {"calories": 295, "protein": 17, "carbs": 28, "fat": 13},
            "soup": {"calories": 60, "protein": 3, "carbs": 10, "fat": 1.5},
            "sandwich": {"calories": 250, "protein": 15, "carbs": 30, "fat": 8},
            "fruit": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2},
            "vegetables": {"calories": 35, "protein": 2, "carbs": 7, "fat": 0.4},
            "cake": {"calories": 350, "protein": 5, "carbs": 50, "fat": 15},
            "ice_cream": {"calories": 207, "protein": 3.5, "carbs": 24, "fat": 11},
            "chocolate": {"calories": 546, "protein": 5, "carbs": 61, "fat": 31},
        }

    def _load_pretrained_model(self):
        """Load pretrained ViT-DINO or similar model"""
        try:
            from transformers import AutoFeatureExtractor, AutoModelForImageClassification

            # Try to load a food classification model from HuggingFace
            # Fallback to general ViT model
            try:
                model_name = "nateraw/food"  # Food-specific model
                self.processor = AutoFeatureExtractor.from_pretrained(model_name)
                self.model = AutoModelForImageClassification.from_pretrained(model_name)
                print(f"✅ Loaded food-specific model: {model_name}")
            except:
                # Fallback to ViT-DINO
                model_name = "facebook/dino-vitb16"
                from transformers import ViTFeatureExtractor, ViTForImageClassification
                self.processor = ViTFeatureExtractor.from_pretrained(model_name)
                self.model = ViTForImageClassification.from_pretrained(model_name)
                print(f"✅ Loaded ViT-DINO model: {model_name}")

            self.model.to(self.device)
            self.model.eval()

        except Exception as e:
            print(f"Could not load pretrained model: {e}")
            print("Falling back to custom model")
            self._create_custom_model()

    def _create_custom_model(self):
        """Create a custom food classifier"""
        class SimpleFoodClassifier(nn.Module):
            def __init__(self, num_classes=101):
                super().__init__()
                # Simple CNN for demonstration
                self.features = nn.Sequential(
                    nn.Conv2d(3, 64, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    nn.Conv2d(64, 128, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    nn.Conv2d(128, 256, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool2d((7, 7))
                )
                self.classifier = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(256 * 7 * 7, 512),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(512, num_classes)
                )

            def forward(self, x):
                x = self.features(x)
                x = self.classifier(x)
                return x

        self.model = SimpleFoodClassifier(num_classes=len(self.food_categories))
        self.model.to(self.device)
        self.model.eval()

        print("✅ Created custom food classifier")

    def recognize_food(
        self,
        image_path: str = None,
        image: Image.Image = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Recognize food items in image

        Args:
            image_path: Path to image file
            image: PIL Image object
            top_k: Return top K predictions

        Returns:
            List of predicted food items with confidence
        """
        # Load image
        if image_path:
            image = Image.open(image_path).convert("RGB")
        elif image is None:
            raise ValueError("Either image_path or image must be provided")

        # Preprocess
        if self.processor:
            # Use HuggingFace processor
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]
        else:
            # Use custom preprocessing
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.model(image_tensor)

            probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]

        # Get top-k predictions
        top_k_probs, top_k_indices = torch.topk(probabilities, k=min(top_k, len(probabilities)))

        predictions = []
        for prob, idx in zip(top_k_probs, top_k_indices):
            if idx < len(self.food_categories):
                food_name = self.food_categories[idx]
                predictions.append({
                    "name": food_name.replace("_", " ").title(),
                    "confidence": float(prob),
                    "category": self._get_food_category(food_name)
                })

        return predictions

    def _get_food_category(self, food_name: str) -> str:
        """Categorize food into broad categories"""
        food_lower = food_name.lower()

        if any(x in food_lower for x in ["salad", "vegetables", "greens"]):
            return "vegetables"
        elif any(x in food_lower for x in ["chicken", "beef", "pork", "fish", "salmon", "steak"]):
            return "protein"
        elif any(x in food_lower for x in ["rice", "pasta", "bread", "noodles"]):
            return "carbs"
        elif any(x in food_lower for x in ["cake", "pie", "ice_cream", "chocolate", "dessert"]):
            return "dessert"
        elif any(x in food_lower for x in ["soup", "stew", "chowder"]):
            return "soup"
        else:
            return "mixed"

    def estimate_nutrition(
        self,
        food_items: List[Dict],
        portion_size: str = "medium"
    ) -> Dict[str, float]:
        """
        Estimate nutritional content

        Args:
            food_items: List of recognized food items
            portion_size: "small", "medium", or "large"

        Returns:
            Estimated nutrition (calories, protein, carbs, fat)
        """
        portion_multiplier = {
            "small": 0.7,
            "medium": 1.0,
            "large": 1.5
        }

        multiplier = portion_multiplier.get(portion_size, 1.0)

        total_nutrition = {
            "calories": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0,
            "fiber_g": 0
        }

        for item in food_items:
            # Get category
            category = item.get("category", "mixed")

            # Look up nutrition
            nutrition = self.nutrition_db.get(category, self.nutrition_db.get("mixed", {}))

            # Weight by confidence
            confidence = item.get("confidence", 1.0)

            total_nutrition["calories"] += nutrition.get("calories", 200) * multiplier * confidence
            total_nutrition["protein_g"] += nutrition.get("protein", 10) * multiplier * confidence
            total_nutrition["carbs_g"] += nutrition.get("carbs", 25) * multiplier * confidence
            total_nutrition["fat_g"] += nutrition.get("fat", 8) * multiplier * confidence

            # Estimate fiber (rough)
            if category in ["vegetables", "fruit", "salad"]:
                total_nutrition["fiber_g"] += 3 * multiplier * confidence

        # Round values
        return {k: round(v, 1) for k, v in total_nutrition.items()}

    def get_health_recommendations(
        self,
        food_items: List[Dict],
        nutrition: Dict[str, float]
    ) -> List[str]:
        """
        Generate health recommendations based on detected food
        """
        recommendations = []

        # Check if meal is balanced
        protein = nutrition.get("protein_g", 0)
        carbs = nutrition.get("carbs_g", 0)
        fat = nutrition.get("fat_g", 0)
        calories = nutrition.get("calories", 0)

        # High protein check
        if protein > 30:
            recommendations.append("Great protein content! Supports muscle recovery and satiety.")
        elif protein < 15:
            recommendations.append("Consider adding more protein (chicken, fish, tofu, legumes) for better satiety.")

        # Balanced macros
        total_macros = protein + carbs + fat
        if total_macros > 0:
            protein_pct = (protein * 4 / calories * 100) if calories > 0 else 0
            if 25 <= protein_pct <= 35:
                recommendations.append("Well-balanced macronutrient distribution.")

        # Vegetable content
        has_vegetables = any(item.get("category") == "vegetables" for item in food_items)
        if has_vegetables:
            recommendations.append("Good vegetable content for micronutrients and fiber!")
        else:
            recommendations.append("Add vegetables or salad for vitamins, minerals, and fiber.")

        # Dessert check
        has_dessert = any(item.get("category") == "dessert" for item in food_items)
        if has_dessert:
            recommendations.append("Enjoy the dessert mindfully! Consider limiting sugar intake.")

        # Calorie check
        if calories > 800:
            recommendations.append("This is a substantial meal. Ensure it fits your daily caloric needs.")
        elif calories < 300:
            recommendations.append("Light meal detected. You may need another meal or snack later.")

        return recommendations[:3]  # Top 3 recommendations

    def analyze_meal(
        self,
        image_path: str = None,
        image: Image.Image = None,
        portion_size: str = "medium"
    ) -> Dict:
        """
        Complete meal analysis: recognition + nutrition + recommendations

        Returns:
            Dict with food items, nutrition, and recommendations
        """
        # Recognize food
        food_items = self.recognize_food(image_path=image_path, image=image, top_k=3)

        # Estimate nutrition
        nutrition = self.estimate_nutrition(food_items, portion_size=portion_size)

        # Generate recommendations
        recommendations = self.get_health_recommendations(food_items, nutrition)

        return {
            "detected_foods": food_items,
            "total_calories": int(nutrition["calories"]),
            "nutritional_summary": nutrition,
            "recommendations": recommendations
        }


class FoodImageProcessor:
    """
    Utility class for food image preprocessing
    """

    @staticmethod
    def enhance_food_image(image: Image.Image) -> Image.Image:
        """
        Enhance food image for better recognition
        """
        from PIL import ImageEnhance

        # Slightly enhance saturation and contrast for food photos
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.2)

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)

        return image

    @staticmethod
    def crop_to_food(image: Image.Image) -> Image.Image:
        """
        Crop image to focus on food (simple center crop)
        """
        width, height = image.size
        crop_size = min(width, height)

        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        right = left + crop_size
        bottom = top + crop_size

        return image.crop((left, top, right, bottom))


# Convenience function
def analyze_food_from_image(image_path: str) -> Dict:
    """
    Quick function to analyze food from image
    """
    classifier = FoodRecognitionModel()
    return classifier.analyze_meal(image_path=image_path)
