"""
Enhanced Recommendation Engine

Generates personalized wellness recommendations based on:
- User health metrics and trends
- EEG analysis data
- Dietary patterns
- Sleep and activity levels
- Dosha type (Ayurvedic constitution)
- GraphRAG knowledge
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.models.postgres_models import (
    HealthMetric,
    EEGAnalysis,
    Recommendation,
    User
)
from backend.services.graph_rag import get_graph_rag


class RecommendationEngine:
    """
    Personalized recommendation engine using ML and GraphRAG
    """

    def __init__(self):
        self.graph_rag = get_graph_rag()

    async def generate_recommendations(
        self,
        user_id: str,
        db: AsyncSession,
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations for a user

        Returns:
            List of recommendations with priority and evidence
        """
        # Gather user data
        user_state = await self._build_user_state(user_id, db)

        # Generate recommendations from multiple sources
        recommendations = []

        # 1. EEG-based recommendations
        eeg_recs = await self._eeg_based_recommendations(user_state, db)
        recommendations.extend(eeg_recs)

        # 2. Sleep-based recommendations
        sleep_recs = await self._sleep_based_recommendations(user_state, db)
        recommendations.extend(sleep_recs)

        # 3. Activity-based recommendations
        activity_recs = await self._activity_based_recommendations(user_state, db)
        recommendations.extend(activity_recs)

        # 4. GraphRAG complex reasoning recommendations
        graph_recs = self._graphrag_recommendations(user_state)
        recommendations.extend(graph_recs)

        # 5. Dosha-based recommendations (Ayurvedic)
        dosha_recs = self._dosha_based_recommendations(user_state)
        recommendations.extend(dosha_recs)

        # Deduplicate and rank
        final_recs = self._rank_and_deduplicate(recommendations)

        # Store in database
        await self._store_recommendations(user_id, final_recs[:max_recommendations], db)

        return final_recs[:max_recommendations]

    async def _build_user_state(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Build comprehensive user state from database
        """
        state = {
            "user_id": user_id,
            "recent_metrics": [],
            "eeg_history": [],
            "sleep_avg": None,
            "stress_trend": None,
            "activity_level": None,
            "dosha": None,
            "current_supplements": [],
            "health_goals": []
        }

        # Get user profile
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                state["dosha"] = user.dosha_type
                state["health_goals"] = user.health_goals or []
        except:
            pass

        # Get recent health metrics (30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        result = await db.execute(
            select(HealthMetric)
            .where(HealthMetric.user_id == user_id)
            .where(HealthMetric.date >= cutoff_date)
            .order_by(desc(HealthMetric.date))
        )
        metrics = result.scalars().all()

        if metrics:
            state["recent_metrics"] = [
                {
                    "date": m.date,
                    "steps": m.steps,
                    "sleep_hours": m.sleep_hours,
                    "stress_level": m.stress_level,
                    "heart_rate": m.heart_rate_avg
                }
                for m in metrics
            ]

            # Calculate averages and trends
            sleep_hours = [m.sleep_hours for m in metrics if m.sleep_hours]
            if sleep_hours:
                state["sleep_avg"] = np.mean(sleep_hours)

            steps = [m.steps for m in metrics if m.steps]
            if steps:
                state["activity_level"] = "active" if np.mean(steps) > 8000 else "moderate" if np.mean(steps) > 5000 else "low"

            stress_levels = [m.stress_level for m in metrics[-7:] if m.stress_level]
            if len(stress_levels) >= 3:
                # Check if stress is increasing
                state["stress_trend"] = "increasing" if stress_levels[-1] > stress_levels[0] else "stable"

        # Get recent EEG analyses
        result = await db.execute(
            select(EEGAnalysis)
            .where(EEGAnalysis.user_id == user_id)
            .order_by(desc(EEGAnalysis.timestamp))
            .limit(10)
        )
        eeg_analyses = result.scalars().all()

        if eeg_analyses:
            state["eeg_history"] = [
                {
                    "timestamp": e.timestamp,
                    "mental_state": e.mental_state,
                    "stress_level": e.stress_level,
                    "focus_level": e.focus_level
                }
                for e in eeg_analyses
            ]

        return state

    async def _eeg_based_recommendations(
        self,
        user_state: Dict,
        db: AsyncSession
    ) -> List[Dict]:
        """
        Generate recommendations based on EEG analysis
        """
        recommendations = []

        eeg_history = user_state.get("eeg_history", [])
        if not eeg_history:
            return recommendations

        latest_eeg = eeg_history[0]

        # High stress detection
        if latest_eeg.get("stress_level", 0) > 0.7:
            recommendations.append({
                "title": "Reduce Elevated Stress",
                "description": "Your recent brain activity shows high stress levels. Consider stress-reduction techniques.",
                "action": "Try a 10-minute breathing exercise or short meditation",
                "priority": "high",
                "category": "mental_health",
                "evidence": f"EEG stress level: {latest_eeg['stress_level']:.2f}",
                "related_supplements": ["Ashwagandha", "Magnesium", "L-Theanine"]
            })

        # Low focus detection
        if latest_eeg.get("focus_level", 0) < 0.4:
            recommendations.append({
                "title": "Enhance Focus and Concentration",
                "description": "Your brainwave patterns indicate suboptimal focus. Let's improve your concentration.",
                "action": "Ensure adequate sleep, try Pomodoro technique, consider cognitive supplements",
                "priority": "medium",
                "category": "cognitive",
                "evidence": f"EEG focus level: {latest_eeg['focus_level']:.2f}",
                "related_supplements": ["Brahmi", "L-Theanine", "Lion's Mane"]
            })

        return recommendations

    async def _sleep_based_recommendations(
        self,
        user_state: Dict,
        db: AsyncSession
    ) -> List[Dict]:
        """
        Generate recommendations based on sleep patterns
        """
        recommendations = []

        sleep_avg = user_state.get("sleep_avg")
        if sleep_avg is None:
            return recommendations

        # Insufficient sleep
        if sleep_avg < 6.5:
            recommendations.append({
                "title": "Improve Sleep Duration",
                "description": f"You're averaging {sleep_avg:.1f} hours of sleep. Aim for 7-9 hours for optimal health.",
                "action": "Set a consistent bedtime, create a relaxing evening routine, optimize sleep environment",
                "priority": "high",
                "category": "sleep",
                "evidence": f"7-day average: {sleep_avg:.1f} hours",
                "related_supplements": ["Magnesium Glycinate", "L-Theanine", "Ashwagandha"]
            })

        # Excessive sleep (might indicate other issues)
        elif sleep_avg > 9.5:
            recommendations.append({
                "title": "Investigate Sleep Quality",
                "description": f"You're averaging {sleep_avg:.1f} hours of sleep, which is above normal. Consider sleep quality factors.",
                "action": "Consult healthcare provider to rule out sleep disorders, check vitamin D and B12 levels",
                "priority": "medium",
                "category": "sleep",
                "evidence": f"7-day average: {sleep_avg:.1f} hours"
            })

        return recommendations

    async def _activity_based_recommendations(
        self,
        user_state: Dict,
        db: AsyncSession
    ) -> List[Dict]:
        """
        Generate recommendations based on activity levels
        """
        recommendations = []

        activity_level = user_state.get("activity_level")
        if not activity_level:
            return recommendations

        if activity_level == "low":
            recommendations.append({
                "title": "Increase Physical Activity",
                "description": "Your activity levels are below recommended guidelines. Regular movement improves mood, energy, and overall health.",
                "action": "Start with 15-minute daily walks, gradually increase to 30 minutes",
                "priority": "high",
                "category": "lifestyle",
                "evidence": "Average daily steps < 5000"
            })

        return recommendations

    def _graphrag_recommendations(
        self,
        user_state: Dict
    ) -> List[Dict]:
        """
        Generate recommendations using GraphRAG complex reasoning
        """
        recommendations = []

        # Build symptom list from user state
        symptoms = []
        if user_state.get("sleep_avg") and user_state["sleep_avg"] < 6.5:
            symptoms.append("Poor Sleep")
        if user_state.get("stress_trend") == "increasing":
            symptoms.append("High Stress")
        if user_state.get("activity_level") == "low":
            symptoms.append("Low Energy")

        eeg_history = user_state.get("eeg_history", [])
        if eeg_history and eeg_history[0].get("focus_level", 1) < 0.4:
            symptoms.append("Low Focus")

        if not symptoms:
            return recommendations

        # Use GraphRAG to find treatments
        graph_state = {
            "symptoms": symptoms,
            "current_supplements": user_state.get("current_supplements", []),
            "dosha": user_state.get("dosha"),
            "contraindications": []  # Would get from user profile
        }

        graph_results = self.graph_rag.complex_reasoning_query(graph_state)

        # Convert to recommendation format
        for supp in graph_results.get("new_supplements", []):
            recommendations.append({
                "title": f"Consider {supp['name']}",
                "description": f"Based on your symptoms, {supp['name']} may help. It addresses: {', '.join(supp.get('treated_symptoms', []))}",
                "action": f"Research {supp['name']} and consult healthcare provider before starting",
                "priority": "medium",
                "category": "supplements",
                "evidence": f"Efficacy score: {supp.get('efficacy', 0):.2f}, Coverage: {supp.get('coverage', 0)} symptoms",
                "related_supplements": [supp['name']]
            })

        for practice in graph_results.get("practices", []):
            recommendations.append({
                "title": practice['name'],
                "description": f"This practice can help with: {', '.join(practice.get('treated_symptoms', []))}",
                "action": f"Incorporate {practice['name']} into your daily routine",
                "priority": "medium",
                "category": "lifestyle",
                "evidence": f"Efficacy: {practice.get('efficacy', 0):.2f}"
            })

        return recommendations

    def _dosha_based_recommendations(
        self,
        user_state: Dict
    ) -> List[Dict]:
        """
        Generate recommendations based on Ayurvedic dosha type
        """
        recommendations = []

        dosha = user_state.get("dosha")
        if not dosha:
            return recommendations

        # Get dosha recommendations from GraphRAG
        dosha_recs = self.graph_rag.find_dosha_balancing_recommendations(dosha)

        if dosha_recs:
            # Food recommendations
            foods = dosha_recs.get("balancing_foods", [])[:3]
            if foods:
                recommendations.append({
                    "title": f"{dosha} Balancing Foods",
                    "description": f"Based on your {dosha} constitution, these foods can help maintain balance",
                    "action": f"Include: {', '.join(foods)}",
                    "priority": "low",
                    "category": "nutrition",
                    "evidence": "Ayurvedic constitutional analysis"
                })

            # Herb recommendations
            herbs = dosha_recs.get("recommended_herbs", [])[:2]
            if herbs:
                herb_names = [h["name"] for h in herbs]
                recommendations.append({
                    "title": f"{dosha} Balancing Herbs",
                    "description": f"Traditional Ayurvedic herbs for {dosha} constitution",
                    "action": f"Consider: {', '.join(herb_names)}",
                    "priority": "low",
                    "category": "supplements",
                    "evidence": "Ayurvedic herbal wisdom",
                    "related_supplements": herb_names
                })

        return recommendations

    def _rank_and_deduplicate(
        self,
        recommendations: List[Dict]
    ) -> List[Dict]:
        """
        Rank recommendations by priority and deduplicate
        """
        # Priority scores
        priority_scores = {"high": 3, "medium": 2, "low": 1}

        # Remove exact duplicates
        unique_recs = []
        seen_titles = set()

        for rec in recommendations:
            if rec["title"] not in seen_titles:
                unique_recs.append(rec)
                seen_titles.add(rec["title"])

        # Sort by priority
        sorted_recs = sorted(
            unique_recs,
            key=lambda x: priority_scores.get(x.get("priority", "low"), 1),
            reverse=True
        )

        return sorted_recs

    async def _store_recommendations(
        self,
        user_id: str,
        recommendations: List[Dict],
        db: AsyncSession
    ):
        """
        Store recommendations in database
        """
        try:
            for rec in recommendations:
                db_rec = Recommendation(
                    user_id=user_id,
                    title=rec["title"],
                    description=rec["description"],
                    action=rec["action"],
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "general"),
                    evidence=rec.get("evidence", ""),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(db_rec)

            await db.commit()
        except Exception as e:
            print(f"Error storing recommendations: {e}")
            await db.rollback()


# Global instance
_engine_instance = None

def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine singleton"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RecommendationEngine()
    return _engine_instance
