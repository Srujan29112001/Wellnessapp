"""
Supplement Label OCR Scanner

This module extracts supplement information from bottle/label images using:
- Tesseract OCR or EasyOCR
- Text parsing and extraction
- Matching against supplement database
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from PIL import Image
import numpy as np


class SupplementOCR:
    """
    OCR system for supplement labels
    """

    def __init__(
        self,
        ocr_engine: str = "tesseract",  # or "easyocr"
        knowledge_base_path: str = "/home/user/Wellnessapp/knowledge_base"
    ):
        self.ocr_engine = ocr_engine
        self.knowledge_base_path = Path(knowledge_base_path)

        # Initialize OCR engine
        self.ocr = None
        self._initialize_ocr()

        # Load supplement database
        self.supplement_db = self._load_supplement_database()

    def _initialize_ocr(self):
        """Initialize OCR engine"""
        if self.ocr_engine == "tesseract":
            try:
                import pytesseract
                self.ocr = pytesseract
                print("✅ Using Tesseract OCR")
            except ImportError:
                print("Tesseract not available, trying EasyOCR")
                self.ocr_engine = "easyocr"

        if self.ocr_engine == "easyocr":
            try:
                import easyocr
                self.ocr = easyocr.Reader(['en'], gpu=False)
                print("✅ Using EasyOCR")
            except ImportError:
                print("❌ No OCR engine available")
                self.ocr = None

    def _load_supplement_database(self) -> Dict:
        """Load supplement database"""
        supplements_file = self.knowledge_base_path / "supplements" / "supplements_db.json"

        if supplements_file.exists():
            with open(supplements_file) as f:
                data = json.load(f)
                # Create lookup dictionary
                db = {}
                for supp in data.get("supplements", []):
                    # Index by name and common names
                    names = [supp["name"]] + supp.get("common_names", [])
                    for name in names:
                        db[name.lower()] = supp
                return db
        return {}

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        """
        from PIL import ImageEnhance, ImageFilter

        # Convert to grayscale
        image = image.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)

        # Resize if too small
        width, height = image.size
        if width < 600:
            scale = 600 / width
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def extract_text(
        self,
        image_path: str = None,
        image: Image.Image = None
    ) -> str:
        """
        Extract text from image using OCR
        """
        # Load image
        if image_path:
            image = Image.open(image_path).convert("RGB")
        elif image is None:
            raise ValueError("Either image_path or image must be provided")

        # Preprocess
        processed_image = self.preprocess_image(image)

        # Run OCR
        if self.ocr_engine == "tesseract" and self.ocr:
            try:
                text = self.ocr.image_to_string(processed_image)
            except Exception as e:
                print(f"Tesseract error: {e}")
                text = ""

        elif self.ocr_engine == "easyocr" and self.ocr:
            try:
                result = self.ocr.readtext(np.array(processed_image))
                text = " ".join([detection[1] for detection in result])
            except Exception as e:
                print(f"EasyOCR error: {e}")
                text = ""
        else:
            # Fallback: return empty string
            text = ""

        return text

    def parse_supplement_info(self, text: str) -> Dict:
        """
        Parse supplement information from extracted text

        Extracts:
        - Supplement name
        - Dosage/strength
        - Active ingredients
        - Serving size
        - Warnings
        """
        text_lower = text.lower()
        lines = text.split('\n')

        info = {
            "raw_text": text,
            "supplement_name": None,
            "dosage": None,
            "serving_size": None,
            "ingredients": [],
            "active_compounds": {},
            "warnings": [],
            "matched_supplement": None
        }

        # Extract supplement name (match against database)
        for name, supp_data in self.supplement_db.items():
            if name in text_lower:
                info["supplement_name"] = supp_data["name"]
                info["matched_supplement"] = supp_data
                break

        # If no match, try to extract from first few lines
        if not info["supplement_name"]:
            # Heuristic: supplement name is usually in first 3 lines
            for line in lines[:3]:
                line_clean = line.strip()
                if len(line_clean) > 3 and len(line_clean) < 50:
                    # Check if it contains common supplement keywords
                    if any(kw in line_clean.lower() for kw in [
                        "vitamin", "mineral", "omega", "extract", "supplement",
                        "capsule", "tablet", "mg", "iu", "acid"
                    ]):
                        info["supplement_name"] = line_clean.title()
                        break

        # Extract dosage/strength (patterns like "500mg", "1000 IU", "25mcg")
        dosage_pattern = r'(\d+\s*(mg|mcg|g|iu|ml))'
        dosages = re.findall(dosage_pattern, text_lower)
        if dosages:
            info["dosage"] = dosages[0][0].upper()

        # Extract serving size
        serving_patterns = [
            r'serving size[:\s]+(\d+\s*\w+)',
            r'take\s+(\d+\s*\w+)',
            r'(\d+\s*capsule|tablet|softgel)'
        ]
        for pattern in serving_patterns:
            match = re.search(pattern, text_lower)
            if match:
                info["serving_size"] = match.group(1)
                break

        # Extract ingredients (look for "ingredients" section)
        ingredients_idx = -1
        for i, line in enumerate(lines):
            if "ingredient" in line.lower():
                ingredients_idx = i
                break

        if ingredients_idx >= 0:
            # Get next few lines after "ingredients"
            ingredient_lines = lines[ingredients_idx+1:ingredients_idx+6]
            for line in ingredient_lines:
                clean_line = line.strip()
                if clean_line and len(clean_line) > 2:
                    info["ingredients"].append(clean_line)

        # Extract warnings
        warning_keywords = ["warning", "caution", "do not", "consult", "pregnant", "nursing"]
        for line in lines:
            if any(kw in line.lower() for kw in warning_keywords):
                info["warnings"].append(line.strip())

        # Extract active compounds percentages
        compound_pattern = r'(\w+(?:\s+\w+)?)\s*:?\s*(\d+(?:\.\d+)?)\s*%'
        compounds = re.findall(compound_pattern, text)
        if compounds:
            for compound, percentage in compounds:
                info["active_compounds"][compound.strip()] = f"{percentage}%"

        return info

    def enrich_with_database(self, parsed_info: Dict) -> Dict:
        """
        Enrich parsed information with database knowledge
        """
        if parsed_info.get("matched_supplement"):
            supp = parsed_info["matched_supplement"]

            # Add benefits
            parsed_info["benefits"] = supp.get("benefits", [])

            # Add contraindications
            parsed_info["contraindications"] = supp.get("contraindications", [])

            # Add recommended dosage
            if "dosage" in supp:
                parsed_info["recommended_dosage"] = supp["dosage"].get("typical", "")

            # Add interactions
            parsed_info["interactions"] = supp.get("interactions", [])

            # Add evidence level
            parsed_info["evidence_level"] = supp.get("evidence_level", "unknown")

        return parsed_info

    def scan_supplement_label(
        self,
        image_path: str = None,
        image: Image.Image = None
    ) -> Dict:
        """
        Complete supplement label scanning pipeline

        Returns:
            Dict with supplement information, benefits, warnings, etc.
        """
        # Extract text via OCR
        text = self.extract_text(image_path=image_path, image=image)

        if not text:
            return {
                "success": False,
                "error": "Could not extract text from image",
                "supplement_name": None
            }

        # Parse supplement info
        parsed_info = self.parse_supplement_info(text)

        # Enrich with database
        enriched_info = self.enrich_with_database(parsed_info)

        # Add success flag
        enriched_info["success"] = bool(enriched_info.get("supplement_name"))

        return enriched_info

    def check_interactions(
        self,
        current_supplements: List[str],
        new_supplement: str
    ) -> List[Dict]:
        """
        Check for interactions between supplements

        Args:
            current_supplements: List of supplement names currently taking
            new_supplement: New supplement to check

        Returns:
            List of potential interactions
        """
        interactions = []

        # Get new supplement data
        new_supp_data = self.supplement_db.get(new_supplement.lower())
        if not new_supp_data:
            return interactions

        # Check each current supplement
        for current in current_supplements:
            current_data = self.supplement_db.get(current.lower())
            if not current_data:
                continue

            # Check if there are known interactions
            # This is simplified - real implementation would have interaction database
            new_interactions = new_supp_data.get("interactions", [])
            current_name = current_data["name"]

            # Heuristic: check if current supplement is mentioned in interactions
            for interaction in new_interactions:
                if current_name.lower() in interaction.lower() or current.lower() in interaction.lower():
                    interactions.append({
                        "supplement1": current_name,
                        "supplement2": new_supp_data["name"],
                        "interaction": interaction,
                        "severity": "moderate"  # Would need proper severity data
                    })

        return interactions


class SupplementRecommendationEngine:
    """
    Generate supplement recommendations based on scanned labels and user data
    """

    def __init__(self, knowledge_base_path: str = "/home/user/Wellnessapp/knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.supplement_db = self._load_supplement_database()

    def _load_supplement_database(self) -> Dict:
        """Load supplement database"""
        supplements_file = self.knowledge_base_path / "supplements" / "supplements_db.json"

        if supplements_file.exists():
            with open(supplements_file) as f:
                data = json.load(f)
                return {supp["name"]: supp for supp in data.get("supplements", [])}
        return {}

    def analyze_supplement_stack(
        self,
        supplements: List[str],
        user_goals: List[str] = None
    ) -> Dict:
        """
        Analyze a stack of supplements

        Args:
            supplements: List of supplement names
            user_goals: User health goals (e.g., ["stress reduction", "better sleep"])

        Returns:
            Analysis with coverage, gaps, and recommendations
        """
        analysis = {
            "total_supplements": len(supplements),
            "covered_benefits": set(),
            "gaps": [],
            "recommendations": [],
            "warnings": []
        }

        # Aggregate benefits
        for supp_name in supplements:
            supp_data = self.supplement_db.get(supp_name)
            if supp_data:
                analysis["covered_benefits"].update(supp_data.get("benefits", []))

        analysis["covered_benefits"] = list(analysis["covered_benefits"])

        # Check against user goals
        if user_goals:
            for goal in user_goals:
                goal_met = False
                for benefit in analysis["covered_benefits"]:
                    if goal.lower() in benefit.lower():
                        goal_met = True
                        break

                if not goal_met:
                    analysis["gaps"].append(goal)

                    # Recommend supplements for this goal
                    recommended = self._find_supplements_for_goal(goal)
                    if recommended:
                        analysis["recommendations"].extend(recommended[:2])  # Top 2

        # Check for redundancy
        if len(supplements) > 5:
            analysis["warnings"].append("Large supplement stack - consider if all are necessary")

        return analysis

    def _find_supplements_for_goal(self, goal: str) -> List[Dict]:
        """Find supplements that address a specific goal"""
        matches = []

        for supp_name, supp_data in self.supplement_db.items():
            for benefit in supp_data.get("benefits", []):
                if goal.lower() in benefit.lower():
                    matches.append({
                        "name": supp_name,
                        "benefit": benefit,
                        "evidence_level": supp_data.get("evidence_level", "moderate")
                    })
                    break

        return matches


# Convenience function
def scan_supplement(image_path: str) -> Dict:
    """
    Quick function to scan supplement label
    """
    scanner = SupplementOCR()
    return scanner.scan_supplement_label(image_path=image_path)
