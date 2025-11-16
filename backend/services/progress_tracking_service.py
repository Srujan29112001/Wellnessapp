"""
Progress Monitoring & Adherence Tracking Service

Tracks:
- Daily check-ins (did user follow the plan?)
- Adherence percentages across all wellness dimensions
- Progress toward goals with milestones
- Automated plan adjustments based on adherence
- Success metrics and achievements
"""
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from enum import Enum


class AdherenceCategory(str, Enum):
    """Categories for tracking adherence"""
    MEAL_PLAN = "meal_plan"
    EXERCISE = "exercise"
    MEDITATION = "meditation"
    SLEEP = "sleep"
    SUPPLEMENTS = "supplements"
    HYDRATION = "hydration"


class DailyCheckIn(BaseModel):
    """Daily user check-in"""
    user_id: str
    date: date
    adherence: Dict[AdherenceCategory, bool]  # Did they follow each category?
    notes: Optional[str] = None
    mood_rating: Optional[int] = None  # 1-10
    energy_rating: Optional[int] = None  # 1-10
    stress_rating: Optional[int] = None  # 1-10


class AdherenceStats(BaseModel):
    """Adherence statistics"""
    category: AdherenceCategory
    total_days: int
    adherent_days: int
    adherence_percentage: float
    streak_current: int  # Current consecutive days
    streak_longest: int
    recent_trend: str  # improving, stable, declining


class ProgressMilestone(BaseModel):
    """Goal milestone"""
    milestone_id: str
    goal_name: str
    target_metric: str
    target_value: float
    current_value: float
    progress_percentage: float
    achieved: bool
    target_date: Optional[date] = None


class WellnessProgress(BaseModel):
    """Complete wellness progress report"""
    user_id: str
    report_date: date
    overall_adherence: float  # 0-100
    category_adherence: Dict[str, AdherenceStats]
    milestones: List[ProgressMilestone]
    achievements: List[str]
    insights: List[str]
    recommendations: List[str]


class ProgressTracker:
    """Track user progress and adherence"""

    def __init__(self):
        # In-memory storage (in production, use database)
        self.check_ins: Dict[str, List[DailyCheckIn]] = {}
        self.milestones: Dict[str, List[ProgressMilestone]] = {}

    def record_check_in(self, check_in: DailyCheckIn):
        """Record a daily check-in"""
        if check_in.user_id not in self.check_ins:
            self.check_ins[check_in.user_id] = []

        self.check_ins[check_in.user_id].append(check_in)

    def calculate_adherence_stats(
        self,
        user_id: str,
        category: AdherenceCategory,
        days: int = 30
    ) -> AdherenceStats:
        """Calculate adherence stats for a category"""
        if user_id not in self.check_ins:
            return self._empty_stats(category)

        # Get check-ins for last N days
        cutoff_date = date.today() - timedelta(days=days)
        recent_check_ins = [
            ci for ci in self.check_ins[user_id]
            if ci.date >= cutoff_date
        ]

        if not recent_check_ins:
            return self._empty_stats(category)

        # Count adherent days
        adherent_days = sum(
            1 for ci in recent_check_ins
            if ci.adherence.get(category, False)
        )

        total_days = len(recent_check_ins)
        adherence_pct = (adherent_days / total_days * 100) if total_days > 0 else 0

        # Calculate streaks
        current_streak = self._calculate_current_streak(user_id, category)
        longest_streak = self._calculate_longest_streak(user_id, category)

        # Determine trend
        recent_trend = self._determine_trend(user_id, category, days)

        return AdherenceStats(
            category=category,
            total_days=total_days,
            adherent_days=adherent_days,
            adherence_percentage=round(adherence_pct, 1),
            streak_current=current_streak,
            streak_longest=longest_streak,
            recent_trend=recent_trend
        )

    def _calculate_current_streak(self, user_id: str, category: AdherenceCategory) -> int:
        """Calculate current consecutive adherence streak"""
        if user_id not in self.check_ins:
            return 0

        # Sort check-ins by date descending
        sorted_check_ins = sorted(
            self.check_ins[user_id],
            key=lambda x: x.date,
            reverse=True
        )

        streak = 0
        for check_in in sorted_check_ins:
            if check_in.adherence.get(category, False):
                streak += 1
            else:
                break

        return streak

    def _calculate_longest_streak(self, user_id: str, category: AdherenceCategory) -> int:
        """Calculate longest streak ever"""
        if user_id not in self.check_ins:
            return 0

        sorted_check_ins = sorted(self.check_ins[user_id], key=lambda x: x.date)

        max_streak = 0
        current_streak = 0

        for check_in in sorted_check_ins:
            if check_in.adherence.get(category, False):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def _determine_trend(
        self,
        user_id: str,
        category: AdherenceCategory,
        days: int
    ) -> str:
        """Determine if adherence is improving, stable, or declining"""
        if user_id not in self.check_ins:
            return "stable"

        cutoff_date = date.today() - timedelta(days=days)
        recent_check_ins = [
            ci for ci in self.check_ins[user_id]
            if ci.date >= cutoff_date
        ]

        if len(recent_check_ins) < 7:
            return "stable"

        # Compare first half vs second half
        midpoint = len(recent_check_ins) // 2
        first_half = recent_check_ins[:midpoint]
        second_half = recent_check_ins[midpoint:]

        first_adherence = sum(1 for ci in first_half if ci.adherence.get(category, False)) / len(first_half)
        second_adherence = sum(1 for ci in second_half if ci.adherence.get(category, False)) / len(second_half)

        diff = second_adherence - first_adherence

        if diff > 0.15:
            return "improving"
        elif diff < -0.15:
            return "declining"
        else:
            return "stable"

    def _empty_stats(self, category: AdherenceCategory) -> AdherenceStats:
        """Return empty stats"""
        return AdherenceStats(
            category=category,
            total_days=0,
            adherent_days=0,
            adherence_percentage=0,
            streak_current=0,
            streak_longest=0,
            recent_trend="stable"
        )

    def generate_progress_report(self, user_id: str) -> WellnessProgress:
        """Generate comprehensive progress report"""

        # Calculate adherence for all categories
        category_stats = {}
        total_adherence = 0

        for category in AdherenceCategory:
            stats = self.calculate_adherence_stats(user_id, category)
            category_stats[category.value] = stats
            total_adherence += stats.adherence_percentage

        overall_adherence = total_adherence / len(AdherenceCategory) if AdherenceCategory else 0

        # Get milestones
        user_milestones = self.milestones.get(user_id, [])

        # Generate achievements
        achievements = self._generate_achievements(user_id, category_stats)

        # Generate insights
        insights = self._generate_insights(category_stats)

        # Generate recommendations
        recommendations = self._generate_recommendations(category_stats, overall_adherence)

        return WellnessProgress(
            user_id=user_id,
            report_date=date.today(),
            overall_adherence=round(overall_adherence, 1),
            category_adherence=category_stats,
            milestones=user_milestones,
            achievements=achievements,
            insights=insights,
            recommendations=recommendations
        )

    def _generate_achievements(
        self,
        user_id: str,
        category_stats: Dict[str, AdherenceStats]
    ) -> List[str]:
        """Generate achievement badges"""
        achievements = []

        for category, stats in category_stats.items():
            # Streak achievements
            if stats.streak_current >= 7:
                achievements.append(f"🔥 {category.replace('_', ' ').title()} - 7 Day Streak!")
            if stats.streak_current >= 30:
                achievements.append(f"🏆 {category.replace('_', ' ').title()} - 30 Day Streak!")

            # Adherence achievements
            if stats.adherence_percentage >= 90:
                achievements.append(f"⭐ {category.replace('_', ' ').title()} - 90%+ Adherence!")
            if stats.adherence_percentage == 100:
                achievements.append(f"💯 {category.replace('_', ' ').title()} - Perfect Adherence!")

        return achievements

    def _generate_insights(self, category_stats: Dict[str, AdherenceStats]) -> List[str]:
        """Generate insights from data"""
        insights = []

        for category, stats in category_stats.items():
            cat_name = category.replace('_', ' ').title()

            if stats.recent_trend == "improving":
                insights.append(f"📈 {cat_name} adherence is improving - great progress!")

            elif stats.recent_trend == "declining":
                insights.append(f"📉 {cat_name} adherence is declining - may need support")

            if stats.adherence_percentage < 50:
                insights.append(f"⚠️ {cat_name} adherence is low ({stats.adherence_percentage:.0f}%) - consider simplifying")

        return insights

    def _generate_recommendations(
        self,
        category_stats: Dict[str, AdherenceStats],
        overall_adherence: float
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Overall adherence feedback
        if overall_adherence < 50:
            recommendations.append("Your current plan may be too ambitious - let's simplify it together")
            recommendations.append("Focus on 1-2 key habits to build consistency")

        elif overall_adherence < 70:
            recommendations.append("You're making progress! Consider what barriers are preventing full adherence")
            recommendations.append("Try the '2-minute rule' - make habits so easy you can't say no")

        elif overall_adherence >= 85:
            recommendations.append("Outstanding adherence! You're building lasting healthy habits")
            recommendations.append("Consider gradually adding new wellness practices")

        # Category-specific recommendations
        for category, stats in category_stats.items():
            cat_name = category.replace('_', ' ').title()

            if stats.adherence_percentage < 50:
                if category == "meal_plan":
                    recommendations.append(f"{cat_name}: Try meal prepping on weekends for easier adherence")
                elif category == "exercise":
                    recommendations.append(f"{cat_name}: Start with just 10 minutes - consistency beats intensity")
                elif category == "meditation":
                    recommendations.append(f"{cat_name}: Use guided meditations or try shorter 5-minute sessions")
                elif category == "sleep":
                    recommendations.append(f"{cat_name}: Set a bedtime alarm and establish a wind-down routine")

        return recommendations

    def should_adjust_plan(self, user_id: str) -> Dict[str, any]:
        """Determine if plan should be automatically adjusted"""
        report = self.generate_progress_report(user_id)

        adjustments_needed = {
            'should_adjust': False,
            'reasons': [],
            'adjustments': []
        }

        # If overall adherence < 70%, simplify plan
        if report.overall_adherence < 70:
            adjustments_needed['should_adjust'] = True
            adjustments_needed['reasons'].append(
                f"Overall adherence is {report.overall_adherence:.0f}% (target: 70%)"
            )

            # Specific adjustments
            for category, stats in report.category_adherence.items():
                if stats.adherence_percentage < 50:
                    if category == "meal_plan":
                        adjustments_needed['adjustments'].append({
                            'category': category,
                            'action': 'simplify_meals',
                            'details': 'Reduce meal complexity, suggest 3 simple recipes on rotation'
                        })
                    elif category == "exercise":
                        adjustments_needed['adjustments'].append({
                            'category': category,
                            'action': 'reduce_duration',
                            'details': 'Reduce from current plan to 15 min/day minimum'
                        })

        # If stress levels high (from check-ins)
        recent_check_ins = self.check_ins.get(user_id, [])[-7:]
        if recent_check_ins:
            avg_stress = sum(ci.stress_rating for ci in recent_check_ins if ci.stress_rating) / len(recent_check_ins)
            if avg_stress and avg_stress > 7:
                adjustments_needed['should_adjust'] = True
                adjustments_needed['reasons'].append(f"High stress levels detected (avg: {avg_stress:.1f}/10)")
                adjustments_needed['adjustments'].append({
                    'category': 'schedule',
                    'action': 'add_breaks',
                    'details': 'Add more rest periods and breathing exercises to schedule'
                })

        return adjustments_needed


# Singleton instance
_progress_tracker = None


def get_progress_tracker() -> ProgressTracker:
    """Get singleton progress tracker"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
