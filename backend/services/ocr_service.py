"""
OCR Service for Supplement Labels

Extracts text and structured information from supplement bottle labels
"""
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from PIL import Image

from config.settings import settings

logger = logging.getLogger(__name__)


class SupplementOCR:
    """
    OCR for supplement labels with information extraction
    """

    def __init__(self):
        self.ocr_engine = settings.OCR_ENGINE

        # Initialize OCR reader
        if self.ocr_engine == "easyocr":
            try:
                import easyocr
                self.reader = easyocr.Reader(
                    [settings.OCR_LANGUAGES],
                    gpu=True if settings.DEBUG else False
                )
                logger.info("Initialized EasyOCR")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.reader = None
        else:
            # Use Tesseract
            try:
                import pytesseract
                self.reader = pytesseract
                logger.info("Initialized Tesseract OCR")
            except Exception as e:
                logger.error(f"Failed to initialize Tesseract: {e}")
                self.reader = None

    def extract_text(self, file_path: str) -> str:
        """Extract all text from image"""
        try:
            image = Image.open(file_path)

            if self.ocr_engine == "easyocr" and self.reader:
                # EasyOCR
                results = self.reader.readtext(file_path)
                # Combine all text
                text = " ".join([result[1] for result in results])
            else:
                # Tesseract
                if self.reader:
                    text = self.reader.image_to_string(image)
                else:
                    logger.error("OCR reader not available")
                    return ""

            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

    def parse_supplement_info(self, text: str) -> Dict[str, Any]:
        """
        Parse supplement information from OCR text

        Extracts:
        - Supplement name
        - Dosage/serving size
        - Ingredients
        - Warnings/contraindications
        """
        info = {
            "name": None,
            "serving_size": None,
            "ingredients": [],
            "warnings": [],
            "dosage": None,
            "raw_text": text
        }

        # Clean text
        text_lower = text.lower()

        # Extract supplement name (usually first line or near "supplement" keyword)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Try to find name near keywords
            for line in lines[:5]:  # Check first 5 lines
                if len(line.split()) <= 5 and len(line) > 3:  # Short phrase
                    if not any(skip in line.lower() for skip in ['serving', 'size', 'amount', 'warning', 'dietary']):
                        info["name"] = line
                        break

            if not info["name"] and lines:
                info["name"] = lines[0]  # Fallback to first line

        # Extract serving size
        serving_pattern = r'serving\s+size[:\s]+(\d+(?:\.\d+)?)\s*(\w+)'
        match = re.search(serving_pattern, text_lower)
        if match:
            info["serving_size"] = f"{match.group(1)} {match.group(2)}"

        # Extract dosage/amount
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|iu|units?)',
            r'amount\s+per\s+serving[:\s]+(\d+(?:\.\d+)?)\s*(\w+)',
        ]

        for pattern in dosage_patterns:
            match = re.search(pattern, text_lower)
            if match:
                info["dosage"] = f"{match.group(1)} {match.group(2)}"
                break

        # Extract ingredients (usually after "ingredients:" or "contains:")
        ingredients_pattern = r'ingredients?[:\s]+([^\n]+)'
        match = re.search(ingredients_pattern, text_lower)
        if match:
            ingredients_text = match.group(1)
            # Split by comma or semicolon
            ingredients = re.split(r'[,;]', ingredients_text)
            info["ingredients"] = [ing.strip() for ing in ingredients if ing.strip()]

        # Extract warnings
        warning_keywords = ['warning', 'caution', 'do not', 'contraindication', 'avoid']
        for line in lines:
            if any(keyword in line.lower() for keyword in warning_keywords):
                info["warnings"].append(line.strip())

        logger.info(f"Parsed supplement info: {info['name']}, {info['dosage']}")

        return info

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Complete OCR analysis of supplement label

        Args:
            file_path: Path to supplement label image

        Returns:
            Dict with extracted information
        """
        try:
            # Extract text
            text = self.extract_text(file_path)

            if not text:
                return {
                    "success": False,
                    "message": "No text detected in image",
                    "extracted_info": {}
                }

            # Parse information
            info = self.parse_supplement_info(text)

            result = {
                "success": True,
                "message": f"Extracted information for {info.get('name', 'unknown supplement')}",
                "extracted_info": info,
                "text_length": len(text)
            }

            logger.info(f"OCR analysis complete: {result['message']}")

            return result

        except Exception as e:
            logger.error(f"Error in OCR analysis: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "extracted_info": {}
            }


# Global OCR instance
_ocr = None


def get_supplement_ocr() -> SupplementOCR:
    """Get or create OCR instance"""
    global _ocr
    if _ocr is None:
        _ocr = SupplementOCR()
    return _ocr
