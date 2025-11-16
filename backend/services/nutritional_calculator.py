"""
Nutritional Calculator Service.

Calculates personalized nutritional requirements based on:
- Physical metrics (BMR, TDEE)
- Goals (weight loss, muscle gain, etc.)
- Dosha type (Ayurvedic constitution)
- Activity level
- Health conditions
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from backend.models.life_optimization_models import (
    PhysicalProfile,
    ActivityLevel,
    GoalType,
    HealthProfile,
    PersonalityProfile,
    WellnessGoals,
    ComprehensiveUserProfile
)


class MacroDistribution(str, Enum):
    """Macro distribution patterns."""
    BALANCED = "balanced"  # 40/30/30
    HIGH_PROTEIN = "high_protein"  # 30/40/30
    LOW_CARB = "low_carb"  # 50/25/25
    KETO = "keto"  # 70/25/5
    ENDURANCE = "endurance"  # 25/20/55


@dataclass
class DailyNutritionRequirements:
    """Daily nutritional requirements."""
    # Energy
    bmr: float  # Basal Metabolic Rate
    tdee: float  # Total Daily Energy Expenditure
    target_calories: float  # Adjusted for goals

    # Macronutrients (grams)
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float

    # Percentages
    protein_percent: int
    carbs_percent: int
    fat_percent: int

    # Micronutrients (daily values)
    vitamin_a_mcg: float
    vitamin_c_mg: float
    vitamin_d_mcg: float
    vitamin_e_mg: float
    vitamin_k_mcg: float
    b_complex: Dict[str, float]

    calcium_mg: float
    iron_mg: float
    magnesium_mg: float
    potassium_mg: float
    zinc_mg: float
    selenium_mcg: float

    # Hydration
    water_ml: int

    # Ayurvedic guidance
    dosha_dietary_guidelines: Dict[str, List[str]]
    foods_to_favor: List[str]
    foods_to_reduce: List[str]

    # Meal timing
    meal_frequency: int  # meals per day
    eating_window_hours: Optional[int]  # for IF
    largest_meal_time: str  # breakfast, lunch, dinner

    # Reasoning
    calculation_notes: List[str]


class NutritionalCalculator:
    """Calculate personalized nutritional requirements."""

    # Micronutrient RDAs (Recommended Daily Allowances)
    MICRONUTRIENT_RDA = {
        "male": {
            "vitamin_a_mcg": 900,
            "vitamin_c_mg": 90,
            "vitamin_d_mcg": 15,
            "vitamin_e_mg": 15,
            "vitamin_k_mcg": 120,
            "b1_thiamin_mg": 1.2,
            "b2_riboflavin_mg": 1.3,
            "b3_niacin_mg": 16,
            "b6_mg": 1.3,
            "b12_mcg": 2.4,
            "folate_mcg": 400,
            "calcium_mg": 1000,
            "iron_mg": 8,
            "magnesium_mg": 400,
            "potassium_mg": 3400,
            "zinc_mg": 11,
            "selenium_mcg": 55,
        },
        "female": {
            "vitamin_a_mcg": 700,
            "vitamin_c_mg": 75,
            "vitamin_d_mcg": 15,
            "vitamin_e_mg": 15,
            "vitamin_k_mcg": 90,
            "b1_thiamin_mg": 1.1,
            "b2_riboflavin_mg": 1.1,
            "b3_niacin_mg": 14,
            "b6_mg": 1.3,
            "b12_mcg": 2.4,
            "folate_mcg": 400,
            "calcium_mg": 1000,
            "iron_mg": 18,
            "magnesium_mg": 310,
            "potassium_mg": 2600,
            "zinc_mg": 8,
            "selenium_mcg": 55,
        }
    }

    # Activity level multipliers for TDEE
    ACTIVITY_MULTIPLIERS = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHT: 1.375,
        ActivityLevel.MODERATE: 1.55,
        ActivityLevel.VERY_ACTIVE: 1.725,
        ActivityLevel.EXTREMELY_ACTIVE: 1.9,
    }

    # Dosha dietary guidelines (Ayurveda)
    DOSHA_GUIDELINES = {
        "vata": {
            "qualities": ["Dry", "Light", "Cold", "Rough", "Subtle", "Mobile"],
            "balance_with": ["Warm", "Moist", "Heavy", "Smooth", "Grounding"],
            "favor": [
                "Warm, cooked foods",
                "Healthy fats (ghee, sesame oil, nuts)",
                "Sweet, sour, salty tastes",
                "Root vegetables",
                "Whole grains (rice, oats)",
                "Dairy (warm milk, ghee)",
                "Sweet fruits (bananas, avocados)",
                "Warming spices (ginger, cinnamon, cumin)"
            ],
            "reduce": [
                "Raw, cold foods",
                "Dry, light foods (crackers, chips)",
                "Bitter, pungent, astringent tastes",
                "Nightshades (excess)",
                "Caffeine (excess)",
                "Beans (except mung dal)",
                "Cruciferous vegetables (excess)"
            ],
            "meal_timing": "Regular meal times essential, never skip meals",
            "portion_size": "Moderate portions, don't under-eat"
        },
        "pitta": {
            "qualities": ["Hot", "Sharp", "Light", "Oily", "Liquid"],
            "balance_with": ["Cool", "Mild", "Dry", "Grounding"],
            "favor": [
                "Cool, refreshing foods",
                "Sweet, bitter, astringent tastes",
                "Cucumber, leafy greens, zucchini",
                "Sweet fruits (melons, grapes, coconut)",
                "Whole grains (basmati rice, barley, oats)",
                "Cooling herbs (cilantro, mint, fennel)",
                "Moderate amounts of ghee, coconut oil",
                "Legumes (mung beans, chickpeas)"
            ],
            "reduce": [
                "Spicy, hot, pungent foods",
                "Sour, salty tastes (excess)",
                "Fried, oily foods",
                "Red meat",
                "Alcohol",
                "Caffeine",
                "Tomatoes, onions, garlic (excess)",
                "Sour fruits (citrus in excess)"
            ],
            "meal_timing": "Regular meals, largest at lunch (peak Agni)",
            "portion_size": "Moderate portions, avoid overeating"
        },
        "kapha": {
            "qualities": ["Heavy", "Slow", "Cold", "Oily", "Smooth", "Dense"],
            "balance_with": ["Light", "Stimulating", "Warm", "Dry"],
            "favor": [
                "Light, warm, dry foods",
                "Pungent, bitter, astringent tastes",
                "Leafy greens, cruciferous vegetables",
                "Legumes (lentils, split peas)",
                "Light grains (quinoa, millet, buckwheat)",
                "Warming spices (ginger, black pepper, turmeric)",
                "Astringent fruits (apples, pears, berries)",
                "Honey (small amounts)"
            ],
            "reduce": [
                "Heavy, oily, fried foods",
                "Sweet, sour, salty tastes (excess)",
                "Dairy (excess, especially cold)",
                "Wheat, rice (excess)",
                "Red meat",
                "Sweets and sugar",
                "Cold drinks and ice cream",
                "Nuts (excess)"
            ],
            "meal_timing": "Light breakfast, largest meal at lunch, light dinner",
            "portion_size": "Smaller portions, avoid overeating"
        }
    }

    def __init__(self):
        """Initialize calculator."""
        pass

    def calculate_bmr(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str
    ) -> float:
        """
        Calculate Basal Metabolic Rate using Harris-Benedict equation.

        Args:
            weight_kg: Weight in kilograms
            height_cm: Height in centimeters
            age: Age in years
            gender: 'male' or 'female'

        Returns:
            BMR in calories/day
        """
        if gender.lower() in ['male', 'm']:
            # Men: BMR = 88.362 + (13.397 × weight in kg) + (4.799 × height in cm) - (5.677 × age)
            bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        else:
            # Women: BMR = 447.593 + (9.247 × weight in kg) + (3.098 × height in cm) - (4.330 × age)
            bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

        return round(bmr, 1)

    def calculate_tdee(
        self,
        bmr: float,
        activity_level: ActivityLevel
    ) -> float:
        """
        Calculate Total Daily Energy Expenditure.

        Args:
            bmr: Basal Metabolic Rate
            activity_level: Activity level enum

        Returns:
            TDEE in calories/day
        """
        multiplier = self.ACTIVITY_MULTIPLIERS[activity_level]
        tdee = bmr * multiplier
        return round(tdee, 1)

    def adjust_calories_for_goal(
        self,
        tdee: float,
        primary_goal: GoalType,
        urgency: str,
        current_weight_kg: float,
        target_weight_kg: Optional[float]
    ) -> Tuple[float, str]:
        """
        Adjust calories based on goal.

        Args:
            tdee: Total Daily Energy Expenditure
            primary_goal: Primary wellness goal
            urgency: 'gradual', 'balanced', 'aggressive'
            current_weight_kg: Current weight
            target_weight_kg: Target weight (if applicable)

        Returns:
            (adjusted_calories, reasoning)
        """
        adjustments = {
            "gradual": 0.10,    # 10% deficit/surplus
            "balanced": 0.15,   # 15% deficit/surplus
            "aggressive": 0.20  # 20% deficit/surplus
        }

        adjustment = adjustments.get(urgency, 0.15)

        if primary_goal == GoalType.WEIGHT_LOSS:
            # Caloric deficit
            target_calories = tdee * (1 - adjustment)
            reasoning = f"Weight loss: {int(adjustment*100)}% caloric deficit for {urgency} approach"

            # Don't go below 1200 (women) or 1500 (men)
            min_calories = 1200
            if target_calories < min_calories:
                target_calories = min_calories
                reasoning += f" (capped at minimum {min_calories} calories)"

        elif primary_goal == GoalType.MUSCLE_GAIN:
            # Caloric surplus
            target_calories = tdee * (1 + adjustment)
            reasoning = f"Muscle gain: {int(adjustment*100)}% caloric surplus for {urgency} approach"

        elif primary_goal in [GoalType.PHYSICAL_STRENGTH, GoalType.ENDURANCE]:
            # Slight surplus for performance
            target_calories = tdee * 1.05
            reasoning = "Performance optimization: slight caloric surplus (5%)"

        elif primary_goal == GoalType.MENTAL_STRENGTH:
            # Maintenance with focus on brain health
            target_calories = tdee
            reasoning = "Mental clarity: maintenance calories with focus on brain-healthy nutrients"

        elif primary_goal == GoalType.SPIRITUAL_STRENGTH:
            # Slightly lower, cleaner diet
            target_calories = tdee * 0.95
            reasoning = "Spiritual practice: slightly reduced calories for clarity (5% deficit)"

        else:
            # Maintenance
            target_calories = tdee
            reasoning = "Maintenance calories for current weight"

        return round(target_calories, 1), reasoning

    def calculate_macros(
        self,
        target_calories: float,
        primary_goal: GoalType,
        dosha_type: str,
        diet_type: str
    ) -> Tuple[float, float, float, int, int, int, str]:
        """
        Calculate macronutrient distribution.

        Args:
            target_calories: Target daily calories
            primary_goal: Primary wellness goal
            dosha_type: Dominant dosha
            diet_type: Diet type (vegan, vegetarian, etc.)

        Returns:
            (protein_g, carbs_g, fat_g, protein_%, carbs_%, fat_%, reasoning)
        """
        # Base distributions by goal
        if primary_goal == GoalType.MUSCLE_GAIN:
            protein_pct, carbs_pct, fat_pct = 30, 40, 30
            reasoning = "Muscle gain: higher protein and carbs for growth"

        elif primary_goal == GoalType.WEIGHT_LOSS:
            protein_pct, carbs_pct, fat_pct = 35, 35, 30
            reasoning = "Weight loss: higher protein to preserve muscle"

        elif primary_goal == GoalType.ENDURANCE:
            protein_pct, carbs_pct, fat_pct = 20, 55, 25
            reasoning = "Endurance: higher carbs for sustained energy"

        elif primary_goal in [GoalType.MENTAL_STRENGTH, GoalType.SPIRITUAL_STRENGTH]:
            protein_pct, carbs_pct, fat_pct = 25, 45, 30
            reasoning = "Mental/spiritual: balanced with healthy fats for brain"

        else:
            protein_pct, carbs_pct, fat_pct = 25, 45, 30
            reasoning = "Balanced macro distribution"

        # Adjust for dosha
        if "vata" in dosha_type.lower():
            fat_pct += 5
            carbs_pct -= 5
            reasoning += " | Vata: increased healthy fats for grounding"

        elif "pitta" in dosha_type.lower():
            carbs_pct += 5
            protein_pct -= 5
            reasoning += " | Pitta: increased cooling carbs"

        elif "kapha" in dosha_type.lower():
            protein_pct += 5
            fat_pct -= 5
            reasoning += " | Kapha: reduced fats, increased protein"

        # Normalize to 100%
        total = protein_pct + carbs_pct + fat_pct
        protein_pct = round(protein_pct * 100 / total)
        carbs_pct = round(carbs_pct * 100 / total)
        fat_pct = 100 - protein_pct - carbs_pct

        # Calculate grams
        # 1g protein = 4 cal, 1g carbs = 4 cal, 1g fat = 9 cal
        protein_g = round((target_calories * protein_pct / 100) / 4, 1)
        carbs_g = round((target_calories * carbs_pct / 100) / 4, 1)
        fat_g = round((target_calories * fat_pct / 100) / 9, 1)

        return protein_g, carbs_g, fat_g, protein_pct, carbs_pct, fat_pct, reasoning

    def calculate_fiber(
        self,
        target_calories: float,
        age: int,
        gender: str
    ) -> float:
        """
        Calculate daily fiber requirement.

        General recommendation: 14g per 1000 calories
        Men: 30-38g, Women: 21-25g
        """
        fiber_by_calories = (target_calories / 1000) * 14

        if gender.lower() in ['male', 'm']:
            fiber_rda = 38 if age < 50 else 30
        else:
            fiber_rda = 25 if age < 50 else 21

        # Use higher of the two
        return round(max(fiber_by_calories, fiber_rda), 1)

    def calculate_micronutrients(
        self,
        gender: str,
        age: int,
        health_conditions: List[str],
        nutrient_deficiencies: List[str]
    ) -> Dict[str, float]:
        """
        Calculate micronutrient requirements.

        Args:
            gender: 'male' or 'female'
            age: Age in years
            health_conditions: List of health conditions
            nutrient_deficiencies: List of known deficiencies

        Returns:
            Dictionary of micronutrient requirements
        """
        gender_key = "male" if gender.lower() in ['male', 'm'] else "female"
        base_rda = self.MICRONUTRIENT_RDA[gender_key].copy()

        # Age adjustments
        if age > 50:
            base_rda["calcium_mg"] = 1200
            base_rda["vitamin_d_mcg"] = 20
            base_rda["b12_mcg"] = 2.4  # Better absorption needed

        if age > 70:
            base_rda["vitamin_d_mcg"] = 20

        # Condition adjustments
        if "osteoporosis" in health_conditions or "bone" in str(health_conditions).lower():
            base_rda["calcium_mg"] = 1500
            base_rda["vitamin_d_mcg"] = 25
            base_rda["magnesium_mg"] += 100
            base_rda["vitamin_k_mcg"] += 50

        if "anemia" in health_conditions or "iron" in nutrient_deficiencies:
            base_rda["iron_mg"] *= 1.5
            base_rda["b12_mcg"] *= 1.5
            base_rda["folate_mcg"] *= 1.5

        if "immune" in str(health_conditions).lower():
            base_rda["vitamin_c_mg"] *= 1.5
            base_rda["vitamin_d_mcg"] *= 1.5
            base_rda["zinc_mg"] *= 1.3

        # Deficiency adjustments
        for deficiency in nutrient_deficiencies:
            deficiency_lower = deficiency.lower().replace(" ", "_")

            if "vitamin_d" in deficiency_lower:
                base_rda["vitamin_d_mcg"] = 50
            elif "iron" in deficiency_lower:
                base_rda["iron_mg"] *= 2
            elif "b12" in deficiency_lower or "b_12" in deficiency_lower:
                base_rda["b12_mcg"] *= 2
            elif "magnesium" in deficiency_lower:
                base_rda["magnesium_mg"] *= 1.5

        return base_rda

    def calculate_hydration(
        self,
        weight_kg: float,
        activity_level: ActivityLevel,
        climate: str = "moderate"
    ) -> int:
        """
        Calculate daily water requirement.

        Base formula: 30-35 ml per kg body weight
        Adjustments for activity and climate
        """
        # Base: 35 ml/kg
        base_ml = weight_kg * 35

        # Activity adjustment
        activity_bonus = {
            ActivityLevel.SEDENTARY: 0,
            ActivityLevel.LIGHT: 250,
            ActivityLevel.MODERATE: 500,
            ActivityLevel.VERY_ACTIVE: 750,
            ActivityLevel.EXTREMELY_ACTIVE: 1000,
        }
        base_ml += activity_bonus[activity_level]

        # Climate adjustment
        if climate.lower() in ["hot", "tropical"]:
            base_ml *= 1.2
        elif climate.lower() in ["very_hot", "desert"]:
            base_ml *= 1.4

        return round(base_ml / 250) * 250  # Round to nearest 250ml

    def get_dosha_guidelines(
        self,
        dosha_type: str,
        dosha_percentages: Dict[str, int]
    ) -> Dict[str, List[str]]:
        """
        Get Ayurvedic dietary guidelines based on dosha.

        Args:
            dosha_type: Primary dosha type
            dosha_percentages: Percentages of each dosha

        Returns:
            Combined dietary guidelines
        """
        # Primary dosha
        primary_dosha = dosha_type.lower().split("-")[0]  # Handle "vata-pitta" etc.

        guidelines = {
            "favor": [],
            "reduce": [],
            "meal_timing": "",
            "portion_guidance": ""
        }

        # Get primary dosha guidelines
        if primary_dosha in self.DOSHA_GUIDELINES:
            primary_guide = self.DOSHA_GUIDELINES[primary_dosha]
            guidelines["favor"] = primary_guide["favor"].copy()
            guidelines["reduce"] = primary_guide["reduce"].copy()
            guidelines["meal_timing"] = primary_guide["meal_timing"]
            guidelines["portion_guidance"] = primary_guide["portion_size"]

        # If dual dosha, blend recommendations
        if "-" in dosha_type.lower():
            secondary_dosha = dosha_type.lower().split("-")[1]
            if secondary_dosha in self.DOSHA_GUIDELINES:
                secondary_guide = self.DOSHA_GUIDELINES[secondary_dosha]

                # Add unique items from secondary dosha
                for item in secondary_guide["favor"]:
                    if item not in guidelines["favor"]:
                        guidelines["favor"].append(item)

                guidelines["meal_timing"] += f" | Also: {secondary_guide['meal_timing']}"

        return guidelines

    def determine_meal_frequency(
        self,
        dosha_type: str,
        primary_goal: GoalType,
        intermittent_fasting: bool,
        fasting_window: Optional[str]
    ) -> Tuple[int, Optional[int], str]:
        """
        Determine optimal meal frequency.

        Returns:
            (meals_per_day, eating_window_hours, largest_meal_time)
        """
        # Intermittent fasting
        if intermittent_fasting and fasting_window:
            if fasting_window == "16:8":
                eating_window = 8
                meals = 2
            elif fasting_window == "18:6":
                eating_window = 6
                meals = 2
            elif fasting_window == "20:4":
                eating_window = 4
                meals = 1
            else:
                eating_window = 8
                meals = 2
        else:
            eating_window = None

            # Base on dosha and goal
            if "vata" in dosha_type.lower():
                meals = 3  # Vata needs regular meals
            elif "pitta" in dosha_type.lower():
                meals = 3  # Pitta has strong digestion
            elif "kapha" in dosha_type.lower():
                meals = 2  # Kapha benefits from less frequent eating
            else:
                meals = 3

            # Adjust for goals
            if primary_goal == GoalType.MUSCLE_GAIN:
                meals = 4  # More frequent for muscle building
            elif primary_goal == GoalType.WEIGHT_LOSS and "kapha" in dosha_type.lower():
                meals = 2  # Less frequent for Kapha weight loss

        # Largest meal timing (Ayurvedic principle: Agni strongest at noon)
        largest_meal = "lunch"

        return meals, eating_window, largest_meal

    def calculate_complete_requirements(
        self,
        profile: ComprehensiveUserProfile
    ) -> DailyNutritionRequirements:
        """
        Calculate complete nutritional requirements from user profile.

        Args:
            profile: Complete user profile

        Returns:
            Complete daily nutrition requirements
        """
        notes = []

        # 1. Calculate BMR
        bmr = self.calculate_bmr(
            profile.physical.weight_kg,
            profile.physical.height_cm,
            profile.physical.age,
            profile.physical.gender
        )
        notes.append(f"BMR calculated using Harris-Benedict: {bmr} cal/day")

        # 2. Calculate TDEE
        tdee = self.calculate_tdee(bmr, profile.physical.activity_level)
        notes.append(f"TDEE with {profile.physical.activity_level.value} activity: {tdee} cal/day")

        # 3. Adjust for goals
        target_calories, goal_reasoning = self.adjust_calories_for_goal(
            tdee,
            profile.goals.primary_goal,
            profile.goals.urgency,
            profile.physical.weight_kg,
            profile.goals.target_weight_kg
        )
        notes.append(goal_reasoning)

        # 4. Calculate macros
        protein_g, carbs_g, fat_g, protein_pct, carbs_pct, fat_pct, macro_reasoning = self.calculate_macros(
            target_calories,
            profile.goals.primary_goal,
            profile.personality.dosha_type,
            profile.dietary_preferences.diet_type.value
        )
        notes.append(macro_reasoning)

        # 5. Calculate fiber
        fiber_g = self.calculate_fiber(
            target_calories,
            profile.physical.age,
            profile.physical.gender
        )

        # 6. Calculate micronutrients
        micros = self.calculate_micronutrients(
            profile.physical.gender,
            profile.physical.age,
            profile.health.conditions,
            profile.health.nutrient_deficiencies
        )

        # 7. Calculate hydration
        water_ml = self.calculate_hydration(
            profile.physical.weight_kg,
            profile.physical.activity_level
        )
        notes.append(f"Hydration: {water_ml}ml based on {profile.physical.weight_kg}kg body weight")

        # 8. Get dosha guidelines
        dosha_guidelines = self.get_dosha_guidelines(
            profile.personality.dosha_type,
            profile.personality.dosha_percentages
        )

        # 9. Determine meal frequency
        meal_freq, eating_window, largest_meal = self.determine_meal_frequency(
            profile.personality.dosha_type,
            profile.goals.primary_goal,
            profile.custom_preferences.intermittent_fasting,
            profile.custom_preferences.fasting_window
        )

        # Extract B-complex vitamins
        b_complex = {
            "b1_thiamin_mg": micros.pop("b1_thiamin_mg"),
            "b2_riboflavin_mg": micros.pop("b2_riboflavin_mg"),
            "b3_niacin_mg": micros.pop("b3_niacin_mg"),
            "b6_mg": micros.pop("b6_mg"),
            "b12_mcg": micros.pop("b12_mcg"),
            "folate_mcg": micros.pop("folate_mcg"),
        }

        return DailyNutritionRequirements(
            bmr=bmr,
            tdee=tdee,
            target_calories=target_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
            protein_percent=protein_pct,
            carbs_percent=carbs_pct,
            fat_percent=fat_pct,
            vitamin_a_mcg=micros["vitamin_a_mcg"],
            vitamin_c_mg=micros["vitamin_c_mg"],
            vitamin_d_mcg=micros["vitamin_d_mcg"],
            vitamin_e_mg=micros["vitamin_e_mg"],
            vitamin_k_mcg=micros["vitamin_k_mcg"],
            b_complex=b_complex,
            calcium_mg=micros["calcium_mg"],
            iron_mg=micros["iron_mg"],
            magnesium_mg=micros["magnesium_mg"],
            potassium_mg=micros["potassium_mg"],
            zinc_mg=micros["zinc_mg"],
            selenium_mcg=micros["selenium_mcg"],
            water_ml=water_ml,
            dosha_dietary_guidelines=dosha_guidelines,
            foods_to_favor=dosha_guidelines["favor"],
            foods_to_reduce=dosha_guidelines["reduce"],
            meal_frequency=meal_freq,
            eating_window_hours=eating_window,
            largest_meal_time=largest_meal,
            calculation_notes=notes
        )


# Singleton instance
_nutritional_calculator = None


def get_nutritional_calculator() -> NutritionalCalculator:
    """Get singleton nutritional calculator."""
    global _nutritional_calculator
    if _nutritional_calculator is None:
        _nutritional_calculator = NutritionalCalculator()
    return _nutritional_calculator


# Example usage
if __name__ == "__main__":
    from datetime import date, time as dt_time

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
            chronotype="early_bird",
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
        health=HealthProfile(
            conditions=[],
            allergies=["peanuts"],
            medications=[],
            nutrient_deficiencies=["vitamin_d"],
            digestive_issues=[],
            family_history=[]
        ),
        dietary_preferences=DietaryPreferences(
            diet_type="vegetarian",
            cuisine_preferences=["indian", "mediterranean"],
            disliked_foods=["mushrooms"],
            favorite_foods=["dal", "quinoa"],
            budget_per_week=100,
            budget_currency="USD",
            cooking_skill="intermediate",
            cooking_time_available=45,
            meal_prep_preference="daily",
            eating_out_frequency=2
        ),
        lifestyle=LifestyleProfile(
            region="Mumbai, Maharashtra, India",
            country_code="IN",
            timezone="Asia/Kolkata",
            occupation="Software Engineer",
            work_schedule_type="remote",
            typical_work_hours="9:00-18:00",
            work_break_preferences=["lunch"],
            commute_time_minutes=0,
            household_size=1,
            has_family_meals=False
        ),
        sleep_preferences=SleepPreferences(
            ideal_sleep_duration=7.5,
            preferred_bedtime=dt_time(23, 0),
            preferred_wake_time=dt_time(6, 30),
            current_sleep_quality=7,
            sleep_issues=[]
        ),
        goals=WellnessGoals(
            primary_goal=GoalType.PHYSICAL_STRENGTH,
            secondary_goals=[GoalType.MENTAL_STRENGTH],
            timeline="3_months",
            urgency="balanced",
            target_weight_kg=None,
            meditation_minutes_daily=20,
            exercise_minutes_daily=45
        ),
        custom_preferences=CustomPreferences(
            intermittent_fasting=False,
            fasting_window=None,
            caffeine_preference="moderate",
            alcohol_consumption="occasional",
            supplement_stack=["vitamin_d", "omega_3"],
            exercise_preferences=["yoga", "weights"],
            spiritual_practices=["meditation"],
            notes=""
        )
    )

    calculator = get_nutritional_calculator()
    requirements = calculator.calculate_complete_requirements(profile)

    print("=== DAILY NUTRITION REQUIREMENTS ===\n")
    print(f"BMR: {requirements.bmr} cal/day")
    print(f"TDEE: {requirements.tdee} cal/day")
    print(f"Target Calories: {requirements.target_calories} cal/day\n")

    print(f"MACROS:")
    print(f"  Protein: {requirements.protein_g}g ({requirements.protein_percent}%)")
    print(f"  Carbs: {requirements.carbs_g}g ({requirements.carbs_percent}%)")
    print(f"  Fat: {requirements.fat_g}g ({requirements.fat_percent}%)")
    print(f"  Fiber: {requirements.fiber_g}g\n")

    print(f"HYDRATION: {requirements.water_ml}ml\n")

    print(f"MEAL FREQUENCY: {requirements.meal_frequency} meals/day")
    print(f"Largest meal: {requirements.largest_meal_time}\n")

    print(f"DOSHA GUIDELINES (Pitta-Vata):")
    print(f"  Favor: {', '.join(requirements.foods_to_favor[:5])}...")
    print(f"  Reduce: {', '.join(requirements.foods_to_reduce[:5])}...\n")

    print(f"CALCULATION NOTES:")
    for note in requirements.calculation_notes:
        print(f"  - {note}")
