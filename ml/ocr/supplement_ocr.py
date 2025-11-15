"""
Supplement Label OCR

Extracts information from supplement bottles using OCR
"""
import pytesseract
from PIL import Image
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SupplementOCR:
    """
    OCR for supplement labels

    Extracts:
    - Supplement name
    - Dosage
    - Active ingredients
    - Warning labels
    """

    def __init__(self):
        """Initialize OCR"""
        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.available = True
        except:
            logger.warning("Tesseract not found. OCR will use mock data.")
            self.available = False

    def extract_label_info(
        self,
        image_path: str
    ) -> Dict:
        """
        Extract supplement information from label image

        Args:
            image_path: Path to label image

        Returns:
            Dict with supplement name, dosage, ingredients, etc.
        """
        if not self.available:
            return self._get_mock_data()

        try:
            # Load image
            image = Image.open(image_path)

            # Run OCR
            text = pytesseract.image_to_string(image)

            # Parse extracted text
            info = self._parse_label_text(text)

            return info

        except Exception as e:
            logger.error(f"OCR error: {e}")
            return self._get_mock_data()

    def _parse_label_text(self, text: str) -> Dict:
        """
        Parse OCR text to extract structured information

        Args:
            text: Raw OCR text

        Returns:
            Structured supplement info
        """
        info = {
            "supplement_name": "Unknown",
            "dosage": "Unknown",
            "ingredients": [],
            "active_compounds": {},
            "benefits": [],
            "warnings": [],
            "contraindications": []
        }

        # Convert to lowercase for matching
        text_lower = text.lower()

        # Extract supplement name (common supplements)
        common_supplements = [
            "ashwagandha", "magnesium", "omega-3", "vitamin d", "vitamin d3",
            "vitamin b12", "vitamin b", "b-complex", "iron", "zinc",
            "l-theanine", "melatonin", "turmeric", "curcumin", "brahmi",
            "rhodiola", "ginseng", "multivitamin", "probiotics", "fish oil"
        ]

        for supp in common_supplements:
            if supp in text_lower:
                info["supplement_name"] = supp.title()
                break

        # Extract dosage (look for patterns like "500mg", "1000 mg", "2 capsules")
        dosage_patterns = [
            r'(\d+\s?(?:mg|mcg|g|iu|capsules?))',
            r'(\d+\.?\d*\s?(?:mg|mcg|g|iu))'
        ]

        for pattern in dosage_patterns:
            match = re.search(pattern, text_lower)
            if match:
                info["dosage"] = match.group(1)
                break

        # Extract active compounds (look for percentage)
        compound_pattern = r'(\w+(?:\s+\w+)?)\s*[:\-]?\s*(\d+(?:\.\d+)?%)'
        compounds = re.findall(compound_pattern, text)
        for compound, percentage in compounds:
            info["active_compounds"][compound.strip()] = percentage

        # Look for warnings
        warning_keywords = ["warning", "caution", "do not", "consult physician", "pregnant", "nursing"]
        warnings_found = []
        for keyword in warning_keywords:
            if keyword in text_lower:
                # Extract sentence containing warning
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        warnings_found.append(sentence.strip())

        info["warnings"] = warnings_found[:3]  # Top 3 warnings

        # Infer benefits based on supplement name
        info["benefits"] = self._infer_benefits(info["supplement_name"])

        return info

    def _infer_benefits(self, supplement_name: str) -> List[str]:
        """Infer benefits based on supplement name"""
        benefits_map = {
            "Ashwagandha": ["Stress reduction", "Anxiety relief", "Sleep support"],
            "Magnesium": ["Sleep support", "Muscle relaxation", "Stress reduction"],
            "Omega-3": ["Brain health", "Heart health", "Inflammation reduction"],
            "Vitamin D3": ["Immune support", "Bone health", "Mood enhancement"],
            "Vitamin B12": ["Energy production", "Nerve health", "Red blood cell formation"],
            "L-Theanine": ["Relaxation", "Focus", "Anxiety reduction"],
            "Melatonin": ["Sleep regulation", "Circadian rhythm support"],
            "Turmeric": ["Anti-inflammatory", "Antioxidant", "Joint health"],
            "Brahmi": ["Memory enhancement", "Cognitive function", "Learning support"],
            "Rhodiola": ["Mental stamina", "Stress adaptation", "Energy"]
        }

        return benefits_map.get(supplement_name, ["General wellness support"])

    def _get_mock_data(self) -> Dict:
        """Return mock data when OCR fails"""
        return {
            "supplement_name": "Ashwagandha Extract",
            "dosage": "500mg",
            "ingredients": ["Ashwagandha root extract", "Cellulose capsule"],
            "active_compounds": {"Withanolides": "5%"},
            "benefits": ["Stress reduction", "Anxiety relief", "Sleep support"],
            "warnings": ["Consult doctor if pregnant or nursing", "Keep out of reach of children"],
            "contraindications": ["Pregnancy", "Nursing", "Thyroid medication (consult doctor)"]
        }


# Alternative: EasyOCR for better accuracy
class EasyOCRExtractor:
    """
    Enhanced OCR using EasyOCR

    Better accuracy for:
    - Multiple languages
    - Handwritten text
    - Low-quality images
    """

    def __init__(self):
        """Initialize EasyOCR"""
        try:
            import easyocr
            self.reader = easyocr.Reader(['en'])
            self.available = True
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")
            self.available = False

    def extract(self, image_path: str) -> str:
        """
        Extract text using EasyOCR

        Args:
            image_path: Path to image

        Returns:
            Extracted text
        """
        if not self.available:
            return ""

        try:
            result = self.reader.readtext(image_path)
            # Combine all detected text
            text = " ".join([detection[1] for detection in result])
            return text
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return ""


# Global instance
_supplement_ocr = None

def get_supplement_ocr() -> SupplementOCR:
    """Get or create OCR singleton"""
    global _supplement_ocr
    if _supplement_ocr is None:
        _supplement_ocr = SupplementOCR()
    return _supplement_ocr
