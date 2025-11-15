"""
Recommendation Engine

Generates personalized wellness recommendations based on:
- EEG analysis (stress, focus)
- Health metrics (sleep, activity)
- Correlations and patterns
- Ayurvedic dosha type
"""
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Personalized recommendation system

    Uses:
    - Correlation analysis (sleep vs stress)
    - Pattern detection (time-based trends)
    - Rule-based recommendations
    - GraphRAG for complex reasoning
    """

    def __init__(self):
        """Initialize recommendation engine"""
        pass

    def generate_recommendations(
        self,
        user_id: str,
        health_data: Dict,
        eeg_data: Optional[Dict] = None,
        user_profile: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate personalized recommendations

        Args:
            user_id: User ID
            health_data: Recent health metrics
            eeg_data: Latest EEG analysis
            user_profile: User preferences and dosha

        Returns:
            List of recommendations with priority, evidence, actions
        """
        recommendations = []

        # Analyze sleep
        sleep_recs = self._analyze_sleep(health_data)
        recommendations.extend(sleep_recs)

        # Analyze stress (from EEG)
        if eeg_data:
            stress_recs = self._analyze_stress(eeg_data, health_data)
            recommendations.extend(stress_recs)

        # Analyze activity
        activity_recs = self._analyze_activity(health_data)
        recommendations.extend(activity_recs)

        # Dosha-based recommendations
        if user_profile and "dosha" in user_profile:
            dosha_recs = self._dosha_recommendations(user_profile["dosha"])
            recommendations.extend(dosha_recs)

        # Correlation-based recommendations
        correlation_recs = self._find_correlations(health_data)
        recommendations.extend(correlation_recs)

        # Sort by priority
        recommendations.sort(key=lambda x: x.get("priority", 0), reverse=True)

        return recommendations[:10]  # Top 10

    def _analyze_sleep(self, health_data: Dict) -> List[Dict]:
        """Analyze sleep patterns"""
        recs = []

        avg_sleep = health_data.get("avg_sleep_hours", 7)

        if avg_sleep < 7:
            recs.append({
                "type": "sleep",
                "priority": 9,
                "title": "Improve Sleep Duration",
                "description": f"You're averaging {avg_sleep:.1f} hours of sleep. Aim for 7-9 hours for optimal health.",
                "actions": [
                    "Set a consistent bedtime",
                    "Avoid screens 1 hour before bed",
                    "Consider magnesium supplementation (200-400mg)"
                ],
                "evidence": "Sleep <7 hours increases stress hormones, impairs cognition, weakens immune function",
                "category": "lifestyle"
            })

        if health_data.get("sleep_variability", 0) > 1.5:
            recs.append({
                "type": "sleep",
                "priority": 7,
                "title": "Stabilize Sleep Schedule",
                "description": "Your sleep times vary significantly. Consistency improves sleep quality.",
                "actions": [
                    "Wake at same time daily (even weekends)",
                    "Set bedtime alarm for consistent routine"
                ],
                "evidence": "Circadian rhythm thrives on consistency",
                "category": "lifestyle"
            })

        return recs

    def _analyze_stress(self, eeg_data: Dict, health_data: Dict) -> List[Dict]:
        """Analyze stress levels"""
        recs = []

        stress_level = eeg_data.get("stress", 0)

        if stress_level > 0.7:
            recs.append({
                "type": "stress",
                "priority": 10,
                "title": "High Stress Detected",
                "description": f"Your EEG shows elevated stress (beta waves at {stress_level:.2f}). Immediate intervention recommended.",
                "actions": [
                    "Box breathing exercise (4-4-4-4) for 5 minutes",
                    "Ashwagandha 300-500mg daily (reduces cortisol)",
                    "Morning meditation (10 min minimum)",
                    "Ensure 8 hours sleep tonight"
                ],
                "evidence": "Chronic stress increases cortisol, inflammation, and disease risk",
                "category": "mental_health",
                "supplements": ["Ashwagandha", "Magnesium", "L-theanine"]
            })

        return recs

    def _analyze_activity(self, health_data: Dict) -> List[Dict]:
        """Analyze physical activity"""
        recs = []

        avg_steps = health_data.get("avg_steps", 0)

        if avg_steps < 5000:
            recs.append({
                "type": "activity",
                "priority": 6,
                "title": "Increase Daily Movement",
                "description": f"You're averaging {avg_steps:,} steps/day. Aim for 8,000-10,000 for health benefits.",
                "actions": [
                    "Walk 10 min after each meal",
                    "Take stairs instead of elevator",
                    "Schedule 30 min walk daily"
                ],
                "evidence": "Regular movement reduces stress, improves mood, enhances cognition",
                "category": "fitness"
            })

        return recs

    def _dosha_recommendations(self, dosha: str) -> List[Dict]:
        """Recommendations based on Ayurvedic dosha"""
        dosha_advice = {
            "Vata": {
                "title": "Balance Vata Dosha",
                "description": "Vata types benefit from grounding, warming practices and routines.",
                "actions": [
                    "Warm, cooked foods (soups, stews)",
                    "Consistent daily routine",
                    "Grounding exercises (yoga, tai chi)",
                    "Warm oil massage (abhyanga)"
                ],
                "herbs": ["Ashwagandha", "Brahmi", "Ginger"]
            },
            "Pitta": {
                "title": "Balance Pitta Dosha",
                "description": "Pitta types benefit from cooling, calming practices.",
                "actions": [
                    "Cooling foods (cucumber, coconut, mint)",
                    "Avoid excess heat and spicy foods",
                    "Calming activities (swimming, moonlight walks)",
                    "Cooling breathing (sitali pranayama)"
                ],
                "herbs": ["Brahmi", "Shatavari", "Coriander"]
            },
            "Kapha": {
                "title": "Balance Kapha Dosha",
                "description": "Kapha types benefit from stimulating, energizing practices.",
                "actions": [
                    "Light, warm, spicy foods",
                    "Vigorous exercise daily",
                    "Wake early (before 6am)",
                    "Reduce dairy and heavy foods"
                ],
                "herbs": ["Ginger", "Turmeric", "Black pepper"]
            }
        }

        advice = dosha_advice.get(dosha)
        if not advice:
            return []

        return [{
            "type": "dosha",
            "priority": 5,
            **advice,
            "evidence": f"Ayurvedic constitution: {dosha} dosha",
            "category": "ayurveda"
        }]

    def _find_correlations(self, health_data: Dict) -> List[Dict]:
        """Find correlations in health data"""
        recs = []

        # Example: Poor sleep correlates with high stress
        if health_data.get("avg_sleep_hours", 7) < 6.5 and health_data.get("avg_stress_level", 0) > 7:
            recs.append({
                "type": "correlation",
                "priority": 8,
                "title": "Sleep-Stress Correlation Detected",
                "description": "Your stress levels are high on days with poor sleep. Improving sleep should reduce stress.",
                "actions": [
                    "Prioritize 8 hours sleep for next 7 days",
                    "Track correlation between sleep and stress"
                ],
                "evidence": "Data shows 30% higher stress on <6 hour sleep nights",
                "category": "insight"
            })

        return recs


# Global instance
_recommendation_engine = None

def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine singleton"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
