"""
Meal Plan Optimization Engine.

Generates optimal meal plans using constraint-based optimization:
- Nutritional requirements (macros, micros)
- Budget constraints
- Dosha balance (Ayurvedic)
- Food preferences and allergies
- Cooking time available
- Variety requirements
- Cultural/cuisine preferences
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, time as dt_time, datetime
import random
from dataclasses import dataclass
from copy import deepcopy

from backend.models.life_optimization_models import (
    ComprehensiveUserProfile,
    Meal,
    DailyMealPlan,
    WeeklyMealPlan,
    FoodIngredient,
    NutrientInfo,
    AyurvedicProperties as MealAyurvedicProperties
)
from backend.services.nutritional_calculator import (
    get_nutritional_calculator,
    DailyNutritionRequirements
)
from backend.services.global_food_database import (
    get_food_database,
    FoodItem,
    FoodCategory
)
from backend.services.currency_location_service import (
    get_currency_service,
    LocationInfo
)


@dataclass
class MealConstraints:
    """Constraints for meal generation."""
    # Nutritional
    min_calories: float
    max_calories: float
    min_protein_g: float
    max_protein_g: float
    min_carbs_g: float
    max_carbs_g: float
    min_fat_g: float
    max_fat_g: float

    # Budget
    max_cost_usd: float

    # Time
    max_prep_time_minutes: int

    # Dosha
    dosha_to_balance: str
    dosha_priority: float  # 0-1, how important is dosha balance

    # Preferences
    required_dietary_flags: List[str]
    excluded_allergens: List[str]
    excluded_foods: List[str]
    preferred_cuisines: List[str]

    # Meal type specific
    meal_type: str  # breakfast, lunch, dinner, snack
    time_of_day: dt_time


class MealPlanOptimizer:
    """Optimize meal plans based on constraints."""

    # Meal type characteristics
    MEAL_CHARACTERISTICS = {
        "breakfast": {
            "calorie_pct": 0.25,  # 25% of daily calories
            "protein_pct": 0.20,
            "emphasis": "light_easy_digest",
            "ayurvedic_timing": "6:30-9:00",
            "cooking_methods": ["boiled", "steamed", "raw", "blended"]
        },
        "lunch": {
            "calorie_pct": 0.40,  # 40% of daily calories (Agni strongest)
            "protein_pct": 0.40,
            "emphasis": "nourishing_complete",
            "ayurvedic_timing": "12:00-13:30",
            "cooking_methods": ["steamed", "sautéed", "roasted", "curry"]
        },
        "dinner": {
            "calorie_pct": 0.25,  # 25% of daily calories
            "protein_pct": 0.30,
            "emphasis": "light_digestible",
            "ayurvedic_timing": "18:00-20:00",
            "cooking_methods": ["steamed", "soup", "sautéed", "baked"]
        },
        "snack": {
            "calorie_pct": 0.10,  # 10% of daily calories
            "protein_pct": 0.10,
            "emphasis": "light_quick",
            "ayurvedic_timing": "flexible",
            "cooking_methods": ["raw", "blended", "roasted"]
        }
    }

    # Cooking time estimates by method (minutes)
    COOKING_TIMES = {
        "raw": 5,
        "blended": 10,
        "steamed": 20,
        "boiled": 25,
        "sautéed": 20,
        "stir_fried": 15,
        "roasted": 35,
        "baked": 40,
        "curry": 35,
        "soup": 30,
        "grilled": 25,
    }

    def __init__(self):
        """Initialize optimizer."""
        self.nutritional_calc = get_nutritional_calculator()
        self.food_db = get_food_database()
        self.currency_service = get_currency_service()

    def generate_daily_meal_plan(
        self,
        profile: ComprehensiveUserProfile,
        target_date: date,
        location: LocationInfo
    ) -> DailyMealPlan:
        """
        Generate optimized daily meal plan.

        Args:
            profile: User profile
            target_date: Date for meal plan
            location: User location for pricing

        Returns:
            Optimized daily meal plan
        """
        # 1. Calculate nutritional requirements
        nutrition_req = self.nutritional_calc.calculate_complete_requirements(profile)

        # 2. Determine meal structure
        meal_structure = self._determine_meal_structure(nutrition_req, profile)

        # 3. Generate meals
        meals = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        total_cost = 0

        for meal_info in meal_structure:
            meal = self._generate_meal(
                meal_info["type"],
                meal_info["time"],
                meal_info["calorie_target"],
                meal_info["macro_targets"],
                profile,
                nutrition_req,
                location
            )

            if meal:
                meals.append(meal)
                total_calories += meal.total_nutrients.calories
                total_protein += meal.total_nutrients.protein_g
                total_carbs += meal.total_nutrients.carbs_g
                total_fat += meal.total_nutrients.fat_g
                total_fiber += meal.total_nutrients.fiber_g
                total_cost += meal.cost_total

        # 4. Generate hydration schedule
        hydration_schedule = self._generate_hydration_schedule(
            nutrition_req.water_ml,
            profile.sleep_preferences.preferred_wake_time,
            profile.sleep_preferences.preferred_bedtime
        )

        # 5. Calculate dosha balance score
        dosha_score = self._calculate_dosha_balance_score(meals, profile.personality.dosha_type)

        # 6. Check compliance
        meets_goals = self._check_nutritional_compliance(
            total_calories, total_protein, total_carbs, total_fat,
            nutrition_req
        )

        budget_usd = self.currency_service.convert_currency(
            profile.dietary_preferences.budget_per_week,
            profile.dietary_preferences.budget_currency,
            "USD"
        )
        daily_budget = budget_usd / 7
        meets_budget = total_cost <= daily_budget

        nutrient_gaps = self._identify_nutrient_gaps(
            total_calories, total_protein, total_carbs, total_fat, total_fiber,
            nutrition_req
        )

        return DailyMealPlan(
            date=target_date,
            user_id=profile.user_id,
            meals=meals,
            total_calories=round(total_calories, 1),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fat=round(total_fat, 1),
            total_fiber=round(total_fiber, 1),
            total_cost=round(total_cost, 2),
            cost_currency="USD",
            water_ml=nutrition_req.water_ml,
            hydration_schedule=hydration_schedule,
            dosha_balance_score=dosha_score,
            meets_goals=meets_goals,
            meets_budget=meets_budget,
            nutrient_gaps=nutrient_gaps
        )

    def _determine_meal_structure(
        self,
        nutrition_req: DailyNutritionRequirements,
        profile: ComprehensiveUserProfile
    ) -> List[Dict]:
        """Determine meal times and calorie distribution."""
        meal_structure = []

        num_meals = nutrition_req.meal_frequency
        largest_meal = nutrition_req.largest_meal_time

        if num_meals == 2:
            # Intermittent fasting: brunch + dinner
            meal_structure = [
                {
                    "type": "brunch",
                    "time": dt_time(11, 0),
                    "calorie_target": nutrition_req.target_calories * 0.50,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * 0.45,
                        "carbs": nutrition_req.carbs_g * 0.50,
                        "fat": nutrition_req.fat_g * 0.50
                    }
                },
                {
                    "type": "dinner",
                    "time": dt_time(18, 30),
                    "calorie_target": nutrition_req.target_calories * 0.50,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * 0.55,
                        "carbs": nutrition_req.carbs_g * 0.50,
                        "fat": nutrition_req.fat_g * 0.50
                    }
                }
            ]

        elif num_meals == 3:
            # Standard 3 meals
            if largest_meal == "lunch":
                # Ayurvedic: biggest meal at lunch
                breakfast_pct, lunch_pct, dinner_pct = 0.25, 0.50, 0.25
            else:
                # Western: even distribution
                breakfast_pct, lunch_pct, dinner_pct = 0.30, 0.40, 0.30

            meal_structure = [
                {
                    "type": "breakfast",
                    "time": profile.sleep_preferences.preferred_wake_time or dt_time(7, 0),
                    "calorie_target": nutrition_req.target_calories * breakfast_pct,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * (breakfast_pct * 0.9),
                        "carbs": nutrition_req.carbs_g * breakfast_pct,
                        "fat": nutrition_req.fat_g * breakfast_pct
                    }
                },
                {
                    "type": "lunch",
                    "time": dt_time(12, 30),
                    "calorie_target": nutrition_req.target_calories * lunch_pct,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * (lunch_pct * 1.1),
                        "carbs": nutrition_req.carbs_g * lunch_pct,
                        "fat": nutrition_req.fat_g * lunch_pct
                    }
                },
                {
                    "type": "dinner",
                    "time": dt_time(19, 0),
                    "calorie_target": nutrition_req.target_calories * dinner_pct,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * dinner_pct,
                        "carbs": nutrition_req.carbs_g * (dinner_pct * 0.9),
                        "fat": nutrition_req.fat_g * dinner_pct
                    }
                }
            ]

        elif num_meals == 4:
            # 3 meals + snack
            meal_structure = [
                {
                    "type": "breakfast",
                    "time": dt_time(7, 0),
                    "calorie_target": nutrition_req.target_calories * 0.25,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * 0.20,
                        "carbs": nutrition_req.carbs_g * 0.25,
                        "fat": nutrition_req.fat_g * 0.25
                    }
                },
                {
                    "type": "lunch",
                    "time": dt_time(12, 30),
                    "calorie_target": nutrition_req.target_calories * 0.35,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * 0.35,
                        "carbs": nutrition_req.carbs_g * 0.35,
                        "fat": nutrition_req.fat_g * 0.30
                    }
                },
                {
                    "type": "snack",
                    "time": dt_time(16, 0),
                    "calorie_target": nutrition_req.target_calories * 0.15,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * 0.20,
                        "carbs": nutrition_req.carbs_g * 0.15,
                        "fat": nutrition_req.fat_g * 0.20
                    }
                },
                {
                    "type": "dinner",
                    "time": dt_time(19, 0),
                    "calorie_target": nutrition_req.target_calories * 0.25,
                    "macro_targets": {
                        "protein": nutrition_req.protein_g * 0.25,
                        "carbs": nutrition_req.carbs_g * 0.25,
                        "fat": nutrition_req.fat_g * 0.25
                    }
                }
            ]

        return meal_structure

    def _generate_meal(
        self,
        meal_type: str,
        meal_time: dt_time,
        calorie_target: float,
        macro_targets: Dict[str, float],
        profile: ComprehensiveUserProfile,
        nutrition_req: DailyNutritionRequirements,
        location: LocationInfo
    ) -> Optional[Meal]:
        """Generate a single meal."""

        # Get suitable foods
        suitable_foods = self._get_suitable_foods(profile, nutrition_req, meal_type)

        if not suitable_foods:
            return None

        # Build meal iteratively
        ingredients = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_cost = 0
        cooking_time = 0

        # Calorie tolerance
        cal_min = calorie_target * 0.85
        cal_max = calorie_target * 1.15

        # Select base (grain or legume)
        base_foods = [f for f in suitable_foods if f.category in [FoodCategory.GRAINS, FoodCategory.LEGUMES]]
        if base_foods:
            base_food = random.choice(base_foods)
            base_qty = self._calculate_quantity(
                base_food,
                calorie_target * 0.35  # Base provides 35% calories
            )

            ingredient, cost = self._create_ingredient(base_food, base_qty, location)
            ingredients.append(ingredient)
            total_calories += ingredient.calories
            total_protein += ingredient.protein_g
            total_carbs += ingredient.carbs_g
            total_fat += ingredient.fat_g
            total_cost += cost

        # Add vegetables (2-3)
        veg_foods = [f for f in suitable_foods if f.category == FoodCategory.VEGETABLES]
        if veg_foods:
            num_veggies = min(2, len(veg_foods))
            selected_veggies = random.sample(veg_foods, num_veggies)

            for veg in selected_veggies:
                veg_qty = self._calculate_quantity(veg, calorie_target * 0.15)
                ingredient, cost = self._create_ingredient(veg, veg_qty, location)
                ingredients.append(ingredient)
                total_calories += ingredient.calories
                total_protein += ingredient.protein_g
                total_carbs += ingredient.carbs_g
                total_fat += ingredient.fat_g
                total_cost += cost

        # Add protein (if needed)
        protein_gap = macro_targets["protein"] - total_protein
        if protein_gap > 5:  # Need more protein
            protein_foods = [f for f in suitable_foods
                             if f.nutrition.protein_g > 15 and f.category != FoodCategory.GRAINS]
            if protein_foods:
                protein_food = random.choice(protein_foods)
                protein_qty = (protein_gap / protein_food.nutrition.protein_g) * 100
                ingredient, cost = self._create_ingredient(protein_food, protein_qty, location)
                ingredients.append(ingredient)
                total_calories += ingredient.calories
                total_protein += ingredient.protein_g
                total_carbs += ingredient.carbs_g
                total_fat += ingredient.fat_g
                total_cost += cost

        # Add healthy fat (if needed)
        fat_gap = macro_targets["fat"] - total_fat
        if fat_gap > 3:
            fat_foods = [f for f in suitable_foods if f.category in [FoodCategory.OILS_FATS, FoodCategory.NUTS_SEEDS]]
            if fat_foods:
                fat_food = random.choice(fat_foods)
                fat_qty = min(30, (fat_gap / fat_food.nutrition.fat_g) * 100)  # Max 30g of pure fat
                ingredient, cost = self._create_ingredient(fat_food, fat_qty, location)
                ingredients.append(ingredient)
                total_calories += ingredient.calories
                total_protein += ingredient.protein_g
                total_carbs += ingredient.carbs_g
                total_fat += ingredient.fat_g
                total_cost += cost

        # Add spices (flavor, no significant nutrition)
        spice_foods = [f for f in suitable_foods if f.category == FoodCategory.SPICES]
        if spice_foods:
            spices = random.sample(spice_foods, min(2, len(spice_foods)))
            for spice in spices:
                ingredient, cost = self._create_ingredient(spice, 2, location)  # 2g spice
                ingredients.append(ingredient)
                total_cost += cost

        # Determine cooking method
        cooking_method = random.choice(self.MEAL_CHARACTERISTICS.get(meal_type, {}).get("cooking_methods", ["steamed"]))
        cooking_time = self.COOKING_TIMES.get(cooking_method, 20)

        # Generate cooking instructions
        instructions = self._generate_cooking_instructions(ingredients, cooking_method)

        # Calculate Ayurvedic properties
        ayurvedic_props = self._calculate_meal_ayurvedic_properties(ingredients, suitable_foods)

        # Determine timing reason
        timing_reason = self._get_timing_reason(meal_type, meal_time, profile.personality.dosha_type)

        # Create meal name
        meal_name = self._generate_meal_name(ingredients, meal_type)

        return Meal(
            meal_id=f"{profile.user_id}_{datetime.now().timestamp()}",
            day=date.today().strftime("%A").lower(),
            meal_type=meal_type,
            time=meal_time,
            name=meal_name,
            description=f"{meal_type.capitalize()} optimized for {profile.personality.dosha_type}",
            ingredients=ingredients,
            cooking_instructions=instructions,
            prep_time_minutes=cooking_time,
            cooking_method=cooking_method,
            total_nutrients=NutrientInfo(
                calories=round(total_calories, 1),
                protein_g=round(total_protein, 1),
                carbs_g=round(total_carbs, 1),
                fat_g=round(total_fat, 1),
                fiber_g=round(sum([i.fiber_g for i in ingredients if hasattr(i, 'fiber_g')]), 1)
            ),
            ayurvedic_properties=ayurvedic_props,
            cost_total=round(total_cost, 2),
            cost_currency="USD",
            suitable_for=profile.dietary_preferences.diet_type.value.split(","),
            avoid_if=profile.health.allergies,
            timing_reason=timing_reason
        )

    def _get_suitable_foods(
        self,
        profile: ComprehensiveUserProfile,
        nutrition_req: DailyNutritionRequirements,
        meal_type: str
    ) -> List[FoodItem]:
        """Get foods suitable for user."""
        suitable = []

        for food in self.food_db.foods.values():
            # Check dietary restrictions
            diet_type = profile.dietary_preferences.diet_type.value
            if diet_type == "vegan" and "vegan" not in food.dietary_flags:
                continue
            if diet_type == "vegetarian" and "vegetarian" not in food.dietary_flags:
                continue

            # Check allergens
            if any(allergen in food.allergens for allergen in profile.health.allergies):
                continue

            # Check disliked foods
            if food.name.lower() in [f.lower() for f in profile.dietary_preferences.disliked_foods]:
                continue

            # Check cuisine preferences (if specified)
            if profile.dietary_preferences.cuisine_preferences:
                if not any(cuisine in food.cuisines for cuisine in profile.dietary_preferences.cuisine_preferences):
                    # Allow global foods
                    if "global" not in food.cuisines:
                        continue

            suitable.append(food)

        return suitable

    def _calculate_quantity(self, food: FoodItem, target_calories: float) -> float:
        """Calculate quantity in grams to meet calorie target."""
        if food.nutrition.calories == 0:
            return 10  # Default for spices/zero-cal items

        quantity_g = (target_calories / food.nutrition.calories) * 100
        return round(quantity_g, 1)

    def _create_ingredient(
        self,
        food: FoodItem,
        quantity_g: float,
        location: LocationInfo
    ) -> Tuple[FoodIngredient, float]:
        """Create ingredient with calculated nutrition and cost."""

        # Scale nutrition to quantity
        scale_factor = quantity_g / 100

        calories = food.nutrition.calories * scale_factor
        protein = food.nutrition.protein_g * scale_factor
        carbs = food.nutrition.carbs_g * scale_factor
        fat = food.nutrition.fat_g * scale_factor

        # Calculate cost
        quantity_kg = quantity_g / 1000
        regional_price = self.food_db.get_regional_price(
            food.food_id,
            location.country_code,
            location.region
        )

        if regional_price:
            cost_usd = regional_price.price_per_kg * quantity_kg
        else:
            cost_usd = food.base_price_usd_per_kg * quantity_kg

        # Determine unit
        if quantity_g < 10:
            unit = "g"
            display_qty = quantity_g
        elif quantity_g < 1000:
            unit = "g"
            display_qty = round(quantity_g)
        else:
            unit = "kg"
            display_qty = round(quantity_g / 1000, 2)

        # Reason for ingredient
        reason = self._get_ingredient_reason(food)

        ingredient = FoodIngredient(
            name=food.name,
            quantity=display_qty,
            unit=unit,
            calories=round(calories, 1),
            protein_g=round(protein, 1),
            carbs_g=round(carbs, 1),
            fat_g=round(fat, 1),
            cost_local=cost_usd,
            cost_currency="USD",
            reason=reason,
            alternatives=[]
        )

        return ingredient, cost_usd

    def _get_ingredient_reason(self, food: FoodItem) -> str:
        """Get reason for including ingredient."""
        reasons = []

        # Nutritional highlights
        if food.nutrition.protein_g > 15:
            reasons.append("high protein")
        if food.nutrition.fiber_g > 5:
            reasons.append("high fiber")

        # Ayurvedic
        dosha_effects = []
        for dosha, effect in food.ayurvedic.dosha_effect.items():
            if effect == "decrease":
                dosha_effects.append(f"balances {dosha}")

        if dosha_effects:
            reasons.append(", ".join(dosha_effects[:2]))

        # Micronutrients
        if food.nutrition.iron_mg and food.nutrition.iron_mg > 3:
            reasons.append("iron-rich")
        if food.nutrition.vitamin_c_mg and food.nutrition.vitamin_c_mg > 20:
            reasons.append("vitamin C")

        return "; ".join(reasons) if reasons else "nutritious"

    def _generate_cooking_instructions(self, ingredients: List[FoodIngredient], method: str) -> List[str]:
        """Generate simple cooking instructions."""
        instructions = []

        if method == "steamed":
            instructions = [
                f"Rinse {ingredients[0].name}",
                "Add to steamer with water",
                "Steam for 15-20 minutes until tender",
                "Add vegetables in last 5 minutes" if len(ingredients) > 1 else "Season with spices",
                "Serve hot"
            ]
        elif method == "curry":
            instructions = [
                "Heat oil in pan",
                "Add spices and sauté for 1 minute",
                f"Add {ingredients[0].name} and cook 5 minutes",
                "Add vegetables and water/stock",
                "Simmer for 20-25 minutes",
                "Adjust seasoning and serve"
            ]
        elif method == "raw":
            instructions = [
                "Wash all ingredients thoroughly",
                "Chop or prepare as needed",
                "Combine in bowl",
                "Add any dressing or toppings",
                "Serve fresh"
            ]
        elif method == "soup":
            instructions = [
                "Heat oil in pot",
                "Sauté aromatics for 2 minutes",
                "Add main ingredients",
                "Add water/stock to cover",
                "Simmer 25-30 minutes",
                "Blend if desired, season and serve"
            ]
        else:
            instructions = [
                "Prepare all ingredients",
                f"{method.capitalize()} according to standard method",
                "Cook until tender",
                "Season to taste",
                "Serve warm"
            ]

        return instructions

    def _calculate_meal_ayurvedic_properties(
        self,
        ingredients: List[FoodIngredient],
        all_foods: List[FoodItem]
    ) -> MealAyurvedicProperties:
        """Calculate combined Ayurvedic properties of meal."""

        # Find foods by name
        food_map = {f.name: f for f in all_foods}

        all_rasas = []
        heating_count = 0
        cooling_count = 0
        dosha_effects = {"vata": 0, "pitta": 0, "kapha": 0}

        for ingredient in ingredients:
            food = food_map.get(ingredient.name)
            if food:
                all_rasas.extend(food.ayurvedic.rasa)

                if food.ayurvedic.virya == "heating":
                    heating_count += 1
                elif food.ayurvedic.virya == "cooling":
                    cooling_count += 1

                for dosha, effect in food.ayurvedic.dosha_effect.items():
                    if effect == "increase":
                        dosha_effects[dosha] += 1
                    elif effect == "decrease":
                        dosha_effects[dosha] -= 1

        # Determine overall virya
        if heating_count > cooling_count:
            overall_virya = "heating"
        elif cooling_count > heating_count:
            overall_virya = "cooling"
        else:
            overall_virya = "neutral"

        # Determine dosha effect
        dosha_effect_str = ", ".join([
            f"{dosha}: {'increase' if effect > 0 else 'decrease' if effect < 0 else 'neutral'}"
            for dosha, effect in dosha_effects.items()
        ])

        # Get unique rasas
        unique_rasas = list(set(all_rasas))

        return MealAyurvedicProperties(
            rasa=unique_rasas[:3],  # Top 3 tastes
            virya=overall_virya,
            vipaka="sweet",  # Simplified
            dosha_effect=dosha_effect_str,
            qualities=["nourishing", "balanced"]
        )

    def _get_timing_reason(self, meal_type: str, meal_time: dt_time, dosha: str) -> str:
        """Get reason for meal timing."""
        reasons = []

        if meal_type == "breakfast":
            reasons.append("Vata time (6-10am) - light, grounding breakfast")
        elif meal_type == "lunch":
            reasons.append("Pitta time (10am-2pm) - Agni strongest, largest meal")
        elif meal_type == "dinner":
            reasons.append("Kapha time (6-10pm) - light, easy to digest")

        if "vata" in dosha.lower():
            reasons.append("warm, moist foods for Vata")
        elif "pitta" in dosha.lower():
            reasons.append("cooling foods for Pitta")
        elif "kapha" in dosha.lower():
            reasons.append("light, stimulating foods for Kapha")

        return " | ".join(reasons)

    def _generate_meal_name(self, ingredients: List[FoodIngredient], meal_type: str) -> str:
        """Generate descriptive meal name."""
        # Get main ingredients (not spices)
        main_ingredients = [i.name for i in ingredients if i.quantity > 10][:3]

        if len(main_ingredients) >= 2:
            return f"{main_ingredients[0]} with {main_ingredients[1]}"
        elif len(main_ingredients) == 1:
            return f"{main_ingredients[0]} {meal_type.capitalize()}"
        else:
            return f"Balanced {meal_type.capitalize()}"

    def _generate_hydration_schedule(
        self,
        total_ml: int,
        wake_time: dt_time,
        bed_time: dt_time
    ) -> List[Dict]:
        """Generate hydration schedule throughout the day."""
        schedule = []

        # Morning (wake up)
        schedule.append({
            "time": wake_time.strftime("%H:%M"),
            "quantity_ml": 500,
            "note": "Warm water with lemon - cleansing"
        })

        # Mid-morning
        morning_time = dt_time(wake_time.hour + 2, 0)
        schedule.append({
            "time": morning_time.strftime("%H:%M"),
            "quantity_ml": 250,
            "note": "Hydration"
        })

        # Pre-lunch
        schedule.append({
            "time": "12:00",
            "quantity_ml": 250,
            "note": "30 min before lunch"
        })

        # Afternoon
        schedule.append({
            "time": "15:00",
            "quantity_ml": 250,
            "note": "Afternoon hydration"
        })

        # Evening
        schedule.append({
            "time": "17:30",
            "quantity_ml": 250,
            "note": "Pre-dinner"
        })

        # Before bed (if time allows)
        if bed_time.hour > 20:
            schedule.append({
                "time": f"{bed_time.hour - 1}:00",
                "quantity_ml": 200,
                "note": "Light hydration before bed"
            })

        return schedule

    def _calculate_dosha_balance_score(self, meals: List[Meal], dosha_type: str) -> float:
        """Calculate how well meals balance the dosha (0-100)."""
        # Simplified scoring
        balancing_count = 0
        total_ingredients = 0

        primary_dosha = dosha_type.lower().split("-")[0]

        for meal in meals:
            for ingredient in meal.ingredients:
                total_ingredients += 1
                # Check if ingredient reason mentions balancing
                if f"balances {primary_dosha}" in ingredient.reason.lower():
                    balancing_count += 1

        if total_ingredients == 0:
            return 50.0

        score = (balancing_count / total_ingredients) * 100
        return round(min(100, score + 50), 1)  # Baseline 50, bonus for balancing foods

    def _check_nutritional_compliance(
        self,
        total_cal: float,
        total_pro: float,
        total_carb: float,
        total_fat: float,
        req: DailyNutritionRequirements
    ) -> bool:
        """Check if nutrition meets requirements (within 15% tolerance)."""
        tolerance = 0.15

        cal_ok = abs(total_cal - req.target_calories) / req.target_calories <= tolerance
        pro_ok = abs(total_pro - req.protein_g) / req.protein_g <= tolerance
        carb_ok = abs(total_carb - req.carbs_g) / req.carbs_g <= tolerance
        fat_ok = abs(total_fat - req.fat_g) / req.fat_g <= tolerance

        return cal_ok and pro_ok and carb_ok and fat_ok

    def _identify_nutrient_gaps(
        self,
        total_cal: float,
        total_pro: float,
        total_carb: float,
        total_fat: float,
        total_fiber: float,
        req: DailyNutritionRequirements
    ) -> List[str]:
        """Identify nutrient deficiencies."""
        gaps = []

        if total_cal < req.target_calories * 0.9:
            gaps.append(f"calories (need {req.target_calories - total_cal:.0f} more)")

        if total_pro < req.protein_g * 0.9:
            gaps.append(f"protein (need {req.protein_g - total_pro:.0f}g more)")

        if total_fiber < req.fiber_g * 0.8:
            gaps.append(f"fiber (need {req.fiber_g - total_fiber:.0f}g more)")

        return gaps


# Singleton
_meal_optimizer = None


def get_meal_optimizer() -> MealPlanOptimizer:
    """Get singleton meal optimizer."""
    global _meal_optimizer
    if _meal_optimizer is None:
        _meal_optimizer = MealPlanOptimizer()
    return _meal_optimizer
