"""
OCR for Supplement Label Scanning
Extracts supplement information from product labels
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from PIL import Image
import numpy as np
import cv2
import easyocr
import pytesseract

logger = logging.getLogger(__name__)


class SupplementLabelScanner:
    """
    Extract supplement information from product labels using OCR

    Extracts:
    - Supplement name
    - Active ingredients and dosages
    - Serving size
    - Warnings and contraindications
    """

    def __init__(
        self,
        use_easyocr: bool = True,
        languages: List[str] = ['en']
    ):
        """
        Initialize OCR scanner

        Args:
            use_easyocr: Use EasyOCR (more accurate) vs Tesseract (faster)
            languages: Languages to recognize
        """
        self.use_easyocr = use_easyocr

        if use_easyocr:
            try:
                self.reader = easyocr.Reader(languages, gpu=True)
                logger.info("Initialized EasyOCR reader")
            except Exception as e:
                logger.warning(f"Could not initialize EasyOCR with GPU: {e}")
                try:
                    self.reader = easyocr.Reader(languages, gpu=False)
                    logger.info("Initialized EasyOCR reader (CPU)")
                except Exception as e:
                    logger.error(f"Could not initialize EasyOCR: {e}")
                    logger.info("Falling back to Tesseract")
                    self.use_easyocr = False

        # Load supplement database for matching
        self.supplement_db = self._load_supplement_database()

        # Common supplement ingredients patterns
        self.ingredient_patterns = [
            r"(\w+)\s+(\d+\.?\d*)\s*(mg|g|mcg|iu|%)",  # e.g., "Vitamin D 1000 IU"
            r"(\w+)\s+(\d+\.?\d*)\s*(milligram|gram|microgram)",
        ]

    def _load_supplement_database(self) -> Dict:
        """Load known supplement database"""
        from config.settings import settings

        supplements_path = Path(settings.KB_DIR) / "supplements" / "supplements_db.json"

        if supplements_path.exists():
            with open(supplements_path) as f:
                return json.load(f)
        else:
            logger.warning("Supplement database not found")
            return {}

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results

        Steps:
        - Convert to grayscale
        - Denoise
        - Enhance contrast
        - Binarize
        """
        # Load image
        image = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)

        # Enhance contrast (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Binarize (Otsu's thresholding)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def extract_text(self, image_path: str) -> str:
        """
        Extract all text from image using OCR

        Args:
            image_path: Path to label image

        Returns:
            Extracted text
        """
        if self.use_easyocr:
            # Use EasyOCR
            try:
                results = self.reader.readtext(image_path)
                text = " ".join([result[1] for result in results])
                return text
            except Exception as e:
                logger.error(f"EasyOCR error: {e}")
                # Fall back to Tesseract
                return self._extract_text_tesseract(image_path)
        else:
            # Use Tesseract
            return self._extract_text_tesseract(image_path)

    def _extract_text_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR"""
        try:
            # Preprocess image
            processed = self.preprocess_image(image_path)

            # OCR
            text = pytesseract.image_to_string(processed)
            return text
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""

    def parse_supplement_info(self, text: str) -> Dict[str, any]:
        """
        Parse supplement information from extracted text

        Args:
            text: OCR extracted text

        Returns:
            Structured supplement information
        """
        text_lower = text.lower()

        result = {
            "supplement_name": None,
            "ingredients": [],
            "serving_size": None,
            "warnings": [],
            "matched_database_entry": None,
        }

        # Extract supplement name (usually in first few lines or largest text)
        lines = text.split('\n')
        for line in lines[:5]:
            # Check if matches known supplement
            for supp_name in self.supplement_db.keys():
                if supp_name.lower() in line.lower():
                    result["supplement_name"] = supp_name
                    result["matched_database_entry"] = self.supplement_db[supp_name]
                    break
            if result["supplement_name"]:
                break

        # If no match, use first substantial line as name
        if not result["supplement_name"]:
            for line in lines:
                if len(line.strip()) > 3 and not line.strip().isdigit():
                    result["supplement_name"] = line.strip()
                    break

        # Extract ingredients and dosages
        ingredients = self._extract_ingredients(text)
        result["ingredients"] = ingredients

        # Extract serving size
        serving_size = self._extract_serving_size(text)
        result["serving_size"] = serving_size

        # Extract warnings
        warnings = self._extract_warnings(text)
        result["warnings"] = warnings

        return result

    def _extract_ingredients(self, text: str) -> List[Dict[str, any]]:
        """Extract ingredients with dosages"""
        ingredients = []

        # Pattern matching for ingredients
        for pattern in self.ingredient_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                ingredient_name = match.group(1)
                dosage_value = match.group(2)
                dosage_unit = match.group(3)

                # Clean up ingredient name
                ingredient_name = ingredient_name.strip().title()

                # Skip if too short or common words
                if len(ingredient_name) < 3 or ingredient_name.lower() in ['per', 'serving', 'size', 'daily']:
                    continue

                ingredients.append({
                    "name": ingredient_name,
                    "dosage": f"{dosage_value} {dosage_unit.lower()}",
                    "amount": float(dosage_value),
                    "unit": dosage_unit.lower()
                })

        # Remove duplicates
        unique_ingredients = []
        seen = set()
        for ing in ingredients:
            key = (ing["name"], ing["dosage"])
            if key not in seen:
                seen.add(key)
                unique_ingredients.append(ing)

        return unique_ingredients

    def _extract_serving_size(self, text: str) -> Optional[str]:
        """Extract serving size information"""
        # Patterns for serving size
        patterns = [
            r"serving size:?\s*(\d+\.?\d*)\s*(\w+)",
            r"(\d+\.?\d*)\s*(capsule|tablet|softgel|scoop|gummies?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} {match.group(2)}"

        return None

    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warning information"""
        warnings = []

        text_lower = text.lower()

        # Common warning keywords
        warning_keywords = [
            "do not",
            "consult",
            "doctor",
            "physician",
            "pregnant",
            "nursing",
            "allergic",
            "medication",
            "not intended",
            "fda",
            "side effect",
        ]

        # Split into sentences
        sentences = re.split(r'[.!?]', text)

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Check if sentence contains warning keywords
            if any(keyword in sentence_lower for keyword in warning_keywords):
                warning_text = sentence.strip()
                if len(warning_text) > 10:  # Filter out too short
                    warnings.append(warning_text)

        return warnings

    def scan_label(
        self,
        image_path: str,
        verify_safety: bool = True
    ) -> Dict[str, any]:
        """
        Complete label scanning pipeline

        Args:
            image_path: Path to supplement label image
            verify_safety: Check for contraindications

        Returns:
            Complete supplement information
        """
        logger.info(f"Scanning supplement label: {image_path}")

        # Extract text
        text = self.extract_text(image_path)

        if not text or len(text) < 10:
            return {
                "success": False,
                "error": "Could not extract sufficient text from image",
            }

        # Parse information
        parsed_info = self.parse_supplement_info(text)

        # Add safety information if matched to database
        if parsed_info["matched_database_entry"] and verify_safety:
            db_entry = parsed_info["matched_database_entry"]

            parsed_info["safety_info"] = {
                "contraindications": db_entry.get("contraindications", []),
                "drug_interactions": db_entry.get("drug_interactions", []),
                "recommended_dosage": db_entry.get("dosage", {}),
            }

            # Check if scanned dosage exceeds recommended
            if parsed_info["ingredients"]:
                dosage_warnings = self._check_dosage_safety(
                    parsed_info["ingredients"],
                    db_entry.get("dosage", {})
                )
                if dosage_warnings:
                    parsed_info["dosage_warnings"] = dosage_warnings

        result = {
            "success": True,
            "supplement_info": parsed_info,
            "raw_text": text,
            "confidence": "high" if parsed_info["matched_database_entry"] else "medium"
        }

        logger.info(f"Successfully scanned: {parsed_info.get('supplement_name', 'Unknown')}")

        return result

    def _check_dosage_safety(
        self,
        scanned_ingredients: List[Dict],
        recommended_dosage: Dict
    ) -> List[str]:
        """Check if scanned dosage is safe compared to recommendations"""
        warnings = []

        # This is simplified - in production, do comprehensive dosage checking
        for ingredient in scanned_ingredients:
            amount = ingredient.get("amount", 0)

            # Check against typical ranges (simplified)
            if ingredient["name"].lower() == "vitamin d" and amount > 4000:
                warnings.append(f"Vitamin D dosage ({amount} IU) exceeds typical upper limit (4000 IU)")

            elif ingredient["name"].lower() == "vitamin a" and amount > 10000:
                warnings.append(f"Vitamin A dosage ({amount} IU) exceeds safe upper limit")

        return warnings

    def batch_scan(
        self,
        image_paths: List[str]
    ) -> List[Dict[str, any]]:
        """Scan multiple supplement labels"""
        results = []

        for image_path in image_paths:
            try:
                result = self.scan_label(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scanning {image_path}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "image_path": image_path
                })

        return results


def create_supplement_scanner() -> SupplementLabelScanner:
    """Factory function to create supplement scanner"""
    return SupplementLabelScanner(use_easyocr=True)
