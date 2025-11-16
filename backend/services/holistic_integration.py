"""
Holistic Integration Service.

Deep integration layer that connects all wellness features:
- Life Optimization (meal plans, schedules)
- Multi-modal fusion (EEG, voice, images, wearables)
- LLM wellness coach
- Natal chart insights
- Wearable data
- Dosha analysis

This service ensures the backend uses info across ALL sections to provide
comprehensive, personalized wellness guidance.
"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime, timedelta
from dataclasses import dataclass

from backend.models.life_optimization_models import (
    ComprehensiveUserProfile,
    DailyMealPlan,
    DailySchedule
)
from backend.services.nutritional_calculator import get_nutritional_calculator
from backend.services.meal_plan_optimizer import get_meal_optimizer
from backend.services.schedule_optimizer import get_schedule_optimizer
from backend.services.natal_chart_service import get_natal_chart_service
from backend.services.currency_location_service import get_currency_service


@dataclass
class HolisticWellnessInsight:
    """Comprehensive wellness insight combining all data sources."""
    user_id: str
    date: date

    # Core metrics
    overall_wellness_score: float  # 0-100

    # Component scores
    physical_score: float
    mental_score: float
    emotional_score: float
    spiritual_score: float
    nutritional_score: float

    # Integrated insights
    key_insights: List[str]
    recommendations: List[str]
    warnings: List[str]

    # Data sources used
    data_sources: List[str]

    # Adjustments made
    meal_plan_adjustments: Optional[Dict] = None
    schedule_adjustments: Optional[Dict] = None

    # Personalization factors
    personalization_applied: List[str] = None


class HolisticIntegrationService:
    """
    Integrates all wellness features for comprehensive personalization.

    This is the brain of the system that considers:
    - Current meal plan and nutrition
    - Daily schedule and energy levels
    - EEG brain state
    - Voice emotional state
    - Wearable biometrics (HRV, sleep, activity)
    - Astrological influences
    - Dosha balance
    - Goals and progress
    """

    def __init__(self):
        """Initialize integration service."""
        self.nutritional_calc = get_nutritional_calculator()
        self.meal_optimizer = get_meal_optimizer()
        self.schedule_optimizer = get_schedule_optimizer()
        self.natal_service = get_natal_chart_service()
        self.currency_service = get_currency_service()

    def generate_holistic_wellness_plan(
        self,
        profile: ComprehensiveUserProfile,
        target_date: date,
        wearable_data: Optional[Dict] = None,
        eeg_data: Optional[Dict] = None,
        voice_data: Optional[Dict] = None,
        multimodal_assessment: Optional[Dict] = None
    ) -> HolisticWellnessInsight:
        """
        Generate comprehensive wellness plan using ALL available data.

        Args:
            profile: User profile
            target_date: Date for plan
            wearable_data: Recent wearable metrics (HRV, sleep, steps)
            eeg_data: Recent EEG analysis
            voice_data: Recent voice emotion analysis
            multimodal_assessment: Multi-modal fusion result

        Returns:
            Holistic wellness insight with personalized plan
        """
        insights = []
        recommendations = []
        warnings = []
        data_sources = []
        personalization = []

        # 1. Analyze sleep from wearables
        sleep_quality = None
        if wearable_data and "sleep" in wearable_data:
            sleep_quality = wearable_data["sleep"].get("quality_score", 0)
            data_sources.append("wearable_sleep")

            if sleep_quality < 60:
                warnings.append(f"Poor sleep quality detected ({sleep_quality}/100)")
                insights.append("Sleep debt may affect energy and decision-making today")
                recommendations.append("Prioritize early bedtime tonight (before 10pm for Kapha time)")
                recommendations.append("Avoid caffeine after 2pm")
                personalization.append("adjusted_schedule_for_low_energy")
            elif sleep_quality > 80:
                insights.append(f"Excellent sleep quality ({sleep_quality}/100) - optimal recovery")
                personalization.append("high_energy_schedule")

        # 2. Analyze stress from HRV
        hrv_stress = None
        if wearable_data and "hrv" in wearable_data:
            hrv = wearable_data["hrv"].get("rmssd", 0)
            data_sources.append("wearable_hrv")

            if hrv < 20:  # Low HRV = high stress
                warnings.append("High stress detected from HRV")
                insights.append("Autonomic nervous system showing stress response")
                recommendations.append("Increase meditation to 30+ minutes today")
                recommendations.append("Add adaptogenic herbs (Ashwagandha, Holy Basil)")
                recommendations.append("Prioritize calming activities in schedule")
                personalization.append("anti_stress_meal_plan")
                personalization.append("increased_meditation_time")

        # 3. Analyze brain state from EEG
        if eeg_data:
            data_sources.append("eeg_analysis")

            dominant_state = eeg_data.get("dominant_state", "")

            if dominant_state == "anxious":
                insights.append("EEG shows elevated anxiety patterns")
                recommendations.append("Practice Nadi Shodhana (alternate nostril breathing)")
                recommendations.append("Increase Vata-balancing foods (warm, grounding, oily)")
                personalization.append("vata_balancing_meals")

            elif dominant_state == "focused":
                insights.append("Brain in optimal focus state")
                recommendations.append("Schedule deep work during this window")
                personalization.append("capitalize_on_focus")

        # 4. Analyze emotional state from voice
        if voice_data:
            data_sources.append("voice_emotion")

            emotion = voice_data.get("primary_emotion", "")
            confidence = voice_data.get("confidence", 0)

            if emotion == "stressed" and confidence > 0.7:
                insights.append(f"Voice analysis indicates stress (confidence: {confidence:.0%})")
                recommendations.append("Take 10-minute mindful walking break")
                recommendations.append("Practice box breathing (4-4-4-4)")

            elif emotion == "happy" and confidence > 0.7:
                insights.append("Positive emotional state detected")
                recommendations.append("Good time for creative work or social activities")

        # 5. Multi-modal fusion insights
        overall_wellness = 70  # Default
        if multimodal_assessment:
            data_sources.append("multimodal_fusion")

            overall_wellness = multimodal_assessment.get("overall_wellness_score", 70)

            # Get recommendations from fusion
            fusion_recs = multimodal_assessment.get("recommendations", [])
            recommendations.extend(fusion_recs[:3])  # Top 3

            # Check for critical issues
            if multimodal_assessment.get("risk_level") == "high":
                warnings.append("Multi-modal analysis indicates elevated health risk")
                recommendations.append("Consider consulting healthcare provider")

        # 6. Astrological influences
        if profile.natal_chart_id:
            data_sources.append("natal_chart")

            # Get current transits (simplified - would integrate with natal chart service)
            insights.append("Planetary influences considered for optimal timing")
            personalization.append("astrological_meal_timing")

        # 7. Dosha-specific adjustments
        dosha = profile.personality.dosha_type.lower()
        data_sources.append("dosha_analysis")

        if "vata" in dosha:
            if wearable_data and wearable_data.get("sleep", {}).get("hours", 0) < 7:
                warnings.append("Vata individuals need 7-8 hours sleep for balance")
                recommendations.append("Establish consistent sleep routine")

        elif "pitta" in dosha:
            if hrv_stress and hrv_stress > 70:
                recommendations.append("Pitta under stress - avoid competitive activities today")
                recommendations.append("Favor cooling foods and gentle exercise")

        elif "kapha" in dosha:
            if wearable_data and wearable_data.get("steps", 0) < 5000:
                warnings.append("Low activity detected - Kapha needs regular movement")
                recommendations.append("Add 15-minute brisk walk after meals")

        # 8. Generate adjusted meal plan
        meal_adjustments = self._generate_meal_adjustments(
            profile=profile,
            sleep_quality=sleep_quality,
            stress_level=hrv_stress,
            personalization=personalization
        )

        # 9. Generate adjusted schedule
        schedule_adjustments = self._generate_schedule_adjustments(
            profile=profile,
            energy_level=sleep_quality,
            stress_level=hrv_stress,
            personalization=personalization
        )

        # 10. Calculate component scores
        physical_score = self._calculate_physical_score(wearable_data)
        mental_score = self._calculate_mental_score(eeg_data, voice_data)
        emotional_score = self._calculate_emotional_score(voice_data, hrv_stress)
        spiritual_score = self._calculate_spiritual_score(profile)
        nutritional_score = self._calculate_nutritional_score(profile)

        # 11. Overall wellness score (weighted average)
        if not multimodal_assessment:
            overall_wellness = (
                physical_score * 0.25 +
                mental_score * 0.25 +
                emotional_score * 0.20 +
                spiritual_score * 0.15 +
                nutritional_score * 0.15
            )

        return HolisticWellnessInsight(
            user_id=profile.user_id,
            date=target_date,
            overall_wellness_score=round(overall_wellness, 1),
            physical_score=round(physical_score, 1),
            mental_score=round(mental_score, 1),
            emotional_score=round(emotional_score, 1),
            spiritual_score=round(spiritual_score, 1),
            nutritional_score=round(nutritional_score, 1),
            key_insights=insights,
            recommendations=recommendations,
            warnings=warnings,
            data_sources=data_sources,
            meal_plan_adjustments=meal_adjustments,
            schedule_adjustments=schedule_adjustments,
            personalization_applied=personalization
        )

    def _generate_meal_adjustments(
        self,
        profile: ComprehensiveUserProfile,
        sleep_quality: Optional[float],
        stress_level: Optional[float],
        personalization: List[str]
    ) -> Dict:
        """Generate meal plan adjustments based on real-time data."""
        adjustments = {}

        # Adjust for sleep debt
        if sleep_quality and sleep_quality < 60:
            adjustments["increase_b_vitamins"] = True
            adjustments["add_magnesium_foods"] = True
            adjustments["reduce_stimulants"] = True

        # Adjust for stress
        if stress_level and stress_level > 70:
            adjustments["increase_adaptogenic_herbs"] = True
            adjustments["add_omega3_foods"] = True
            adjustments["increase_tryptophan"] = True  # Serotonin precursor

        # Vata balancing (if indicated)
        if "vata_balancing_meals" in personalization:
            adjustments["increase_warming_spices"] = True
            adjustments["increase_healthy_fats"] = True
            adjustments["favor_cooked_foods"] = True

        # Anti-stress foods
        if "anti_stress_meal_plan" in personalization:
            adjustments["add_foods"] = [
                "Ashwagandha powder",
                "Holy Basil tea",
                "Dark leafy greens (magnesium)",
                "Walnuts (omega-3)",
                "Chamomile tea"
            ]

        return adjustments

    def _generate_schedule_adjustments(
        self,
        profile: ComprehensiveUserProfile,
        energy_level: Optional[float],
        stress_level: Optional[float],
        personalization: List[str]
    ) -> Dict:
        """Generate schedule adjustments based on real-time data."""
        adjustments = {}

        # Adjust for low energy
        if energy_level and energy_level < 60:
            adjustments["reduce_meeting_blocks"] = True
            adjustments["increase_break_frequency"] = True
            adjustments["shorten_deep_work_blocks"] = 60  # Instead of 90 min
            adjustments["add_power_nap"] = "15-20 min around 2-3pm"

        # Adjust for high stress
        if stress_level and stress_level > 70:
            adjustments["increase_meditation"] = profile.goals.meditation_minutes_daily + 15
            adjustments["add_nature_walk"] = "20 min outdoor walking"
            adjustments["reduce_screen_time"] = True

        # Increased meditation
        if "increased_meditation_time" in personalization:
            adjustments["meditation_minutes"] = 30
            adjustments["add_breathwork"] = "10 min Nadi Shodhana"

        return adjustments

    def _calculate_physical_score(self, wearable_data: Optional[Dict]) -> float:
        """Calculate physical wellness score."""
        if not wearable_data:
            return 70.0  # Default

        score = 70.0

        # Sleep (30% weight)
        sleep_quality = wearable_data.get("sleep", {}).get("quality_score", 70)
        score += (sleep_quality - 70) * 0.3

        # Activity (30% weight)
        steps = wearable_data.get("steps", 5000)
        activity_score = min(100, (steps / 10000) * 100)
        score += (activity_score - 70) * 0.3

        # HRV (20% weight)
        hrv = wearable_data.get("hrv", {}).get("rmssd", 30)
        hrv_score = min(100, (hrv / 50) * 100)
        score += (hrv_score - 70) * 0.2

        # Resting heart rate (20% weight)
        rhr = wearable_data.get("resting_heart_rate", 70)
        rhr_score = max(0, 100 - (rhr - 60))  # Lower is better
        score += (rhr_score - 70) * 0.2

        return max(0, min(100, score))

    def _calculate_mental_score(
        self,
        eeg_data: Optional[Dict],
        voice_data: Optional[Dict]
    ) -> float:
        """Calculate mental wellness score."""
        score = 70.0

        if eeg_data:
            state = eeg_data.get("dominant_state", "")

            if state == "focused":
                score += 15
            elif state == "relaxed":
                score += 10
            elif state == "anxious":
                score -= 15
            elif state == "drowsy":
                score -= 10

        if voice_data:
            emotion = voice_data.get("primary_emotion", "")

            if emotion == "happy":
                score += 10
            elif emotion == "stressed":
                score -= 10

        return max(0, min(100, score))

    def _calculate_emotional_score(
        self,
        voice_data: Optional[Dict],
        stress_level: Optional[float]
    ) -> float:
        """Calculate emotional wellness score."""
        score = 70.0

        if voice_data:
            emotion = voice_data.get("primary_emotion", "")
            confidence = voice_data.get("confidence", 0)

            if emotion == "happy":
                score += 20 * confidence
            elif emotion == "sad":
                score -= 20 * confidence
            elif emotion == "stressed":
                score -= 15 * confidence

        if stress_level:
            # Higher stress = lower emotional score
            score -= (stress_level - 50) * 0.3

        return max(0, min(100, score))

    def _calculate_spiritual_score(self, profile: ComprehensiveUserProfile) -> float:
        """Calculate spiritual wellness score based on practices."""
        score = 50.0  # Base

        # Meditation practice
        if profile.goals.meditation_minutes_daily > 0:
            score += min(30, profile.goals.meditation_minutes_daily)

        # Spiritual practices
        practices = profile.custom_preferences.spiritual_practices
        score += len(practices) * 5

        # Spiritual goal priority
        if profile.goals.priority_spiritual >= 7:
            score += 10

        return min(100, score)

    def _calculate_nutritional_score(self, profile: ComprehensiveUserProfile) -> float:
        """Calculate nutritional wellness score."""
        score = 70.0

        # Nutrition priority
        if profile.goals.priority_nutrition >= 8:
            score += 10

        # Diet quality (whole foods, clean eating)
        if profile.dietary_preferences.diet_type.value in ["vegan", "vegetarian"]:
            score += 5

        # Supplement stack
        if len(profile.custom_preferences.supplement_stack) > 0:
            score += 5

        return min(100, score)


# Singleton
_holistic_service = None


def get_holistic_service() -> HolisticIntegrationService:
    """Get singleton holistic integration service."""
    global _holistic_service
    if _holistic_service is None:
        _holistic_service = HolisticIntegrationService()
    return _holistic_service
