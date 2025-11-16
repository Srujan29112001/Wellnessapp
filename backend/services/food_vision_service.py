"""
Food Recognition and OCR Service

Provides:
1. Food recognition from images using ViT-DINO
2. OCR for supplement labels using EasyOCR/Tesseract
3. Nutritional information lookup
"""

import io
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from transformers import AutoImageProcessor, AutoModelForImageClassification
import easyocr
import pytesseract


class FoodRecognitionModel:
    """
    Food recognition using Vision Transformer (ViT) or DINO

    Can use various pre-trained models from HuggingFace
    """

    def __init__(
        self,
        model_name: str = "nateraw/food",  # Food-101 dataset fine-tuned
        device: str = "cpu",
        confidence_threshold: float = 0.3
    ):
        self.device = device
        self.confidence_threshold = confidence_threshold

        try:
            print(f"Loading food recognition model: {model_name}")
            self.processor = AutoImageProcessor.from_pretrained(model_name)
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            self.model.to(device)
            self.model.eval()
            self.available = True
            print("Food recognition model loaded successfully")

        except Exception as e:
            print(f"Could not load food recognition model: {e}")
            print("Using fallback classification")
            self.available = False

        # Load nutritional database
        self.nutrition_db = self._load_nutrition_db()

    def _load_nutrition_db(self) -> Dict:
        """Load nutritional information database"""
        # Simplified nutrition database
        # In production, this would be a comprehensive database like USDA FoodData Central
        return {
            "apple": {"calories": 52, "protein_g": 0.3, "carbs_g": 14, "fat_g": 0.2, "fiber_g": 2.4},
            "banana": {"calories": 89, "protein_g": 1.1, "carbs_g": 23, "fat_g": 0.3, "fiber_g": 2.6},
            "orange": {"calories": 47, "protein_g": 0.9, "carbs_g": 12, "fat_g": 0.1, "fiber_g": 2.4},
            "salad": {"calories": 50, "protein_g": 3, "carbs_g": 8, "fat_g": 1, "fiber_g": 3},
            "chicken": {"calories": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6, "fiber_g": 0},
            "rice": {"calories": 130, "protein_g": 2.7, "carbs_g": 28, "fat_g": 0.3, "fiber_g": 0.4},
            "bread": {"calories": 265, "protein_g": 9, "carbs_g": 49, "fat_g": 3.2, "fiber_g": 2.7},
            "pasta": {"calories": 131, "protein_g": 5, "carbs_g": 25, "fat_g": 1.1, "fiber_g": 1.8},
            "egg": {"calories": 155, "protein_g": 13, "carbs_g": 1.1, "fat_g": 11, "fiber_g": 0},
            "fish": {"calories": 206, "protein_g": 22, "carbs_g": 0, "fat_g": 12, "fiber_g": 0},
            "yogurt": {"calories": 59, "protein_g": 10, "carbs_g": 3.6, "fat_g": 0.4, "fiber_g": 0},
            "cheese": {"calories": 402, "protein_g": 25, "carbs_g": 1.3, "fat_g": 33, "fiber_g": 0},
            "broccoli": {"calories": 34, "protein_g": 2.8, "carbs_g": 7, "fat_g": 0.4, "fiber_g": 2.6},
            "carrot": {"calories": 41, "protein_g": 0.9, "carbs_g": 10, "fat_g": 0.2, "fiber_g": 2.8},
            "tomato": {"calories": 18, "protein_g": 0.9, "carbs_g": 3.9, "fat_g": 0.2, "fiber_g": 1.2},
            "potato": {"calories": 77, "protein_g": 2, "carbs_g": 17, "fat_g": 0.1, "fiber_g": 2.2},
            "steak": {"calories": 271, "protein_g": 26, "carbs_g": 0, "fat_g": 19, "fiber_g": 0},
            "pizza": {"calories": 266, "protein_g": 11, "carbs_g": 33, "fat_g": 10, "fiber_g": 2.5},
            "burger": {"calories": 354, "protein_g": 20, "carbs_g": 30, "fat_g": 17, "fiber_g": 2.0},
            "sandwich": {"calories": 250, "protein_g": 12, "carbs_g": 30, "fat_g": 9, "fiber_g": 2.5},
        }

    def recognize(self, image: Image.Image, top_k: int = 3) -> List[Dict]:
        """
        Recognize food items in image

        Args:
            image: PIL Image
            top_k: Number of top predictions to return

        Returns:
            List of detected foods with confidence scores
        """
        if not self.available:
            return self._fallback_recognition(image)

        try:
            # Preprocess image
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            # Get probabilities
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]

            # Get top-k predictions
            top_probs, top_indices = torch.topk(probs, k=min(top_k, len(probs)))

            results = []
            for prob, idx in zip(top_probs, top_indices):
                prob = float(prob)
                if prob < self.confidence_threshold:
                    continue

                # Get label
                label = self.model.config.id2label[int(idx)]

                # Clean label (remove underscores, etc.)
                clean_label = label.replace('_', ' ').title()

                # Look up nutrition
                nutrition = self._lookup_nutrition(clean_label.lower())

                results.append({
                    "name": clean_label,
                    "confidence": prob,
                    **nutrition
                })

            return results if results else self._fallback_recognition(image)

        except Exception as e:
            print(f"Error in food recognition: {e}")
            return self._fallback_recognition(image)

    def _lookup_nutrition(self, food_name: str) -> Dict:
        """Look up nutritional information"""
        # Try exact match first
        if food_name in self.nutrition_db:
            return self.nutrition_db[food_name].copy()

        # Try partial match
        for key in self.nutrition_db:
            if key in food_name or food_name in key:
                return self.nutrition_db[key].copy()

        # Default values if not found
        return {
            "calories": 100,
            "protein_g": 5.0,
            "carbs_g": 15.0,
            "fat_g": 3.0,
            "fiber_g": 2.0
        }

    def _fallback_recognition(self, image: Image.Image) -> List[Dict]:
        """Fallback recognition when model is not available"""
        # Return mock data
        return [
            {
                "name": "Mixed Salad",
                "confidence": 0.75,
                "calories": 150,
                "protein_g": 5.0,
                "carbs_g": 20.0,
                "fat_g": 7.0,
                "fiber_g": 5.0
            }
        ]


class SupplementOCR:
    """OCR service for extracting supplement information from labels"""

    def __init__(self, use_gpu: bool = False):
        try:
            # Initialize EasyOCR
            self.reader = easyocr.Reader(['en'], gpu=use_gpu)
            self.available = True
            print("EasyOCR initialized successfully")

        except Exception as e:
            print(f"Could not initialize EasyOCR: {e}")
            print("Falling back to Tesseract")
            self.reader = None
            self.available = pytesseract.pytesseract.tesseract_cmd is not None

        # Load supplement database
        self.supplement_db = self._load_supplement_db()

    def _load_supplement_db(self) -> Dict:
        """Load supplement database"""
        db_path = Path("/home/user/Wellnessapp/knowledge_base/supplements/supplements_db.json")

        if db_path.exists():
            with open(db_path) as f:
                data = json.load(f)
                # Create lookup dictionary
                return {
                    supp['name'].lower(): supp
                    for supp in data.get('supplements', [])
                }

        return {}

    def extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        if self.reader is not None:
            # Use EasyOCR
            result = self.reader.readtext(np.array(image))
            text = ' '.join([detection[1] for detection in result])

        else:
            # Use Tesseract
            text = pytesseract.image_to_string(image)

        return text

    def parse_supplement_label(self, image: Image.Image) -> Dict:
        """
        Parse supplement label from image

        Returns:
            {
                'supplement_name': str,
                'dosage': str,
                'ingredients': List[str],
                'benefits': List[str],
                'warnings': List[str],
                ...
            }
        """
        # Extract text
        text = self.extract_text(image)

        # Parse supplement information
        result = {
            "id": f"ocr_{int(datetime.now().timestamp())}",
            "raw_text": text,
            "supplement_name": self._extract_supplement_name(text),
            "dosage": self._extract_dosage(text),
            "ingredients": self._extract_ingredients(text),
            "active_compounds": {},
            "benefits": [],
            "warnings": [],
            "contraindications": []
        }

        # Look up in database if found
        if result["supplement_name"]:
            db_info = self._lookup_supplement(result["supplement_name"])
            if db_info:
                result.update({
                    "benefits": db_info.get("benefits", []),
                    "contraindications": db_info.get("contraindications", []),
                    "dosage_info": db_info.get("dosage", {}),
                    "evidence": db_info.get("evidence", [])
                })

        return result

    def _extract_supplement_name(self, text: str) -> str:
        """Extract supplement name from OCR text"""
        # Look for known supplements
        text_lower = text.lower()

        for supp_name in self.supplement_db:
            if supp_name in text_lower:
                return supp_name.title()

        # Try to find common supplement keywords
        keywords = [
            'ashwagandha', 'magnesium', 'omega', 'vitamin', 'calcium',
            'zinc', 'iron', 'b12', 'b-12', 'turmeric', 'curcumin',
            'melatonin', 'probiotics', 'brahmi', 'theanine'
        ]

        for keyword in keywords:
            if keyword in text_lower:
                return keyword.title()

        return "Unknown Supplement"

    def _extract_dosage(self, text: str) -> str:
        """Extract dosage information"""
        # Look for patterns like "500mg", "1000 mg", "1g", etc.
        patterns = [
            r'(\d+\.?\d*)\s*(mg|g|mcg|iu)',
            r'(\d+)\s*x\s*(\d+\.?\d*)\s*(mg|g|mcg)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0)

        return "Dosage not found"

    def _extract_ingredients(self, text: str) -> List[str]:
        """Extract ingredients list"""
        # Look for "Ingredients:" section
        match = re.search(r'ingredients?:(.+?)(\n|$)', text.lower())

        if match:
            ingredients_text = match.group(1)
            # Split by common delimiters
            ingredients = re.split(r'[,;]', ingredients_text)
            return [ing.strip() for ing in ingredients if ing.strip()]

        return []

    def _lookup_supplement(self, name: str) -> Optional[Dict]:
        """Look up supplement in database"""
        name_lower = name.lower()

        # Exact match
        if name_lower in self.supplement_db:
            return self.supplement_db[name_lower]

        # Partial match
        for key in self.supplement_db:
            if key in name_lower or name_lower in key:
                return self.supplement_db[key]

        return None


class FoodVisionService:
    """Combined food recognition and OCR service"""

    def __init__(self):
        self.food_model = FoodRecognitionModel()
        self.ocr_service = SupplementOCR()

    async def recognize_food(self, image_bytes: bytes, user_id: str) -> Dict:
        """Recognize food from image"""
        # Load image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Recognize foods
        detected_foods = self.food_model.recognize(image, top_k=5)

        # Calculate totals
        total_calories = sum(food.get('calories', 0) for food in detected_foods)

        nutritional_summary = {
            'protein_g': sum(food.get('protein_g', 0) for food in detected_foods),
            'carbs_g': sum(food.get('carbs_g', 0) for food in detected_foods),
            'fat_g': sum(food.get('fat_g', 0) for food in detected_foods),
            'fiber_g': sum(food.get('fiber_g', 0) for food in detected_foods)
        }

        # Generate recommendations
        recommendations = self._generate_food_recommendations(
            detected_foods,
            nutritional_summary
        )

        return {
            'id': f"food_{user_id}_{int(datetime.now().timestamp())}",
            'user_id': user_id,
            'timestamp': datetime.now(),
            'detected_foods': detected_foods,
            'total_calories': total_calories,
            'nutritional_summary': nutritional_summary,
            'recommendations': recommendations
        }

    async def ocr_supplement(self, image_bytes: bytes, user_id: str) -> Dict:
        """Extract supplement information from label"""
        # Load image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Parse label
        result = self.ocr_service.parse_supplement_label(image)
        result['user_id'] = user_id
        result['timestamp'] = datetime.now()

        return result

    def _generate_food_recommendations(
        self,
        foods: List[Dict],
        nutrition: Dict
    ) -> List[str]:
        """Generate dietary recommendations"""
        recommendations = []

        # Check protein
        if nutrition['protein_g'] > 30:
            recommendations.append("Great protein-rich meal!")
        elif nutrition['protein_g'] < 10:
            recommendations.append("Consider adding more protein for muscle maintenance.")

        # Check fiber
        if nutrition['fiber_g'] < 3:
            recommendations.append("Add more vegetables or whole grains for fiber.")

        # Check fat
        if nutrition['fat_g'] > 30:
            recommendations.append("High fat content - ensure it's from healthy sources.")

        # Check carbs
        if nutrition['carbs_g'] > 60:
            recommendations.append("High carb meal - great for energy before exercise.")

        # Balance
        protein_ratio = nutrition['protein_g'] / max(nutrition['carbs_g'], 1)
        if protein_ratio < 0.2:
            recommendations.append("Consider balancing carbs with more protein.")

        return recommendations


# Global service instance
_food_service: Optional[FoodVisionService] = None


def get_food_service() -> FoodVisionService:
    """Get or create food vision service instance"""
    global _food_service

    if _food_service is None:
        _food_service = FoodVisionService()

    return _food_service
