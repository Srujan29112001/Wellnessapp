"""
Schedule Optimization Service.

Creates optimal daily schedules based on:
- Chronotype (early bird, night owl)
- Energy patterns throughout day
- Dosha type (Ayurvedic daily routine)
- Work commitments
- Wellness goals
- Planetary hours (optional)
- Meal timing (from meal plan)
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, time as dt_time, datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from backend.models.life_optimization_models import (
    ComprehensiveUserProfile,
    DailySchedule,
    ScheduleActivity,
    DailyMealPlan,
    ChronotypeEnum,
    GoalType
)


class EnergyLevel(str, Enum):
    """Energy levels throughout the day."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    PEAK = "peak"


class ActivityPriority(str, Enum):
    """Activity priority levels."""
    ESSENTIAL = "essential"  # Sleep, meals, work
    HIGH = "high"  # Exercise, meditation
    MEDIUM = "medium"  # Learning, creative work
    LOW = "low"  # Leisure, optional


@dataclass
class TimeBlock:
    """Time block for scheduling."""
    start_time: dt_time
    end_time: dt_time
    duration_minutes: int
    available: bool
    energy_level: EnergyLevel
    dosha_period: str  # vata, pitta, kapha
    planetary_hour: Optional[str] = None


class ScheduleOptimizer:
    """Optimize daily schedules based on multiple factors."""

    # Ayurvedic time periods (doshas rule different times)
    DOSHA_PERIODS = {
        "vata_morning": {"start": dt_time(2, 0), "end": dt_time(6, 0), "dosha": "vata"},
        "kapha_morning": {"start": dt_time(6, 0), "end": dt_time(10, 0), "dosha": "kapha"},
        "pitta_midday": {"start": dt_time(10, 0), "end": dt_time(14, 0), "dosha": "pitta"},
        "vata_afternoon": {"start": dt_time(14, 0), "end": dt_time(18, 0), "dosha": "vata"},
        "kapha_evening": {"start": dt_time(18, 0), "end": dt_time(22, 0), "dosha": "kapha"},
        "pitta_night": {"start": dt_time(22, 0), "end": dt_time(2, 0), "dosha": "pitta"},
    }

    # Activity recommendations by dosha period
    DOSHA_ACTIVITY_RECOMMENDATIONS = {
        "vata": ["meditation", "spiritual_practice", "creative_work", "gentle_movement"],
        "kapha": ["wake_up", "exercise", "learning", "routine_tasks"],
        "pitta": ["eating", "intense_work", "decision_making", "physical_activity"],
    }

    # Chronotype patterns
    CHRONOTYPE_PATTERNS = {
        ChronotypeEnum.EARLY_BIRD: {
            "peak_hours": [dt_time(9, 0), dt_time(10, 0), dt_time(11, 0)],
            "optimal_wake": dt_time(6, 0),
            "optimal_sleep": dt_time(22, 0),
            "exercise_time": "morning",
            "deep_work_time": "morning"
        },
        ChronotypeEnum.NIGHT_OWL: {
            "peak_hours": [dt_time(15, 0), dt_time(16, 0), dt_time(17, 0), dt_time(20, 0)],
            "optimal_wake": dt_time(8, 0),
            "optimal_sleep": dt_time(0, 0),
            "exercise_time": "evening",
            "deep_work_time": "afternoon"
        },
        ChronotypeEnum.INTERMEDIATE: {
            "peak_hours": [dt_time(10, 0), dt_time(11, 0), dt_time(14, 0), dt_time(15, 0)],
            "optimal_wake": dt_time(7, 0),
            "optimal_sleep": dt_time(23, 0),
            "exercise_time": "morning_or_afternoon",
            "deep_work_time": "mid_morning"
        }
    }

    # Planetary hours (Vedic astrology) - 7 classical planets
    PLANETARY_ACTIVITIES = {
        "Sun": ["leadership", "authority", "vitality", "father_work", "government"],
        "Moon": ["emotions", "mother", "public", "water", "intuition", "meditation"],
        "Mars": ["exercise", "competition", "courage", "surgery", "conflict"],
        "Mercury": ["learning", "communication", "writing", "business", "technology"],
        "Jupiter": ["teaching", "wisdom", "expansion", "finances", "spirituality"],
        "Venus": ["art", "beauty", "relationships", "luxury", "creativity"],
        "Saturn": ["discipline", "hard_work", "structure", "karma", "elderly"]
    }

    def __init__(self):
        """Initialize schedule optimizer."""
        pass

    def generate_daily_schedule(
        self,
        profile: ComprehensiveUserProfile,
        target_date: date,
        meal_plan: Optional[DailyMealPlan] = None,
        include_planetary_hours: bool = False
    ) -> DailySchedule:
        """
        Generate optimized daily schedule.

        Args:
            profile: User profile
            target_date: Date for schedule
            meal_plan: Meal plan for the day (optional)
            include_planetary_hours: Include planetary hour guidance

        Returns:
            Optimized daily schedule
        """
        activities = []

        # 1. Get wake/sleep times
        wake_time = profile.sleep_preferences.preferred_wake_time
        bed_time = profile.sleep_preferences.preferred_bedtime

        # 2. Calculate energy forecast
        energy_forecast = self._calculate_energy_forecast(
            profile.personality.chronotype,
            wake_time,
            bed_time
        )

        # 3. Add essential activities
        # Wake up
        activities.append(ScheduleActivity(
            time=wake_time,
            duration_minutes=30,
            activity_type="wake_up",
            title="Wake Up & Morning Routine",
            description="Hydrate, bathroom, light stretching",
            energy_required="low",
            priority=10,
            reason="Start day with grounding routine",
            related_goal=None
        ))

        # 4. Add spiritual practices (early morning - Brahma Muhurta for some)
        if profile.goals.meditation_minutes_daily > 0:
            # Meditation best in Vata time (early morning)
            meditation_time = self._add_minutes_to_time(wake_time, 30)
            activities.append(ScheduleActivity(
                time=meditation_time,
                duration_minutes=profile.goals.meditation_minutes_daily,
                activity_type="meditation",
                title="Meditation & Pranayama",
                description="Mindfulness practice, breath work",
                energy_required="low",
                priority=9,
                reason="Vata time - ideal for spiritual practice, mental clarity",
                related_goal=str(GoalType.SPIRITUAL_STRENGTH)
            ))

        # 5. Add exercise
        if profile.goals.exercise_minutes_daily > 0:
            exercise_time = self._determine_exercise_time(
                profile.personality.chronotype,
                wake_time,
                bed_time,
                activities
            )

            activities.append(ScheduleActivity(
                time=exercise_time,
                duration_minutes=profile.goals.exercise_minutes_daily,
                activity_type="exercise",
                title=f"{', '.join(profile.custom_preferences.exercise_preferences[:2]) if profile.custom_preferences.exercise_preferences else 'Exercise'}",
                description="Physical training session",
                energy_required="high",
                priority=8,
                reason=self._get_exercise_timing_reason(exercise_time, profile.personality.dosha_type),
                related_goal=str(profile.goals.primary_goal)
            ))

        # 6. Add meals from meal plan
        if meal_plan:
            for meal in meal_plan.meals:
                activities.append(ScheduleActivity(
                    time=meal.time,
                    duration_minutes=meal.prep_time_minutes + 15,  # cooking + eating
                    activity_type="meal",
                    title=f"{meal.meal_type.capitalize()}: {meal.name}",
                    description=f"{meal.total_nutrients.calories} cal, {meal.total_nutrients.protein_g}g protein",
                    energy_required="low",
                    priority=10,
                    reason=meal.timing_reason,
                    meal_id=meal.meal_id,
                    related_goal=None
                ))

        # 7. Add work blocks
        work_start, work_end = self._parse_work_hours(profile.lifestyle.typical_work_hours)
        if work_start and work_end:
            # Break work into focused blocks
            current_time = work_start
            block_count = 0

            while current_time < work_end:
                # Pomodoro-style: 90-minute deep work blocks
                block_duration = min(90, self._minutes_between(current_time, work_end))

                if block_duration >= 30:  # Only add if meaningful duration
                    block_count += 1

                    # Determine work type based on energy
                    hour = current_time.hour
                    if hour in [10, 11, 14, 15]:  # Peak hours for most people
                        work_type = "Deep Work"
                        description = "Focus on complex, creative tasks"
                    else:
                        work_type = "Regular Work"
                        description = "Meetings, emails, routine tasks"

                    activities.append(ScheduleActivity(
                        time=current_time,
                        duration_minutes=block_duration,
                        activity_type="work",
                        title=f"{work_type} Block {block_count}",
                        description=description,
                        location="office" if profile.lifestyle.work_schedule_type != "remote" else "home",
                        energy_required="moderate" if "Deep" in work_type else "low",
                        priority=9,
                        reason=f"{work_type} scheduled during {'peak' if hour in [10, 11, 14, 15] else 'regular'} energy",
                        related_goal=None
                    ))

                    # Add break after block
                    break_time = self._add_minutes_to_time(current_time, block_duration)
                    if break_time < work_end:
                        activities.append(ScheduleActivity(
                            time=break_time,
                            duration_minutes=15,
                            activity_type="break",
                            title="Break & Movement",
                            description="Walk, stretch, hydrate",
                            energy_required="low",
                            priority=7,
                            reason="Recovery between work blocks",
                            related_goal=None
                        ))

                    current_time = self._add_minutes_to_time(break_time, 15)
                else:
                    break

        # 8. Add evening wind-down
        wind_down_time = self._add_minutes_to_time(bed_time, -60)
        activities.append(ScheduleActivity(
            time=wind_down_time,
            duration_minutes=30,
            activity_type="wind_down",
            title="Evening Wind Down",
            description="Light reading, gentle yoga, journaling",
            energy_required="low",
            priority=8,
            reason="Kapha time - prepare body for rest",
            related_goal=None
        ))

        # 9. Sleep
        activities.append(ScheduleActivity(
            time=bed_time,
            duration_minutes=int(profile.sleep_preferences.ideal_sleep_duration * 60),
            activity_type="sleep",
            title="Sleep",
            description="Restorative sleep",
            energy_required="low",
            priority=10,
            reason="Recovery and cellular repair",
            related_goal=None
        ))

        # 10. Add free time blocks
        activities = self._add_free_time_blocks(activities, wake_time, bed_time)

        # Sort activities by time
        activities.sort(key=lambda x: (x.time.hour, x.time.minute))

        # 11. Calculate summary stats
        sleep_hours = profile.sleep_preferences.ideal_sleep_duration
        work_hours = self._minutes_between(work_start, work_end) / 60 if work_start and work_end else 8
        exercise_minutes = profile.goals.exercise_minutes_daily
        spiritual_minutes = profile.goals.meditation_minutes_daily
        meal_count = len(meal_plan.meals) if meal_plan else 3

        # Calculate free time
        total_scheduled_minutes = sum([a.duration_minutes for a in activities if a.activity_type != "sleep"])
        awake_minutes = (24 - sleep_hours) * 60
        free_time_minutes = max(0, awake_minutes - total_scheduled_minutes)

        # 12. Planetary guidance (optional)
        planetary_guidance = None
        if include_planetary_hours:
            planetary_guidance = self._get_planetary_guidance(target_date, profile)

        return DailySchedule(
            date=target_date,
            user_id=profile.user_id,
            activities=activities,
            sleep_hours=sleep_hours,
            work_hours=work_hours,
            exercise_minutes=exercise_minutes,
            spiritual_practice_minutes=spiritual_minutes,
            meal_count=meal_count,
            free_time_minutes=int(free_time_minutes),
            energy_forecast=energy_forecast,
            planetary_guidance=planetary_guidance,
            generated_at=datetime.utcnow()
        )

    def _calculate_energy_forecast(
        self,
        chronotype: ChronotypeEnum,
        wake_time: dt_time,
        bed_time: dt_time
    ) -> Dict[str, str]:
        """Calculate energy levels throughout the day."""
        pattern = self.CHRONOTYPE_PATTERNS.get(chronotype, self.CHRONOTYPE_PATTERNS[ChronotypeEnum.INTERMEDIATE])

        forecast = {}

        # Morning
        if chronotype == ChronotypeEnum.EARLY_BIRD:
            forecast["morning"] = "high"
            forecast["afternoon"] = "moderate"
            forecast["evening"] = "low"
        elif chronotype == ChronotypeEnum.NIGHT_OWL:
            forecast["morning"] = "low"
            forecast["afternoon"] = "moderate"
            forecast["evening"] = "high"
        else:
            forecast["morning"] = "moderate"
            forecast["afternoon"] = "high"
            forecast["evening"] = "moderate"

        return forecast

    def _determine_exercise_time(
        self,
        chronotype: ChronotypeEnum,
        wake_time: dt_time,
        bed_time: dt_time,
        existing_activities: List[ScheduleActivity]
    ) -> dt_time:
        """Determine optimal exercise time."""
        pattern = self.CHRONOTYPE_PATTERNS[chronotype]

        if pattern["exercise_time"] == "morning":
            # 45-60 min after waking (after meditation)
            return self._add_minutes_to_time(wake_time, 75)
        elif pattern["exercise_time"] == "evening":
            # 2-3 hours before bed
            return self._add_minutes_to_time(bed_time, -150)
        else:
            # Mid-morning
            return self._add_minutes_to_time(wake_time, 120)

    def _get_exercise_timing_reason(self, exercise_time: dt_time, dosha: str) -> str:
        """Get reason for exercise timing."""
        hour = exercise_time.hour

        reasons = []

        # Dosha timing
        if 6 <= hour < 10:
            reasons.append("Kapha time - exercise breaks up sluggishness")
        elif 10 <= hour < 14:
            reasons.append("Pitta time - strong digestive fire supports intense activity")
        elif 14 <= hour < 18:
            reasons.append("Vata time - movement grounds Vata energy")

        # Personal dosha
        if "kapha" in dosha.lower():
            reasons.append("Morning exercise essential for Kapha")
        elif "pitta" in dosha.lower():
            reasons.append("Moderate intensity to avoid overheating Pitta")
        elif "vata" in dosha.lower():
            reasons.append("Grounding exercise to balance Vata")

        return " | ".join(reasons)

    def _parse_work_hours(self, work_hours_str: str) -> Tuple[Optional[dt_time], Optional[dt_time]]:
        """Parse work hours string like '9:00-17:00'."""
        try:
            start_str, end_str = work_hours_str.split("-")
            start_hour, start_min = map(int, start_str.split(":"))
            end_hour, end_min = map(int, end_str.split(":"))
            return dt_time(start_hour, start_min), dt_time(end_hour, end_min)
        except:
            return None, None

    def _add_minutes_to_time(self, time_obj: dt_time, minutes: int) -> dt_time:
        """Add minutes to time object."""
        dt = datetime.combine(date.today(), time_obj)
        new_dt = dt + timedelta(minutes=minutes)
        return new_dt.time()

    def _minutes_between(self, start: dt_time, end: dt_time) -> int:
        """Calculate minutes between two times."""
        start_dt = datetime.combine(date.today(), start)
        end_dt = datetime.combine(date.today(), end)

        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        delta = end_dt - start_dt
        return int(delta.total_seconds() / 60)

    def _add_free_time_blocks(
        self,
        activities: List[ScheduleActivity],
        wake_time: dt_time,
        bed_time: dt_time
    ) -> List[ScheduleActivity]:
        """Add free time blocks in gaps."""
        # Sort by time
        sorted_activities = sorted(activities, key=lambda x: (x.time.hour, x.time.minute))

        new_activities = []
        current_time = wake_time

        for activity in sorted_activities:
            # Check gap
            gap_minutes = self._minutes_between(current_time, activity.time)

            if gap_minutes >= 30:  # Meaningful free time
                new_activities.append(ScheduleActivity(
                    time=current_time,
                    duration_minutes=gap_minutes,
                    activity_type="free_time",
                    title="Personal Time",
                    description="Hobbies, social, leisure",
                    energy_required="low",
                    priority=3,
                    reason="Unstructured time for flexibility",
                    related_goal=None
                ))

            new_activities.append(activity)

            # Update current time
            current_time = self._add_minutes_to_time(activity.time, activity.duration_minutes)

        return new_activities

    def _get_planetary_guidance(self, target_date: date, profile: ComprehensiveUserProfile) -> List[str]:
        """Get planetary hour guidance for the day."""
        # Simplified planetary guidance (would integrate with natal chart service)
        guidance = [
            "Sun hour (sunrise): Leadership activities, vitality building",
            "Jupiter hour (mid-morning): Learning, teaching, financial planning",
            "Mercury hour (midday): Communication, writing, business",
            "Venus hour (afternoon): Creative work, relationships, beauty",
            "Mars hour (evening): Physical activity, competitive tasks",
            "Moon hour (night): Reflection, emotional processing, intuition"
        ]

        return guidance[:3]  # Top 3 recommendations


# Singleton
_schedule_optimizer = None


def get_schedule_optimizer() -> ScheduleOptimizer:
    """Get singleton schedule optimizer."""
    global _schedule_optimizer
    if _schedule_optimizer is None:
        _schedule_optimizer = ScheduleOptimizer()
    return _schedule_optimizer


# Example usage
if __name__ == "__main__":
    from backend.models.life_optimization_models import (
        BirthDetails,
        PersonalityProfile,
        PhysicalProfile,
        HealthProfile,
        DietaryPreferences,
        LifestyleProfile,
        SleepPreferences,
        WellnessGoals,
        CustomPreferences,
        ActivityLevel,
        GoalType,
        DietType,
        CookingSkill
    )

    # Mock profile
    profile = ComprehensiveUserProfile(
        user_id="test_user",
        birth_details=BirthDetails(
            date=date(1990, 7, 25),
            time=dt_time(14, 30),
            place="Mumbai, India",
            latitude=19.0760,
            longitude=72.8777,
            timezone="Asia/Kolkata"
        ),
        personality=PersonalityProfile(
            big_five={"openness": 0.7, "conscientiousness": 0.8, "extraversion": 0.6, "agreeableness": 0.7, "neuroticism": 0.4},
            chronotype=ChronotypeEnum.EARLY_BIRD,
            dosha_type="pitta-vata",
            dosha_percentages={"vata": 30, "pitta": 50, "kapha": 20}
        ),
        physical=PhysicalProfile(
            age=33,
            gender="male",
            height_cm=175,
            weight_kg=75,
            activity_level=ActivityLevel.MODERATE
        ),
        health=HealthProfile(),
        dietary_preferences=DietaryPreferences(
            diet_type=DietType.VEGETARIAN,
            cuisine_preferences=["indian"],
            budget_per_week=100,
            budget_currency="USD",
            cooking_skill=CookingSkill.INTERMEDIATE,
            cooking_time_available=45,
            meal_prep_preference="daily"
        ),
        lifestyle=LifestyleProfile(
            region="Mumbai",
            country_code="IN",
            timezone="Asia/Kolkata",
            occupation="Engineer",
            work_schedule_type="remote",
            typical_work_hours="9:00-18:00"
        ),
        sleep_preferences=SleepPreferences(
            ideal_sleep_duration=7.5,
            preferred_bedtime=dt_time(22, 30),
            preferred_wake_time=dt_time(6, 0),
            current_sleep_quality=7
        ),
        goals=WellnessGoals(
            primary_goal=GoalType.PHYSICAL_STRENGTH,
            timeline="3_months",
            urgency="balanced",
            meditation_minutes_daily=20,
            exercise_minutes_daily=45
        ),
        custom_preferences=CustomPreferences(
            exercise_preferences=["yoga", "weights"]
        )
    )

    optimizer = get_schedule_optimizer()
    schedule = optimizer.generate_daily_schedule(profile, date.today())

    print("=== OPTIMIZED DAILY SCHEDULE ===\n")
    for activity in schedule.activities[:10]:
        print(f"{activity.time.strftime('%H:%M')} - {activity.title} ({activity.duration_minutes} min)")
        print(f"  Reason: {activity.reason}\n")

    print(f"Work hours: {schedule.work_hours}")
    print(f"Exercise: {schedule.exercise_minutes} min")
    print(f"Free time: {schedule.free_time_minutes} min")
