"""
Astrological Wellness Service.

Integrates zodiac signs with Ayurvedic doshas and provides
personalized wellness recommendations based on astrological profile.
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ZodiacProfile:
    """Zodiac sign profile with health information."""
    sign: str
    element: str
    ruling_planet: str
    dates: str
    dosha_affinity: str
    dosha_reasoning: str
    health_strengths: List[str]
    health_vulnerabilities: List[str]
    wellness_recommendations: List[str]
    beneficial_foods: List[str]
    supplements_to_consider: List[str]
    exercise_recommendations: List[str]
    stress_triggers: List[str]
    ideal_sleep_routine: str
    planetary_periods: Dict[str, str]


class AstroWellnessService:
    """Service for astrological wellness insights."""

    def __init__(self, knowledge_base_path: str = "/home/user/Wellnessapp/knowledge_base"):
        """
        Initialize astrological wellness service.

        Args:
            knowledge_base_path: Path to knowledge base directory
        """
        self.kb_path = Path(knowledge_base_path)
        self.zodiac_data = self._load_zodiac_data()

        # Zodiac date ranges (MM-DD format)
        self.zodiac_dates = {
            "Capricorn": [(12, 22), (1, 19)],  # Dec 22 - Jan 19
            "Aquarius": [(1, 20), (2, 18)],
            "Pisces": [(2, 19), (3, 20)],
            "Aries": [(3, 21), (4, 19)],
            "Taurus": [(4, 20), (5, 20)],
            "Gemini": [(5, 21), (6, 20)],
            "Cancer": [(6, 21), (7, 22)],
            "Leo": [(7, 23), (8, 22)],
            "Virgo": [(8, 23), (9, 22)],
            "Libra": [(9, 23), (10, 22)],
            "Scorpio": [(10, 23), (11, 21)],
            "Sagittarius": [(11, 22), (12, 21)],
        }

    def _load_zodiac_data(self) -> Dict:
        """Load zodiac wellness knowledge base."""
        zodiac_file = self.kb_path / "astrology" / "zodiac_wellness.json"

        if zodiac_file.exists():
            with open(zodiac_file, 'r') as f:
                return json.load(f)
        else:
            print(f"⚠️  Zodiac wellness data not found at {zodiac_file}")
            return {"zodiac_signs": [], "dosha_zodiac_mapping": {}, "planetary_wellness_influences": {}}

    def get_zodiac_from_date(self, birth_date: date) -> str:
        """
        Determine zodiac sign from birth date.

        Args:
            birth_date: Date of birth

        Returns:
            Zodiac sign name
        """
        month = birth_date.month
        day = birth_date.day

        for sign, date_ranges in self.zodiac_dates.items():
            if len(date_ranges) == 2:  # Handle signs spanning two months
                (start_month, start_day), (end_month, end_day) = date_ranges

                if start_month == end_month:  # Same month (shouldn't happen but safe)
                    if month == start_month and start_day <= day <= end_day:
                        return sign
                else:  # Different months
                    if (month == start_month and day >= start_day) or \
                       (month == end_month and day <= end_day):
                        return sign

        return "Unknown"

    def get_zodiac_profile(self, zodiac_sign: str) -> Optional[ZodiacProfile]:
        """
        Get complete wellness profile for zodiac sign.

        Args:
            zodiac_sign: Name of zodiac sign

        Returns:
            ZodiacProfile with health information
        """
        for sign_data in self.zodiac_data.get("zodiac_signs", []):
            if sign_data["sign"].lower() == zodiac_sign.lower():
                return ZodiacProfile(**sign_data)

        return None

    def get_dosha_from_zodiac(self, zodiac_sign: str) -> str:
        """
        Get Ayurvedic dosha affinity from zodiac sign.

        Args:
            zodiac_sign: Zodiac sign name

        Returns:
            Dosha type (Vata, Pitta, Kapha, or Mixed)
        """
        mapping = self.zodiac_data.get("dosha_zodiac_mapping", {})

        # Check direct mappings
        for dosha, signs in mapping.items():
            if dosha != "Mixed" and zodiac_sign in signs:
                return dosha

        # Check mixed
        mixed = mapping.get("Mixed", {})
        if zodiac_sign in mixed:
            return mixed[zodiac_sign]

        # Fallback: check individual sign data
        profile = self.get_zodiac_profile(zodiac_sign)
        if profile:
            return profile.dosha_affinity

        return "Unknown"

    def get_personalized_recommendations(
        self,
        zodiac_sign: str,
        current_health_issues: Optional[List[str]] = None,
        current_season: Optional[str] = None
    ) -> Dict:
        """
        Get personalized wellness recommendations based on zodiac sign and context.

        Args:
            zodiac_sign: User's zodiac sign
            current_health_issues: List of current health concerns
            current_season: Current season (Spring, Summer, Fall, Winter)

        Returns:
            Dictionary with personalized recommendations
        """
        profile = self.get_zodiac_profile(zodiac_sign)
        if not profile:
            return {"error": f"Unknown zodiac sign: {zodiac_sign}"}

        recommendations = {
            "zodiac_sign": zodiac_sign,
            "dosha_affinity": profile.dosha_affinity,
            "element": profile.element,
            "general_recommendations": profile.wellness_recommendations,
            "dietary_recommendations": profile.beneficial_foods,
            "supplement_recommendations": profile.supplements_to_consider,
            "exercise_recommendations": profile.exercise_recommendations,
            "stress_management": [],
            "health_warnings": [],
            "seasonal_adjustments": []
        }

        # Add stress management based on triggers
        recommendations["stress_management"] = [
            f"Be aware of stress trigger: {trigger}" for trigger in profile.stress_triggers[:3]
        ]
        recommendations["stress_management"].append(
            f"Sleep guidance: {profile.ideal_sleep_routine}"
        )

        # Add health warnings based on vulnerabilities
        if current_health_issues:
            matched_vulnerabilities = [
                vuln for vuln in profile.health_vulnerabilities
                if any(issue.lower() in vuln.lower() for issue in current_health_issues)
            ]
            recommendations["health_warnings"] = matched_vulnerabilities

        # Add seasonal adjustments
        if current_season:
            seasonal_recs = self._get_seasonal_adjustments(profile, current_season)
            recommendations["seasonal_adjustments"] = seasonal_recs

        # Add planetary insights
        recommendations["planetary_insights"] = profile.planetary_periods

        return recommendations

    def _get_seasonal_adjustments(self, profile: ZodiacProfile, season: str) -> List[str]:
        """Get season-specific adjustments for zodiac sign."""
        adjustments = []

        # Fire signs (Aries, Leo, Sagittarius)
        if profile.element == "Fire":
            if season in ["Summer"]:
                adjustments.append("Summer intensifies your fire element - increase cooling foods and activities")
                adjustments.append("Stay hydrated and avoid excessive sun exposure")
            elif season in ["Winter"]:
                adjustments.append("Winter provides natural cooling - maintain but don't overdo heating practices")

        # Earth signs (Taurus, Virgo, Capricorn)
        elif profile.element == "Earth":
            if season in ["Spring"]:
                adjustments.append("Spring renewal helps overcome Kapha heaviness - emphasize lighter foods and more activity")
            elif season in ["Fall"]:
                adjustments.append("Fall transition can increase anxiety - maintain grounding routines")

        # Air signs (Gemini, Libra, Aquarius)
        elif profile.element == "Air":
            if season in ["Fall", "Winter"]:
                adjustments.append("Cold, dry seasons aggravate Vata - increase warm, moist, grounding foods")
                adjustments.append("Extra emphasis on routine and warmth during these months")
            elif season in ["Spring"]:
                adjustments.append("Spring's changeability resonates with you but can scatter energy - maintain focus practices")

        # Water signs (Cancer, Scorpio, Pisces)
        elif profile.element == "Water":
            if season in ["Spring"]:
                adjustments.append("Spring's dampness can increase Kapha - boost metabolism with spices and movement")
            elif season in ["Summer"]:
                adjustments.append("Summer heat can evaporate your water element - stay cool and hydrated")

        return adjustments

    def get_zodiac_dosha_compatibility(self, zodiac_sign: str, measured_dosha: str) -> Dict:
        """
        Check compatibility between zodiac-predicted dosha and measured dosha.

        Args:
            zodiac_sign: User's zodiac sign
            measured_dosha: Dosha determined by assessment quiz

        Returns:
            Compatibility analysis
        """
        zodiac_dosha = self.get_dosha_from_zodiac(zodiac_sign)

        compatibility = {
            "zodiac_sign": zodiac_sign,
            "zodiac_predicted_dosha": zodiac_dosha,
            "measured_dosha": measured_dosha,
            "match": zodiac_dosha.lower() == measured_dosha.lower() or \
                    measured_dosha in zodiac_dosha or \
                    zodiac_dosha in measured_dosha,
            "interpretation": ""
        }

        if compatibility["match"]:
            compatibility["interpretation"] = (
                f"Your assessed dosha ({measured_dosha}) aligns with your zodiac sign's "
                f"natural tendency ({zodiac_dosha}). This suggests your constitution is "
                f"strongly aligned with your astrological profile."
            )
        else:
            compatibility["interpretation"] = (
                f"Your assessed dosha ({measured_dosha}) differs from your zodiac sign's "
                f"typical affinity ({zodiac_dosha}). This can indicate either:\n"
                f"1. Current imbalance - you may be experiencing {measured_dosha} imbalance\n"
                f"2. Unique constitution - your individual prakriti differs from zodiac tendency\n"
                f"3. Environmental factors - lifestyle has shifted your current state\n\n"
                f"Consider balancing practices for {measured_dosha} while honoring your "
                f"{zodiac_dosha} tendencies."
            )

        return compatibility

    def get_current_planetary_guidance(self, zodiac_sign: str) -> List[str]:
        """
        Get current planetary guidance based on zodiac sign.

        Note: This is a simplified version. Full implementation would integrate
        real-time planetary ephemeris data.

        Args:
            zodiac_sign: User's zodiac sign

        Returns:
            List of current planetary guidance
        """
        profile = self.get_zodiac_profile(zodiac_sign)
        if not profile:
            return []

        guidance = []

        # Extract general planetary period guidance
        for period, advice in profile.planetary_periods.items():
            guidance.append(f"{period.replace('_', ' ').title()}: {advice}")

        # Add ruling planet guidance
        ruling_planet = profile.ruling_planet
        planetary_influences = self.zodiac_data.get("planetary_wellness_influences", {})

        if ruling_planet in planetary_influences:
            planet_info = planetary_influences[ruling_planet]
            guidance.append(
                f"\nYour ruling planet {ruling_planet} governs: {', '.join(planet_info['body_parts'])}"
            )
            guidance.append(
                f"Recommended supplements: {', '.join(planet_info['supplements'])}"
            )
            guidance.append(
                f"Focus: {planet_info['recommendations']}"
            )

        return guidance


# Singleton instance
_astro_service = None

def get_astro_wellness_service() -> AstroWellnessService:
    """Get singleton astrological wellness service."""
    global _astro_service
    if _astro_service is None:
        _astro_service = AstroWellnessService()
    return _astro_service


# Example usage
if __name__ == "__main__":
    print("=== Astrological Wellness Service Demo ===\n")

    service = AstroWellnessService()

    # Example 1: Get zodiac from birthday
    birth_date = date(1990, 7, 25)
    zodiac = service.get_zodiac_from_date(birth_date)
    print(f"Birth date: {birth_date}")
    print(f"Zodiac sign: {zodiac}\n")

    # Example 2: Get zodiac profile
    profile = service.get_zodiac_profile(zodiac)
    if profile:
        print(f"=== {profile.sign} Profile ===")
        print(f"Element: {profile.element}")
        print(f"Dosha Affinity: {profile.dosha_affinity}")
        print(f"Ruling Planet: {profile.ruling_planet}")

        print(f"\nHealth Strengths:")
        for strength in profile.health_strengths:
            print(f"  ✓ {strength}")

        print(f"\nHealth Vulnerabilities:")
        for vuln in profile.health_vulnerabilities:
            print(f"  ⚠ {vuln}")

        print(f"\nTop Wellness Recommendations:")
        for rec in profile.wellness_recommendations[:3]:
            print(f"  • {rec}")

    # Example 3: Personalized recommendations
    print("\n=== Personalized Recommendations ===\n")
    recommendations = service.get_personalized_recommendations(
        zodiac_sign=zodiac,
        current_health_issues=["stress", "sleep"],
        current_season="Summer"
    )

    print(f"For {recommendations['zodiac_sign']} ({recommendations['dosha_affinity']} dosha):")
    print(f"\nDietary recommendations:")
    for food in recommendations['dietary_recommendations'][:3]:
        print(f"  • {food}")

    print(f"\nSupplement recommendations:")
    for supp in recommendations['supplement_recommendations'][:3]:
        print(f"  • {supp}")

    print(f"\nSeasonal adjustments (Summer):")
    for adj in recommendations['seasonal_adjustments']:
        print(f"  • {adj}")

    # Example 4: Dosha compatibility check
    print("\n=== Zodiac-Dosha Compatibility ===\n")
    compatibility = service.get_zodiac_dosha_compatibility(zodiac, "Pitta")
    print(f"Zodiac: {compatibility['zodiac_sign']}")
    print(f"Predicted Dosha: {compatibility['zodiac_predicted_dosha']}")
    print(f"Measured Dosha: {compatibility['measured_dosha']}")
    print(f"Match: {compatibility['match']}")
    print(f"\nInterpretation:\n{compatibility['interpretation']}")
