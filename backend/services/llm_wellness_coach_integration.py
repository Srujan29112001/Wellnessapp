"""
LLM Wellness Coach Integration.

Enhances the LLM wellness coach with deep context from:
- Life Optimization (meal plans, schedules, nutrition)
- Holistic integration (all wellness data combined)
- User profile (complete preferences and goals)
- Real-time biometrics (wearables, EEG, voice)
- Astrological insights
- Dosha analysis

The coach can now provide hyper-personalized advice using ALL available data.
"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime
import json

from backend.models.life_optimization_models import (
    ComprehensiveUserProfile,
    DailyMealPlan,
    DailySchedule
)
from backend.services.holistic_integration import (
    get_holistic_service,
    HolisticWellnessInsight
)


class EnhancedWellnessCoach:
    """
    LLM-powered wellness coach with full system integration.

    This coach has access to EVERYTHING:
    - Complete user profile (9 sections)
    - Today's meal plan
    - Today's schedule
    - Recent biometrics
    - Holistic wellness assessment
    - Historical patterns
    - Astrological influences

    Can answer questions like:
    - "Should I work out now?" (considers energy, schedule, biometrics)
    - "Why am I tired?" (analyzes sleep, nutrition, stress, dosha)
    - "What should I eat for dinner?" (considers meal plan, budget, goals)
    - "Am I on track with my goals?" (analyzes progress across all dimensions)
    """

    def __init__(self):
        """Initialize enhanced coach."""
        self.holistic_service = get_holistic_service()

    def generate_coach_context(
        self,
        profile: ComprehensiveUserProfile,
        meal_plan: Optional[DailyMealPlan] = None,
        schedule: Optional[DailySchedule] = None,
        holistic_insight: Optional[HolisticWellnessInsight] = None,
        wearable_data: Optional[Dict] = None,
        eeg_data: Optional[Dict] = None,
        voice_data: Optional[Dict] = None
    ) -> str:
        """
        Generate comprehensive context for LLM.

        This context gives the LLM full awareness of the user's state.

        Args:
            profile: User profile
            meal_plan: Today's meal plan
            schedule: Today's schedule
            holistic_insight: Holistic wellness assessment
            wearable_data: Recent wearable metrics
            eeg_data: Recent EEG analysis
            voice_data: Recent voice emotion

        Returns:
            Rich context string for LLM prompt
        """
        context_parts = []

        # 1. User Overview
        context_parts.append("=== USER PROFILE ===")
        context_parts.append(f"Name: User {profile.user_id}")
        context_parts.append(f"Age: {profile.physical.age}, Gender: {profile.physical.gender}")
        context_parts.append(f"Location: {profile.lifestyle.region}, {profile.lifestyle.country_code}")
        context_parts.append(f"Occupation: {profile.lifestyle.occupation}")
        context_parts.append("")

        # 2. Constitution & Type
        context_parts.append("=== AYURVEDIC & PERSONALITY ===")
        context_parts.append(f"Dosha: {profile.personality.dosha_type}")
        context_parts.append(f"Dosha %: Vata {profile.personality.dosha_percentages.get('vata', 0)}%, "
                           f"Pitta {profile.personality.dosha_percentages.get('pitta', 0)}%, "
                           f"Kapha {profile.personality.dosha_percentages.get('kapha', 0)}%")
        context_parts.append(f"Chronotype: {profile.personality.chronotype.value}")
        context_parts.append("")

        # 3. Physical Stats
        context_parts.append("=== PHYSICAL METRICS ===")
        context_parts.append(f"Height: {profile.physical.height_cm}cm, Weight: {profile.physical.weight_kg}kg")
        context_parts.append(f"BMI: {profile.physical.bmi}")
        context_parts.append(f"Activity Level: {profile.physical.activity_level.value}")

        if profile.metabolic_profile:
            context_parts.append(f"BMR: {profile.metabolic_profile.get('bmr')} cal/day")
            context_parts.append(f"TDEE: {profile.metabolic_profile.get('tdee')} cal/day")
            context_parts.append(f"Target: {profile.metabolic_profile.get('target_calories')} cal/day")

        context_parts.append("")

        # 4. Goals
        context_parts.append("=== WELLNESS GOALS ===")
        context_parts.append(f"Primary: {profile.goals.primary_goal.value}")
        if profile.goals.secondary_goals:
            context_parts.append(f"Secondary: {', '.join([g.value for g in profile.goals.secondary_goals])}")
        context_parts.append(f"Timeline: {profile.goals.timeline}, Urgency: {profile.goals.urgency}")
        context_parts.append(f"Daily Meditation: {profile.goals.meditation_minutes_daily} min")
        context_parts.append(f"Daily Exercise: {profile.goals.exercise_minutes_daily} min")

        context_parts.append("\nPriorities (0-10):")
        context_parts.append(f"  Nutrition: {profile.goals.priority_nutrition}/10")
        context_parts.append(f"  Exercise: {profile.goals.priority_exercise}/10")
        context_parts.append(f"  Sleep: {profile.goals.priority_sleep}/10")
        context_parts.append(f"  Stress Management: {profile.goals.priority_stress}/10")
        context_parts.append(f"  Spiritual Practice: {profile.goals.priority_spiritual}/10")
        context_parts.append(f"  Budget Adherence: {profile.goals.priority_budget}/10")
        context_parts.append("")

        # 5. Health Conditions
        if profile.health.conditions or profile.health.allergies:
            context_parts.append("=== HEALTH CONSIDERATIONS ===")
            if profile.health.conditions:
                context_parts.append(f"Conditions: {', '.join(profile.health.conditions)}")
            if profile.health.allergies:
                context_parts.append(f"Allergies: {', '.join(profile.health.allergies)}")
            if profile.health.nutrient_deficiencies:
                context_parts.append(f"Deficiencies: {', '.join(profile.health.nutrient_deficiencies)}")
            context_parts.append("")

        # 6. Today's Meal Plan
        if meal_plan:
            context_parts.append("=== TODAY'S MEAL PLAN ===")
            context_parts.append(f"Total: {meal_plan.total_calories} cal | "
                               f"P: {meal_plan.total_protein}g | "
                               f"C: {meal_plan.total_carbs}g | "
                               f"F: {meal_plan.total_fat}g")
            context_parts.append(f"Cost: ${meal_plan.total_cost:.2f}")
            context_parts.append(f"Dosha Balance: {meal_plan.dosha_balance_score}/100")
            context_parts.append(f"Meets Goals: {'✓' if meal_plan.meets_goals else '✗'}")
            context_parts.append(f"Within Budget: {'✓' if meal_plan.meets_budget else '✗'}")

            context_parts.append("\nMeals:")
            for meal in meal_plan.meals:
                context_parts.append(f"  {meal.time.strftime('%H:%M')} - {meal.meal_type.upper()}: {meal.name}")
                context_parts.append(f"    {meal.total_nutrients.calories} cal, {meal.prep_time_minutes} min to prepare")
                ingredients = [f"{i.name} ({i.quantity}{i.unit})" for i in meal.ingredients[:3]]
                context_parts.append(f"    Ingredients: {', '.join(ingredients)}...")

            context_parts.append("")

        # 7. Today's Schedule
        if schedule:
            context_parts.append("=== TODAY'S SCHEDULE ===")
            context_parts.append(f"Sleep: {schedule.sleep_hours}h | Work: {schedule.work_hours}h")
            context_parts.append(f"Exercise: {schedule.exercise_minutes} min | Meditation: {schedule.spiritual_practice_minutes} min")
            context_parts.append(f"Free Time: {schedule.free_time_minutes} min")

            context_parts.append("\nEnergy Forecast:")
            for period, level in schedule.energy_forecast.items():
                context_parts.append(f"  {period.capitalize()}: {level}")

            context_parts.append("\nKey Activities:")
            for activity in schedule.activities[:8]:  # First 8 activities
                context_parts.append(f"  {activity.time.strftime('%H:%M')} - {activity.title} ({activity.duration_minutes}min)")

            context_parts.append("")

        # 8. Real-time Biometrics
        if wearable_data:
            context_parts.append("=== RECENT BIOMETRICS (Wearable) ===")

            if "sleep" in wearable_data:
                sleep = wearable_data["sleep"]
                context_parts.append(f"Last Night's Sleep: {sleep.get('hours', 0)}h, Quality: {sleep.get('quality_score', 0)}/100")
                context_parts.append(f"  Deep: {sleep.get('deep_minutes', 0)}min, REM: {sleep.get('rem_minutes', 0)}min")

            if "hrv" in wearable_data:
                hrv = wearable_data["hrv"]
                context_parts.append(f"HRV: {hrv.get('rmssd', 0)}ms (stress indicator)")

            if "steps" in wearable_data:
                context_parts.append(f"Steps Today: {wearable_data['steps']}")

            if "resting_heart_rate" in wearable_data:
                context_parts.append(f"Resting HR: {wearable_data['resting_heart_rate']} bpm")

            context_parts.append("")

        # 9. Brain State
        if eeg_data:
            context_parts.append("=== RECENT BRAIN STATE (EEG) ===")
            context_parts.append(f"Dominant State: {eeg_data.get('dominant_state', 'unknown')}")
            context_parts.append(f"Alpha Power: {eeg_data.get('alpha_power', 0):.2f} (relaxation)")
            context_parts.append(f"Beta Power: {eeg_data.get('beta_power', 0):.2f} (focus/stress)")
            context_parts.append(f"Theta Power: {eeg_data.get('theta_power', 0):.2f} (meditation/drowsiness)")
            context_parts.append("")

        # 10. Emotional State
        if voice_data:
            context_parts.append("=== RECENT EMOTIONAL STATE (Voice) ===")
            context_parts.append(f"Primary Emotion: {voice_data.get('primary_emotion', 'unknown')}")
            context_parts.append(f"Confidence: {voice_data.get('confidence', 0):.0%}")
            context_parts.append("")

        # 11. Holistic Assessment
        if holistic_insight:
            context_parts.append("=== HOLISTIC WELLNESS ASSESSMENT ===")
            context_parts.append(f"Overall Score: {holistic_insight.overall_wellness_score}/100")
            context_parts.append(f"Physical: {holistic_insight.physical_score}/100")
            context_parts.append(f"Mental: {holistic_insight.mental_score}/100")
            context_parts.append(f"Emotional: {holistic_insight.emotional_score}/100")
            context_parts.append(f"Spiritual: {holistic_insight.spiritual_score}/100")
            context_parts.append(f"Nutritional: {holistic_insight.nutritional_score}/100")

            if holistic_insight.warnings:
                context_parts.append("\n⚠️ WARNINGS:")
                for warning in holistic_insight.warnings:
                    context_parts.append(f"  - {warning}")

            if holistic_insight.key_insights:
                context_parts.append("\n💡 KEY INSIGHTS:")
                for insight in holistic_insight.key_insights[:3]:
                    context_parts.append(f"  - {insight}")

            if holistic_insight.recommendations:
                context_parts.append("\n✅ RECOMMENDATIONS:")
                for rec in holistic_insight.recommendations[:5]:
                    context_parts.append(f"  - {rec}")

            context_parts.append(f"\nData Sources: {', '.join(holistic_insight.data_sources)}")
            context_parts.append("")

        # 12. Dietary Preferences
        context_parts.append("=== DIETARY PREFERENCES ===")
        context_parts.append(f"Diet Type: {profile.dietary_preferences.diet_type.value}")
        context_parts.append(f"Cuisines: {', '.join(profile.dietary_preferences.cuisine_preferences)}")
        if profile.dietary_preferences.disliked_foods:
            context_parts.append(f"Dislikes: {', '.join(profile.dietary_preferences.disliked_foods)}")
        context_parts.append(f"Budget: ${profile.dietary_preferences.budget_per_week}/week ({profile.dietary_preferences.budget_currency})")
        context_parts.append(f"Cooking Skill: {profile.dietary_preferences.cooking_skill.value}")
        context_parts.append(f"Time Available: {profile.dietary_preferences.cooking_time_available} min/meal")
        context_parts.append("")

        return "\n".join(context_parts)

    def create_enhanced_prompt(
        self,
        user_question: str,
        context: str
    ) -> str:
        """
        Create enhanced LLM prompt with full context.

        Args:
            user_question: User's question
            context: Generated context from generate_coach_context()

        Returns:
            Complete prompt for LLM
        """
        system_prompt = """You are an advanced AI wellness coach with deep expertise in:
- Ayurveda and Traditional Medicine
- Nutritional Science and Functional Medicine
- Exercise Physiology and Biomechanics
- Neuroscience and Mental Health
- Chronobiology and Circadian Rhythms
- Vedic Astrology and Energy Medicine
- Mindfulness and Spiritual Practices

You have complete access to the user's wellness data including:
- Comprehensive health profile
- Real-time biometrics (sleep, HRV, activity)
- Brain state (EEG analysis)
- Emotional state (voice analysis)
- Today's personalized meal plan
- Today's optimized schedule
- Dosha constitution and imbalances
- Goals and priorities

INSTRUCTIONS:
1. Provide hyper-personalized advice using ALL available data
2. Reference specific data points (e.g., "Your HRV of 25ms indicates...")
3. Consider dosha type in ALL recommendations
4. Explain WHY (e.g., "As a Pitta type, you're prone to...")
5. Be actionable and specific (exact times, foods, practices)
6. Consider current state (tired, stressed) and adjust accordingly
7. Connect multiple data sources (e.g., "Your low sleep quality + high stress...")
8. Prioritize based on user's priority settings
9. Stay within budget constraints when recommending foods
10. Be encouraging but honest about challenges

TONE:
- Warm, supportive, knowledgeable
- Like a wise friend who deeply knows the user
- Balance scientific rigor with holistic wisdom
"""

        full_prompt = f"""{system_prompt}

{context}

=== USER QUESTION ===
{user_question}

=== YOUR RESPONSE ===
(Provide comprehensive, personalized advice using the context above)
"""

        return full_prompt

    def answer_question(
        self,
        user_question: str,
        profile: ComprehensiveUserProfile,
        meal_plan: Optional[DailyMealPlan] = None,
        schedule: Optional[DailySchedule] = None,
        holistic_insight: Optional[HolisticWellnessInsight] = None,
        wearable_data: Optional[Dict] = None,
        eeg_data: Optional[Dict] = None,
        voice_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Answer user question with full context.

        This method would integrate with the LLM service (GPT, Claude, or local model).

        Args:
            user_question: Question from user
            All other args: Context data

        Returns:
            Dict with answer and metadata
        """
        # Generate context
        context = self.generate_coach_context(
            profile=profile,
            meal_plan=meal_plan,
            schedule=schedule,
            holistic_insight=holistic_insight,
            wearable_data=wearable_data,
            eeg_data=eeg_data,
            voice_data=voice_data
        )

        # Create enhanced prompt
        prompt = self.create_enhanced_prompt(user_question, context)

        # Here you would call the LLM service
        # For now, return structured response showing what would be sent

        return {
            "user_question": user_question,
            "context_provided": {
                "profile": True,
                "meal_plan": meal_plan is not None,
                "schedule": schedule is not None,
                "holistic_insight": holistic_insight is not None,
                "wearable_data": wearable_data is not None,
                "eeg_data": eeg_data is not None,
                "voice_data": voice_data is not None
            },
            "prompt_length": len(prompt),
            "full_prompt": prompt,
            "note": "This prompt would be sent to LLM service (GPT/Claude/Local) for personalized response"
        }


# Singleton
_enhanced_coach = None


def get_enhanced_coach() -> EnhancedWellnessCoach:
    """Get singleton enhanced wellness coach."""
    global _enhanced_coach
    if _enhanced_coach is None:
        _enhanced_coach = EnhancedWellnessCoach()
    return _enhanced_coach


# Example usage
if __name__ == "__main__":
    from datetime import date, time as dt_time
    from backend.models.life_optimization_models import (
        BirthDetails, PersonalityProfile, PhysicalProfile,
        HealthProfile, DietaryPreferences, LifestyleProfile,
        SleepPreferences, WellnessGoals, CustomPreferences,
        ActivityLevel, GoalType, DietType, CookingSkill, ChronotypeEnum
    )

    # Mock profile
    profile = ComprehensiveUserProfile(
        user_id="user123",
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
            activity_level=ActivityLevel.MODERATE,
            bmi=24.5
        ),
        health=HealthProfile(
            conditions=[],
            allergies=["peanuts"],
            nutrient_deficiencies=["vitamin_d"]
        ),
        dietary_preferences=DietaryPreferences(
            diet_type=DietType.VEGETARIAN,
            cuisine_preferences=["indian", "mediterranean"],
            disliked_foods=["mushrooms"],
            budget_per_week=100,
            budget_currency="USD",
            cooking_skill=CookingSkill.INTERMEDIATE,
            cooking_time_available=45,
            meal_prep_preference="daily"
        ),
        lifestyle=LifestyleProfile(
            region="Mumbai, Maharashtra, India",
            country_code="IN",
            timezone="Asia/Kolkata",
            occupation="Software Engineer",
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
            secondary_goals=[GoalType.MENTAL_STRENGTH],
            timeline="3_months",
            urgency="balanced",
            meditation_minutes_daily=20,
            exercise_minutes_daily=45,
            priority_nutrition=8,
            priority_exercise=7,
            priority_sleep=8,
            priority_stress=7,
            priority_spiritual=6,
            priority_budget=5
        ),
        custom_preferences=CustomPreferences(
            exercise_preferences=["yoga", "weights"],
            spiritual_practices=["meditation"],
            supplement_stack=["vitamin_d", "omega_3"]
        ),
        metabolic_profile={
            "bmr": 1680,
            "tdee": 2320,
            "target_calories": 2400
        }
    )

    # Mock wearable data
    wearable_data = {
        "sleep": {
            "hours": 6.5,
            "quality_score": 55,
            "deep_minutes": 70,
            "rem_minutes": 85
        },
        "hrv": {
            "rmssd": 18
        },
        "steps": 4200,
        "resting_heart_rate": 72
    }

    # Mock EEG data
    eeg_data = {
        "dominant_state": "anxious",
        "alpha_power": 0.25,
        "beta_power": 0.45,
        "theta_power": 0.15
    }

    coach = get_enhanced_coach()
    result = coach.answer_question(
        user_question="Why am I feeling so tired and anxious today? What should I do?",
        profile=profile,
        wearable_data=wearable_data,
        eeg_data=eeg_data
    )

    print("=== ENHANCED WELLNESS COACH ===\n")
    print(f"Question: {result['user_question']}\n")
    print(f"Context Provided: {result['context_provided']}\n")
    print(f"Prompt Length: {result['prompt_length']} characters\n")
    print(f"\nFull Prompt Preview (first 1000 chars):\n{result['full_prompt'][:1000]}...")
