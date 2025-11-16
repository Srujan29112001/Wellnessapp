"""
Computer Vision Service for Food Recognition and OCR

Handles:
- Food recognition using ViT-DINO or other vision models
- OCR for supplement labels using Tesseract/EasyOCR
"""
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from PIL import Image
import numpy as np

# OCR
import pytesseract
import easyocr

# Computer Vision
import torch
from torchvision import transforms
from transformers import AutoImageProcessor, AutoModelForImageClassification, ViTImageProcessor, ViTForImageClassification

from backend.models.mongo_schemas import MealImage, COLLECTION_MEAL_IMAGES
from backend.database.mongo import get_collection

logger = logging.getLogger(__name__)


class VisionService:
    """Service for food recognition and OCR"""

    def __init__(self):
        """Initialize vision models"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Initialize food recognition model (ViT)
        self.food_model = None
        self.food_processor = None
        self._init_food_model()

        # Initialize OCR reader
        self.ocr_reader = None
        self._init_ocr()

    def _init_food_model(self):
        """Initialize food recognition model"""
        try:
            # Use a pre-trained food classification model
            model_name = "nateraw/food"  # Food-101 dataset trained model

            self.food_processor = AutoImageProcessor.from_pretrained(model_name)
            self.food_model = AutoModelForImageClassification.from_pretrained(model_name)
            self.food_model.to(self.device)
            self.food_model.eval()

            logger.info("Food recognition model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load food model: {e}. Using mock predictions.")
            self.food_model = None

    def _init_ocr(self):
        """Initialize OCR reader"""
        try:
            # Use EasyOCR for better accuracy
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            logger.info("OCR reader initialized (EasyOCR)")
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}. Will fall back to Tesseract.")
            self.ocr_reader = None

    async def recognize_food(
        self,
        user_id: str,
        image_path: str,
        store_result: bool = True
    ) -> Dict[str, Any]:
        """
        Recognize food items in an image

        Args:
            user_id: User ID
            image_path: Path to meal image
            store_result: Whether to store in MongoDB

        Returns:
            Detection results
        """
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')

            # Predict food items
            if self.food_model is not None:
                predictions = self._predict_food(image)
            else:
                # Mock predictions for development
                predictions = self._mock_food_predictions()

            # Store in MongoDB if requested
            mongo_id = None
            if store_result:
                mongo_id = await self._store_meal_image(
                    user_id,
                    image_path,
                    predictions
                )

            return {
                "mongo_id": mongo_id,
                "detected_foods": predictions,
                "count": len(predictions)
            }

        except Exception as e:
            logger.error(f"Error recognizing food: {e}", exc_info=True)
            raise

    def _predict_food(self, image: Image.Image) -> List[Dict]:
        """Predict food items using ViT model"""
        # Preprocess image
        inputs = self.food_processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get predictions
        with torch.no_grad():
            outputs = self.food_model(**inputs)
            logits = outputs.logits

        # Get top predictions
        probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        top_probs, top_indices = torch.topk(probs, k=5)

        predictions = []
        for prob, idx in zip(top_probs, top_indices):
            label = self.food_model.config.id2label[idx.item()]
            confidence = prob.item()

            if confidence > 0.1:  # Only include confident predictions
                predictions.append({
                    "name": label.replace('_', ' ').title(),
                    "confidence": round(confidence, 3),
                    "category": self._categorize_food(label)
                })

        return predictions

    def _mock_food_predictions(self) -> List[Dict]:
        """Mock food predictions for development"""
        return [
            {"name": "Salad", "confidence": 0.85, "category": "vegetables"},
            {"name": "Grilled Chicken", "confidence": 0.75, "category": "protein"},
            {"name": "Brown Rice", "confidence": 0.65, "category": "grains"}
        ]

    def _categorize_food(self, label: str) -> str:
        """Categorize food item"""
        label_lower = label.lower()

        if any(word in label_lower for word in ['salad', 'vegetable', 'broccoli', 'carrot', 'lettuce']):
            return 'vegetables'
        elif any(word in label_lower for word in ['chicken', 'beef', 'fish', 'egg', 'tofu']):
            return 'protein'
        elif any(word in label_lower for word in ['rice', 'bread', 'pasta', 'noodle', 'grain']):
            return 'grains'
        elif any(word in label_lower for word in ['apple', 'banana', 'orange', 'berry']):
            return 'fruits'
        elif any(word in label_lower for word in ['milk', 'cheese', 'yogurt']):
            return 'dairy'
        else:
            return 'other'

    async def extract_supplement_info(
        self,
        user_id: str,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Extract supplement information from label using OCR

        Args:
            user_id: User ID
            image_path: Path to supplement label image

        Returns:
            Extracted information
        """
        try:
            # Perform OCR
            ocr_text = self._perform_ocr(image_path)

            # Parse supplement information
            supplement_info = self._parse_supplement_label(ocr_text)

            # Store in MongoDB
            mongo_id = await self._store_meal_image(
                user_id,
                image_path,
                [],
                ocr_text=ocr_text,
                extracted_info=supplement_info
            )

            return {
                "mongo_id": mongo_id,
                "ocr_text": ocr_text,
                "supplement_info": supplement_info
            }

        except Exception as e:
            logger.error(f"Error extracting supplement info: {e}", exc_info=True)
            raise

    def _perform_ocr(self, image_path: str) -> str:
        """Perform OCR on image"""
        try:
            if self.ocr_reader is not None:
                # Use EasyOCR
                results = self.ocr_reader.readtext(image_path)
                text = ' '.join([result[1] for result in results])
            else:
                # Fall back to Tesseract
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image)

            return text

        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

    def _parse_supplement_label(self, ocr_text: str) -> Dict[str, Any]:
        """
        Parse supplement information from OCR text

        Looks for:
        - Supplement name
        - Dosage (mg, mcg, IU, etc.)
        - Ingredients
        - Warnings
        """
        info = {
            "name": None,
            "dosage": None,
            "ingredients": [],
            "warnings": []
        }

        lines = ocr_text.split('\n')

        # Extract dosage
        import re
        dosage_pattern = r'(\d+)\s*(mg|mcg|iu|g|ml)'
        dosages = re.findall(dosage_pattern, ocr_text, re.IGNORECASE)
        if dosages:
            info['dosage'] = f"{dosages[0][0]} {dosages[0][1]}"

        # Extract supplement name (usually in first few lines, uppercase)
        for line in lines[:5]:
            if line.isupper() and len(line) > 3:
                info['name'] = line.strip()
                break

        # Look for ingredients section
        for i, line in enumerate(lines):
            if 'ingredient' in line.lower():
                # Next few lines are ingredients
                for ing_line in lines[i+1:i+10]:
                    if ing_line.strip() and len(ing_line) > 2:
                        info['ingredients'].append(ing_line.strip())

        # Look for warnings
        warning_keywords = ['warning', 'caution', 'consult', 'not intended']
        for line in lines:
            if any(keyword in line.lower() for keyword in warning_keywords):
                info['warnings'].append(line.strip())

        return info

    async def _store_meal_image(
        self,
        user_id: str,
        image_path: str,
        detected_foods: List[Dict],
        ocr_text: Optional[str] = None,
        extracted_info: Optional[Dict] = None
    ) -> str:
        """Store meal/supplement image data in MongoDB"""
        collection = get_collection(COLLECTION_MEAL_IMAGES)

        doc = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "image_path": image_path,
            "image_format": image_path.split('.')[-1],
            "detected_foods": detected_foods,
            "ocr_text": ocr_text,
            "extracted_info": extracted_info,
            "created_at": datetime.now()
        }

        result = await collection.insert_one(doc)
        return str(result.inserted_id)
