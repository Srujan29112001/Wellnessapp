"""
Recommendation Engine

Generates personalized wellness recommendations based on:
- EEG analysis results (stress, focus, mental state)
- Health metrics (sleep, activity, vitals)
- Dietary patterns and nutritional data
- Ayurvedic dosha type
- User goals and preferences
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from backend.models.postgres_models import (
    User, HealthMetric, EEGAnalysis, Recommendation, Priority
)


class RecommendationEngine:
    """
    AI-powered recommendation engine for holistic wellness
    """

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict:
        """Load supplement and Ayurvedic knowledge bases"""
        kb = {'supplements': {}, 'ayurveda': {}}

        # Load supplements
        supp_path = 'knowledge_base/supplements/supplements_db.json'
        if os.path.exists(supp_path):
            with open(supp_path, 'r') as f:
                data = json.load(f)
                for supp in data.get('supplements', []):
                    kb['supplements'][supp['name'].lower()] = supp

        # Load Ayurveda
        ayur_path = 'knowledge_base/ayurveda/doshas.json'
        if os.path.exists(ayur_path):
            with open(ayur_path, 'r') as f:
                kb['ayurveda'] = json.load(f)

        return kb

    async def generate_recommendations(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[Dict]:
        """
        Generate comprehensive personalized recommendations

        Analyzes:
        - Recent EEG data for mental state patterns
        - Sleep quality and duration trends
        - Stress levels over time
        - Activity levels
        - User's dosha type (if known)
        """
        recommendations = []

        # Get user profile
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            return []

        # Get recent EEG analyses (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        eeg_result = await db.execute(
            select(EEGAnalysis)
            .where(
                and_(
                    EEGAnalysis.user_id == user_id,
                    EEGAnalysis.timestamp >= week_ago
                )
            )
            .order_by(EEGAnalysis.timestamp.desc())
        )
        eeg_analyses = eeg_result.scalars().all()

        # Get recent health metrics
        health_result = await db.execute(
            select(HealthMetric)
            .where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.date >= week_ago.date()
                )
            )
            .order_by(HealthMetric.date.desc())
        )
        health_metrics = health_result.scalars().all()

        # Analyze patterns and generate recommendations
        recommendations.extend(self._analyze_stress_patterns(eeg_analyses, user))
        recommendations.extend(self._analyze_sleep_patterns(health_metrics))
        recommendations.extend(self._analyze_focus_patterns(eeg_analyses))
        recommendations.extend(self._analyze_dosha_balance(user))
        recommendations.extend(self._analyze_activity_levels(health_metrics))

        # Sort by priority
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)

        return recommendations[:10]  # Top 10 recommendations

    def _analyze_stress_patterns(
        self,
        eeg_analyses: List,
        user: Optional[object] = None
    ) -> List[Dict]:
        """Analyze stress levels and recommend interventions"""
        recommendations = []

        if not eeg_analyses:
            return recommendations

        # Calculate average stress
        avg_stress = np.mean([e.stress_level for e in eeg_analyses])

        # High stress detected
        if avg_stress > 0.6:
            # Ashwagandha recommendation
            ashwagandha = self.knowledge_base['supplements'].get('ashwagandha', {})
            if ashwagandha:
                recommendations.append({
                    'category': 'supplement',
                    'title': 'Consider Ashwagandha for Stress Reduction',
                    'description': f'Your average stress level is {avg_stress:.0%}, which is elevated. Ashwagandha is an adaptogenic herb shown to reduce cortisol levels by up to 30%.',
                    'reasoning': f'Analysis of {len(eeg_analyses)} EEG sessions shows consistently high stress. Ashwagandha helps balance the HPA axis and supports stress resilience.',
                    'evidence': ashwagandha.get('scientific_evidence', []),
                    'priority': Priority.HIGH,
                    'priority_score': 9,
                    'actionable_steps': [
                        'Start with 300-500mg standardized extract daily',
                        'Take with food, preferably in the evening',
                        'Allow 2-4 weeks to notice effects',
                        'Consult healthcare provider if on medications'
                    ]
                })

            # Breathing exercises
            recommendations.append({
                'category': 'lifestyle',
                'title': 'Daily Breathing Exercise Practice',
                'description': 'Implement box breathing (4-4-4-4) for 10 minutes daily to activate parasympathetic nervous system.',
                'reasoning': 'High beta wave activity detected, indicating sympathetic nervous system overdrive. Breathwork can help restore balance.',
                'evidence': ['Research shows breathwork reduces cortisol and increases HRV'],
                'priority': Priority.HIGH,
                'priority_score': 10,
                'actionable_steps': [
                    'Practice box breathing: 4 counts in, hold 4, out 4, hold 4',
                    'Do this 3x daily: morning, lunch, evening',
                    'Use our guided breathing session feature'
                ]
            })

            # Magnesium recommendation
            recommendations.append({
                'category': 'supplement',
                'title': 'Magnesium for Nervous System Support',
                'description': 'Magnesium helps calm the nervous system and supports stress response.',
                'reasoning': 'Chronic stress depletes magnesium. Supplementation can improve stress resilience and sleep quality.',
                'evidence': ['Magnesium deficiency linked to increased stress response', 'Supplementation improves sleep and reduces anxiety'],
                'priority': Priority.MEDIUM,
                'priority_score': 7,
                'actionable_steps': [
                    'Take 300-400mg magnesium glycinate before bed',
                    'Increase magnesium-rich foods: nuts, seeds, leafy greens',
                    'Monitor for digestive tolerance'
                ]
            })

        return recommendations

    def _analyze_sleep_patterns(self, health_metrics: List) -> List[Dict]:
        """Analyze sleep quality and duration"""
        recommendations = []

        sleep_data = [m.sleep_hours for m in health_metrics if m.sleep_hours]
        if not sleep_data:
            return recommendations

        avg_sleep = np.mean(sleep_data)

        # Insufficient sleep
        if avg_sleep < 7:
            recommendations.append({
                'category': 'sleep',
                'title': 'Improve Sleep Duration',
                'description': f'Your average sleep is {avg_sleep:.1f} hours. Aim for 7-9 hours for optimal wellness.',
                'reasoning': 'Sleep debt accumulates and impairs cognitive function, mood, and metabolic health.',
                'evidence': ['CDC recommends 7+ hours for adults', 'Sleep deprivation increases cortisol and inflammation'],
                'priority': Priority.HIGH,
                'priority_score': 8,
                'actionable_steps': [
                    'Set consistent sleep/wake times (even weekends)',
                    'Create 30-min wind-down routine before bed',
                    'Keep bedroom cool (65-68°F), dark, and quiet',
                    'Avoid screens 1 hour before bed',
                    'Consider magnesium or L-theanine before bed'
                ]
            })

        return recommendations

    def _analyze_focus_patterns(self, eeg_analyses: List) -> List[Dict]:
        """Analyze focus levels and recommend nootropics/practices"""
        recommendations = []

        if not eeg_analyses:
            return recommendations

        avg_focus = np.mean([e.focus_level for e in eeg_analyses])

        # Low focus
        if avg_focus < 0.4:
            l_theanine = self.knowledge_base['supplements'].get('l-theanine', {})
            if l_theanine:
                recommendations.append({
                    'category': 'supplement',
                    'title': 'L-Theanine for Calm Focus',
                    'description': f'Focus levels averaging {avg_focus:.0%}. L-Theanine promotes alert relaxation without jitters.',
                    'reasoning': 'L-Theanine increases alpha wave activity associated with relaxed focus, while maintaining alertness.',
                    'evidence': l_theanine.get('scientific_evidence', []),
                    'priority': Priority.MEDIUM,
                    'priority_score': 6,
                    'actionable_steps': [
                        'Take 100-200mg L-Theanine when focus needed',
                        'Can combine with moderate caffeine (1:2 ratio)',
                        'Green tea provides natural L-theanine + caffeine'
                    ]
                })

            # Omega-3
            recommendations.append({
                'category': 'supplement',
                'title': 'Omega-3 for Cognitive Function',
                'description': 'EPA/DHA support brain health, focus, and mood regulation.',
                'reasoning': 'Essential fatty acids are crucial for neurotransmitter function and neuronal membrane health.',
                'evidence': ['Omega-3s improve attention in adults', 'Low omega-3 linked to cognitive decline'],
                'priority': Priority.MEDIUM,
                'priority_score': 5,
                'actionable_steps': [
                    'Take 1000-2000mg combined EPA/DHA daily',
                    'Choose quality fish oil or algae-based (vegan)',
                    'Take with meals for better absorption'
                ]
            })

        return recommendations

    def _analyze_dosha_balance(self, user: Optional[object]) -> List[Dict]:
        """Generate Ayurvedic recommendations based on dosha"""
        recommendations = []

        if not user or not user.dosha_type:
            return recommendations

        dosha_name = user.dosha_type.value
        dosha_info = self.knowledge_base['ayurveda'].get('doshas', {}).get(dosha_name, {})

        if dosha_info:
            # Balancing foods
            balancing_foods = dosha_info.get('balancing_foods', [])
            if balancing_foods:
                recommendations.append({
                    'category': 'diet',
                    'title': f'Balancing Foods for {dosha_name.title()} Dosha',
                    'description': f'Favor these foods to balance your {dosha_name} constitution: {", ".join(balancing_foods[:5])}',
                    'reasoning': f'Your {dosha_name} dosha may be imbalanced based on your stress and energy patterns.',
                    'evidence': ['Ayurvedic principle: like increases like, opposites balance'],
                    'priority': Priority.LOW,
                    'priority_score': 4,
                    'actionable_steps': [
                        f'Include {balancing_foods[0]} in your daily diet',
                        f'Add {balancing_foods[1]} to meals regularly',
                        'Avoid excessive cold/raw foods (for Vata/Kapha)'
                    ]
                })

            # Herbs
            herbs = dosha_info.get('herbs', [])
            if herbs:
                top_herb = herbs[0]
                recommendations.append({
                    'category': 'supplement',
                    'title': f'Try {top_herb["name"]} for {dosha_name.title()} Balance',
                    'description': f'{top_herb["name"]}: {", ".join(top_herb.get("properties", [])[:2])}',
                    'reasoning': f'Traditional Ayurvedic herb for balancing {dosha_name} dosha.',
                    'evidence': ['Ayurvedic traditional use for centuries'],
                    'priority': Priority.LOW,
                    'priority_score': 3,
                    'actionable_steps': [
                        'Consult an Ayurvedic practitioner for proper dosing',
                        'Start with small amounts to test tolerance'
                    ]
                })

        return recommendations

    def _analyze_activity_levels(self, health_metrics: List) -> List[Dict]:
        """Analyze physical activity patterns"""
        recommendations = []

        steps_data = [m.steps for m in health_metrics if m.steps]
        if not steps_data:
            return recommendations

        avg_steps = np.mean(steps_data)

        # Low activity
        if avg_steps < 5000:
            recommendations.append({
                'category': 'exercise',
                'title': 'Increase Daily Movement',
                'description': f'Your average daily steps ({avg_steps:.0f}) are below the recommended 7,000-10,000 for optimal health.',
                'reasoning': 'Regular movement improves mood, reduces stress, enhances cognitive function, and supports metabolic health.',
                'evidence': ['10,000 steps/day reduces all-cause mortality', 'Exercise increases BDNF (brain-derived neurotrophic factor)'],
                'priority': Priority.MEDIUM,
                'priority_score': 7,
                'actionable_steps': [
                    'Take a 10-minute walk after each meal',
                    'Use stairs instead of elevators',
                    'Set hourly movement reminders',
                    'Aim for 7,000+ steps as initial goal'
                ]
            })

        return recommendations


# Global instance
_recommendation_engine = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine instance"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
