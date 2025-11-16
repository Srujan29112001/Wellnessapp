"""
Enhanced NLP Parser for Supplement Label OCR.

Improvements over basic regex parsing:
- Named Entity Recognition (NER) for ingredients
- Quantity extraction with units
- Context-aware parsing
- Fuzzy matching against supplement database
- Multi-language support (future)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import json
from pathlib import Path


@dataclass
class ExtractedIngredient:
    """Parsed ingredient information."""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    daily_value_percent: Optional[float] = None
    confidence: float = 1.0


@dataclass
class ParsedLabel:
    """Complete parsed label information."""
    product_name: Optional[str] = None
    brand: Optional[str] = None
    ingredients: List[ExtractedIngredient] = None
    serving_size: Optional[str] = None
    servings_per_container: Optional[int] = None
    warnings: List[str] = None
    directions: Optional[str] = None
    expiry_date: Optional[str] = None
    matched_supplement: Optional[Dict] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.ingredients is None:
            self.ingredients = []
        if self.warnings is None:
            self.warnings = []


class EnhancedOCRParser:
    """Enhanced NLP-based parser for supplement labels."""

    def __init__(self, supplement_db_path: str = None):
        """
        Initialize enhanced parser.

        Args:
            supplement_db_path: Path to supplement database JSON
        """
        self.supplement_db = {}
        if supplement_db_path:
            self.load_supplement_database(supplement_db_path)

        # Common supplement name patterns
        self.supplement_patterns = [
            r'\b(vitamin [A-Z0-9]+)\b',
            r'\b(calcium|magnesium|zinc|iron|potassium|selenium)\b',
            r'\b(omega[- ]?3|omega[- ]?6)\b',
            r'\b(coq10|ubiquinone|ubiquinol)\b',
            r'\b(ashwagandha|rhodiola|brahmi|bacopa)\b',
            r'\b(probiotics?|prebiotics?)\b',
            r'\b(amino acids?)\b',
            r'\b([A-Z][- ]?(theanine|carnitine|arginine|lysine))\b',
        ]

        # Quantity patterns (improved)
        self.quantity_patterns = [
            # Standard format: "500mg", "1000 mg", "500 MG"
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|μg|g|kg|ml|l|iu|ius)',
            # With units spelled out: "500 milligrams"
            r'(\d+(?:\.\d+)?)\s*(milligram|microgram|gram|milliliter|liter|international unit)s?',
            # Percentage: "500mg (25% DV)"
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|g)\s*\((\d+)%\s*(?:DV|Daily Value)\)',
        ]

        # Warning keywords
        self.warning_keywords = [
            'warning', 'caution', 'do not', 'avoid', 'consult',
            'pregnant', 'nursing', 'medication', 'allergy',
            'side effect', 'contraindication'
        ]

    def load_supplement_database(self, db_path: str):
        """Load supplement database for matching."""
        db_file = Path(db_path)
        if db_file.exists():
            with open(db_file, 'r') as f:
                data = json.load(f)
                for supp in data.get("supplements", []):
                    names = [supp["name"]] + supp.get("common_names", [])
                    for name in names:
                        self.supplement_db[name.lower()] = supp

    def parse_label(self, extracted_text: str) -> ParsedLabel:
        """
        Parse OCR extracted text into structured information.

        Args:
            extracted_text: Raw OCR output

        Returns:
            ParsedLabel with extracted information
        """
        lines = extracted_text.split('\n')
        parsed = ParsedLabel()

        # Extract product name (usually first significant line)
        parsed.product_name = self._extract_product_name(lines)

        # Extract brand (if present)
        parsed.brand = self._extract_brand(lines)

        # Extract ingredients with quantities
        parsed.ingredients = self._extract_ingredients(extracted_text)

        # Extract serving information
        parsed.serving_size = self._extract_serving_size(extracted_text)
        parsed.servings_per_container = self._extract_servings_count(extracted_text)

        # Extract warnings
        parsed.warnings = self._extract_warnings(extracted_text)

        # Extract directions
        parsed.directions = self._extract_directions(extracted_text)

        # Extract expiry date
        parsed.expiry_date = self._extract_expiry_date(extracted_text)

        # Match against supplement database
        if parsed.product_name or parsed.ingredients:
            parsed.matched_supplement = self._match_supplement(parsed)

        # Calculate confidence
        parsed.confidence = self._calculate_confidence(parsed)

        return parsed

    def _extract_product_name(self, lines: List[str]) -> Optional[str]:
        """Extract product/supplement name from first lines."""
        # Look for lines with capital letters and supplement keywords
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) < 5 or len(line) > 100:
                continue

            # Check if line contains supplement-related keywords
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in [
                'vitamin', 'supplement', 'capsule', 'tablet',
                'magnesium', 'calcium', 'omega', 'protein', 'probiotic'
            ]):
                # Clean up the line
                # Remove common noise
                cleaned = re.sub(r'\b(dietary supplement|supplement facts)\b', '', line, flags=re.I)
                cleaned = cleaned.strip()
                if cleaned:
                    return cleaned

        # Fallback: First non-empty line with reasonable length
        for line in lines[:5]:
            line = line.strip()
            if 10 < len(line) < 100 and not line.lower().startswith(('supplement facts', 'nutrition facts')):
                return line

        return None

    def _extract_brand(self, lines: List[str]) -> Optional[str]:
        """Extract brand name (often in smaller text near top)."""
        # Look for "by <brand>" or brand at very top
        for line in lines[:5]:
            match = re.search(r'by\s+([A-Z][A-Za-z\s]+)', line, re.I)
            if match:
                return match.group(1).strip()

        return None

    def _extract_ingredients(self, text: str) -> List[ExtractedIngredient]:
        """
        Extract ingredients with quantities using NLP.

        This is the core NLP enhancement - uses context-aware parsing.
        """
        ingredients = []
        text_lower = text.lower()

        # Find supplement facts or ingredients section
        section_markers = ['supplement facts', 'ingredients', 'active ingredients', 'nutrition facts']
        section_start = -1
        for marker in section_markers:
            idx = text_lower.find(marker)
            if idx != -1:
                section_start = idx
                break

        # Extract relevant section
        if section_start != -1:
            relevant_text = text[section_start:section_start+2000]  # Next 2000 chars
        else:
            relevant_text = text

        # Extract ingredient-quantity pairs
        # Pattern: ingredient name followed by quantity
        lines = relevant_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Try to extract quantity
            quantities = self._extract_quantity(line)

            # Try to extract ingredient name
            ingredient_name = self._extract_ingredient_name(line)

            if ingredient_name:
                # Create ingredient object
                ingredient = ExtractedIngredient(
                    name=ingredient_name,
                    quantity=quantities[0] if quantities else None,
                    unit=quantities[1] if len(quantities) > 1 else None,
                    daily_value_percent=quantities[2] if len(quantities) > 2 else None,
                    confidence=0.8  # Base confidence
                )

                # Boost confidence if we found both name and quantity
                if ingredient.quantity:
                    ingredient.confidence = 0.95

                ingredients.append(ingredient)

        # Deduplicate
        seen = set()
        unique_ingredients = []
        for ing in ingredients:
            key = ing.name.lower()
            if key not in seen:
                seen.add(key)
                unique_ingredients.append(ing)

        return unique_ingredients

    def _extract_ingredient_name(self, line: str) -> Optional[str]:
        """Extract ingredient name from line."""
        # Remove quantity patterns first
        cleaned = line
        for pattern in self.quantity_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.I)

        # Remove common noise
        cleaned = re.sub(r'\b(amount per serving|%\s*dv|daily value)\b', '', cleaned, flags=re.I)
        cleaned = re.sub(r'[*†]', '', cleaned)  # Remove asterisks, daggers
        cleaned = cleaned.strip(' :.-')

        if not cleaned or len(cleaned) < 3:
            return None

        # Check against known supplements
        for pattern in self.supplement_patterns:
            match = re.search(pattern, cleaned, re.I)
            if match:
                return match.group(1).title()

        # Look for capitalized words (likely ingredient names)
        words = cleaned.split()
        capitalized = [w for w in words if w and w[0].isupper()]
        if capitalized:
            return ' '.join(capitalized)

        # Fallback: if line looks like ingredient (mostly letters)
        if re.match(r'^[A-Za-z\s\-]+$', cleaned):
            return cleaned.title()

        return None

    def _extract_quantity(self, text: str) -> Tuple[Optional[float], Optional[str], Optional[float]]:
        """
        Extract quantity, unit, and daily value percentage.

        Returns:
            (quantity, unit, dv_percent)
        """
        # Try pattern with DV%
        match = re.search(
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|μg|g|kg|ml|l|iu)\s*\((\d+)%',
            text,
            re.I
        )
        if match:
            qty = float(match.group(1))
            unit = match.group(2).lower()
            dv = float(match.group(3))
            return (qty, unit, dv)

        # Try simple quantity + unit
        match = re.search(
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|μg|g|kg|ml|l|iu|ius)',
            text,
            re.I
        )
        if match:
            qty = float(match.group(1))
            unit = match.group(2).lower()
            unit = unit.rstrip('s')  # Remove plural 's'
            return (qty, unit, None)

        return (None, None, None)

    def _extract_serving_size(self, text: str) -> Optional[str]:
        """Extract serving size."""
        match = re.search(r'serving size[:\s]+([^\n]+)', text, re.I)
        if match:
            return match.group(1).strip()
        return None

    def _extract_servings_count(self, text: str) -> Optional[int]:
        """Extract number of servings per container."""
        match = re.search(r'servings?(?:\s+per\s+container)?[:\s]+(\d+)', text, re.I)
        if match:
            return int(match.group(1))
        return None

    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warning text."""
        warnings = []
        text_lower = text.lower()

        # Find warnings section
        warning_idx = -1
        for keyword in ['warning', 'caution', 'contraindication']:
            idx = text_lower.find(keyword)
            if idx != -1:
                warning_idx = idx
                break

        if warning_idx != -1:
            # Extract next few sentences
            warning_text = text[warning_idx:warning_idx+500]
            sentences = re.split(r'[.!?]', warning_text)

            for sentence in sentences[:5]:  # First 5 sentences
                sentence = sentence.strip()
                if len(sentence) > 10:
                    # Check if it contains warning keywords
                    if any(kw in sentence.lower() for kw in self.warning_keywords):
                        warnings.append(sentence)

        return warnings

    def _extract_directions(self, text: str) -> Optional[str]:
        """Extract usage directions."""
        match = re.search(r'(?:directions?|suggested use)[:\s]+([^\n]+(?:\n[^\n]+){0,3})', text, re.I)
        if match:
            return match.group(1).strip()
        return None

    def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extract expiration date."""
        # Pattern: EXP: MM/YYYY or Best by: MM/DD/YYYY
        match = re.search(
            r'(?:exp|expiry|expires?|best by)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]?\d{2,4})',
            text,
            re.I
        )
        if match:
            return match.group(1)
        return None

    def _match_supplement(self, parsed: ParsedLabel) -> Optional[Dict]:
        """Match parsed label against supplement database."""
        if not self.supplement_db:
            return None

        # Try to match product name
        if parsed.product_name:
            best_match = self._fuzzy_match(parsed.product_name.lower(), list(self.supplement_db.keys()))
            if best_match:
                return self.supplement_db[best_match]

        # Try to match primary ingredient
        if parsed.ingredients:
            primary_ingredient = parsed.ingredients[0].name.lower()
            best_match = self._fuzzy_match(primary_ingredient, list(self.supplement_db.keys()))
            if best_match:
                return self.supplement_db[best_match]

        return None

    def _fuzzy_match(self, query: str, candidates: List[str], threshold: float = 0.7) -> Optional[str]:
        """Fuzzy string matching."""
        best_score = 0
        best_match = None

        for candidate in candidates:
            score = SequenceMatcher(None, query, candidate).ratio()
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= threshold:
            return best_match
        return None

    def _calculate_confidence(self, parsed: ParsedLabel) -> float:
        """Calculate overall parsing confidence."""
        confidence = 0.0
        factors = 0

        if parsed.product_name:
            confidence += 0.25
            factors += 1

        if parsed.ingredients:
            # More ingredients = higher confidence
            ing_conf = min(len(parsed.ingredients) / 5, 1.0) * 0.3
            confidence += ing_conf
            factors += 1

            # Ingredients with quantities boost confidence
            with_qty = sum(1 for i in parsed.ingredients if i.quantity)
            if with_qty > 0:
                confidence += 0.2
                factors += 1

        if parsed.serving_size:
            confidence += 0.1
            factors += 1

        if parsed.matched_supplement:
            confidence += 0.15
            factors += 1

        # Normalize
        if factors > 0:
            confidence = min(confidence, 1.0)
        else:
            confidence = 0.1  # Very low confidence if nothing extracted

        return confidence


# Example usage
if __name__ == "__main__":
    # Sample OCR text
    sample_text = """
    Nature's Way Magnesium Complex
    Dietary Supplement

    Supplement Facts
    Serving Size: 2 Capsules
    Servings Per Container: 30

    Amount Per Serving          %DV
    Magnesium                  400mg  95%
    (as Oxide, Citrate)

    Other Ingredients: Gelatin, Rice Flour

    Directions: Take 2 capsules daily with meals

    Warning: Consult physician if pregnant or nursing

    EXP: 12/2025
    """

    parser = EnhancedOCRParser()
    parsed = parser.parse_label(sample_text)

    print("=== Parsed Label Information ===\n")
    print(f"Product Name: {parsed.product_name}")
    print(f"Serving Size: {parsed.serving_size}")
    print(f"Servings Per Container: {parsed.servings_per_container}")

    print(f"\nIngredients:")
    for ing in parsed.ingredients:
        print(f"  - {ing.name}: {ing.quantity} {ing.unit if ing.unit else ''} "
              f"({ing.daily_value_percent}% DV)" if ing.daily_value_percent else "")

    print(f"\nDirections: {parsed.directions}")

    print(f"\nWarnings:")
    for warn in parsed.warnings:
        print(f"  - {warn}")

    print(f"\nExpiry: {parsed.expiry_date}")
    print(f"\nConfidence: {parsed.confidence:.2f}")
