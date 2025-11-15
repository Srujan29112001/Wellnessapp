"""
Recommendation Engine

Generates personalized wellness recommendations based on:
- User profile and dosha type
- Health metrics and patterns
- EEG/voice analysis results
- Goals and preferences
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.postgres_models import (
    User, HealthMetric, EEGAnalysis, Recommendation,
    Priority, Dosha
)
from backend.database.postgres import AsyncSessionLocal
import json

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Personalized recommendation engine
    """

    def __init__(self):
        # Load knowledge bases
        self.ayurveda_db = self._load_ayurveda()
        self.supplement_db = self._load_supplements()

    def _load_ayurveda(self) -> Dict[str, Any]:
        """Load Ayurvedic knowledge base"""
        try:
            with open("knowledge_base/ayurveda/doshas.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading Ayurveda DB: {e}")
            return {}

    def _load_supplements(self) -> Dict[str, Any]:
        """Load supplement database"""
        try:
            with open("knowledge_base/supplements/supplements_db.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading supplements DB: {e}")
            return {}

    async def analyze_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze user's health patterns

        Returns correlations and trends
        """
        async with AsyncSessionLocal() as session:
            # Get health metrics for analysis period
            since_date = datetime.now().date() - timedelta(days=days)

            result = await session.execute(
                select(HealthMetric)
                .where(and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.date >= since_date
                ))
                .order_by(HealthMetric.date)
            )
            metrics = result.scalars().all()

            if len(metrics) < 7:  # Need at least a week of data
                return {
                    "patterns": [],
                    "correlations": {},
                    "trends": {},
                    "message": "Insufficient data for pattern analysis"
                }

            # Extract time series
            dates = [m.date for m in metrics]
            sleep = np.array([m.sleep_hours or 0 for m in metrics])
            stress = np.array([m.stress_level or 0 for m in metrics])
            steps = np.array([m.steps or 0 for m in metrics])
            mood = np.array([m.mood_score or 0 for m in metrics])

            patterns = []
            correlations = {}

            # Sleep vs Stress correlation
            if len(sleep) > 0 and len(stress) > 0:
                # Filter out zeros
                valid_idx = (sleep > 0) & (stress > 0)
                if np.sum(valid_idx) > 3:
                    corr = np.corrcoef(sleep[valid_idx], stress[valid_idx])[0, 1]
                    correlations["sleep_stress"] = float(corr)

                    if corr < -0.5:  # Strong negative correlation
                        patterns.append({
                            "pattern": "Poor sleep increases stress",
                            "correlation": corr,
                            "strength": "strong"
                        })

            # Activity vs Mood correlation
            if len(steps) > 0 and len(mood) > 0:
                valid_idx = (steps > 0) & (mood > 0)
                if np.sum(valid_idx) > 3:
                    corr = np.corrcoef(steps[valid_idx], mood[valid_idx])[0, 1]
                    correlations["activity_mood"] = float(corr)

                    if corr > 0.5:  # Strong positive correlation
                        patterns.append({
                            "pattern": "More activity improves mood",
                            "correlation": corr,
                            "strength": "strong"
                        })

            # Trends
            trends = {}

            # Sleep trend
            if len(sleep) > 0 and np.mean(sleep) > 0:
                recent_sleep = np.mean(sleep[-7:]) if len(sleep) >= 7 else np.mean(sleep)
                overall_sleep = np.mean(sleep)
                trends["sleep"] = {
                    "recent_avg": float(recent_sleep),
                    "overall_avg": float(overall_sleep),
                    "trend": "improving" if recent_sleep > overall_sleep else "declining"
                }

            # Stress trend
            if len(stress) > 0 and np.mean(stress) > 0:
                recent_stress = np.mean(stress[-7:]) if len(stress) >= 7 else np.mean(stress)
                overall_stress = np.mean(stress)
                trends["stress"] = {
                    "recent_avg": float(recent_stress),
                    "overall_avg": float(overall_stress),
                    "trend": "improving" if recent_stress < overall_stress else "worsening"
                }

            return {
                "patterns": patterns,
                "correlations": correlations,
                "trends": trends,
                "data_points": len(metrics)
            }

    async def generate_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations

        Args:
            user_id: User ID
            limit: Maximum number of recommendations

        Returns:
            List of recommendation dicts
        """
        recommendations = []

        async with AsyncSessionLocal() as session:
            # Get user profile
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return []

            # Analyze patterns
            patterns = await self.analyze_patterns(user_id)

            # Get recent health data
            week_ago = datetime.now().date() - timedelta(days=7)
            result = await session.execute(
                select(HealthMetric)
                .where(and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.date >= week_ago
                ))
            )
            recent_metrics = result.scalars().all()

            # Get latest EEG
            result = await session.execute(
                select(EEGAnalysis)
                .where(EEGAnalysis.user_id == user_id)
                .order_by(EEGAnalysis.timestamp.desc())
                .limit(1)
            )
            latest_eeg = result.scalar_one_or_none()

            # Calculate averages
            avg_sleep = np.mean([m.sleep_hours or 0 for m in recent_metrics]) if recent_metrics else 0
            avg_stress = np.mean([m.stress_level or 0 for m in recent_metrics]) if recent_metrics else 0
            avg_steps = np.mean([m.steps or 0 for m in recent_metrics]) if recent_metrics else 0

            # 1. Sleep recommendations
            if avg_sleep < 7 and avg_sleep > 0:
                recommendations.append({
                    "category": "sleep",
                    "title": "Improve Sleep Duration",
                    "description": f"Your average sleep is {avg_sleep:.1f} hours. Aim for 7-9 hours for optimal health.",
                    "reasoning": f"Data shows you're averaging {avg_sleep:.1f}h/night, below recommended 7-9 hours.",
                    "priority": Priority.HIGH.value,
                    "evidence": [
                        "Sleep deprivation impairs cognitive function and immune health",
                        "Consistent 7-9 hours sleep improves mood and reduces stress"
                    ],
                    "sources": ["Sleep Foundation Guidelines", "NIH Sleep Research"]
                })

            # 2. Stress management
            if avg_stress > 0.6 or (latest_eeg and latest_eeg.stress_level > 0.7):
                stress_val = latest_eeg.stress_level if latest_eeg else avg_stress

                recommendations.append({
                    "category": "stress",
                    "title": "Reduce Stress Levels",
                    "description": f"Your stress level is elevated ({stress_val:.0%}). Practice daily stress reduction techniques.",
                    "reasoning": f"EEG/health data indicates stress at {stress_val:.0%}, above healthy threshold.",
                    "priority": Priority.HIGH.value,
                    "evidence": [
                        "Chronic stress increases cortisol, affecting sleep and immunity",
                        "Mindfulness and breathing exercises reduce stress by 30-40%"
                    ],
                    "sources": ["APA Stress Research", "Mindfulness Studies"]
                })

                # Supplement for stress
                ashwagandha = self._find_supplement("Ashwagandha")
                if ashwagandha:
                    recommendations.append({
                        "category": "supplement",
                        "title": "Consider Ashwagandha for Stress",
                        "description": "Ashwagandha is an adaptogen that may help reduce cortisol and anxiety.",
                        "reasoning": "Your elevated stress levels may benefit from this traditional Ayurvedic herb.",
                        "priority": Priority.MEDIUM.value,
                        "evidence": ashwagandha.get("evidence", []),
                        "sources": ["Ayurvedic Medicine", "Clinical trials on adaptogens"]
                    })

            # 3. Activity recommendations
            if avg_steps < 5000 and avg_steps > 0:
                recommendations.append({
                    "category": "exercise",
                    "title": "Increase Daily Activity",
                    "description": f"You're averaging {avg_steps:.0f} steps/day. Aim for at least 7,000-10,000 steps.",
                    "reasoning": "Low activity levels correlate with mood and energy issues.",
                    "priority": Priority.MEDIUM.value,
                    "evidence": [
                        "10,000 steps/day improves cardiovascular health",
                        "Regular activity boosts mood and cognitive function"
                    ],
                    "sources": ["WHO Physical Activity Guidelines"]
                })

            # 4. Dosha-based recommendations
            if user.dosha_type and user.dosha_type.value in self.ayurveda_db:
                dosha_info = self.ayurveda_db[user.dosha_type.value]

                # Food recommendations
                balancing_foods = dosha_info.get("balancing_foods", [])
                if balancing_foods:
                    foods_str = ", ".join(balancing_foods[:5])
                    recommendations.append({
                        "category": "diet",
                        "title": f"Foods to Balance {user.dosha_type.value.capitalize()} Dosha",
                        "description": f"Include these foods in your diet: {foods_str}",
                        "reasoning": f"Based on your {user.dosha_type.value} constitution, these foods promote balance.",
                        "priority": Priority.LOW.value,
                        "evidence": ["Ayurvedic dietary principles"],
                        "sources": ["Traditional Ayurvedic texts"]
                    })

            # 5. Focus/Cognitive recommendations
            if latest_eeg and latest_eeg.focus_level < 0.5:
                recommendations.append({
                    "category": "lifestyle",
                    "title": "Improve Mental Focus",
                    "description": "Your EEG shows low focus levels. Try meditation, L-theanine, or cognitive breaks.",
                    "reasoning": f"Latest EEG analysis shows focus at {latest_eeg.focus_level:.0%}.",
                    "priority": Priority.MEDIUM.value,
                    "evidence": [
                        "L-theanine improves attention and reduces mind-wandering",
                        "Short meditation breaks enhance cognitive performance"
                    ],
                    "sources": ["Cognitive neuroscience research"]
                })

            # Limit and prioritize
            # Sort by priority
            priority_order = {Priority.HIGH.value: 0, Priority.MEDIUM.value: 1, Priority.LOW.value: 2}
            recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

            return recommendations[:limit]

    def _find_supplement(self, name: str) -> Optional[Dict[str, Any]]:
        """Find supplement in knowledge base"""
        supplements = self.supplement_db.get("supplements", [])
        for supp in supplements:
            if supp.get("name", "").lower() == name.lower():
                return supp
        return None

    async def save_recommendations(
        self,
        user_id: str,
        recommendations: List[Dict[str, Any]]
    ):
        """Save recommendations to database"""
        async with AsyncSessionLocal() as session:
            for rec in recommendations:
                db_rec = Recommendation(
                    user_id=user_id,
                    category=rec["category"],
                    title=rec["title"],
                    description=rec["description"],
                    reasoning=rec.get("reasoning"),
                    evidence=rec.get("evidence", []),
                    sources=rec.get("sources", []),
                    priority=Priority(rec.get("priority", "medium"))
                )
                session.add(db_rec)

            await session.commit()
            logger.info(f"Saved {len(recommendations)} recommendations for user {user_id}")


# Global engine instance
_engine = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine"""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine
