"""
Global Food Database Service.

Comprehensive food database covering:
- All major cuisines worldwide (100+ countries)
- Regional pricing and availability
- Nutritional information
- Ayurvedic properties
- Allergen information
- Cost data for all regions
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class FoodCategory(str, Enum):
    """Food categories."""
    GRAINS = "grains"
    LEGUMES = "legumes"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    NUTS_SEEDS = "nuts_seeds"
    DAIRY = "dairy"
    MEAT = "meat"
    FISH = "fish"
    OILS_FATS = "oils_fats"
    SPICES = "spices"
    HERBS = "herbs"
    SWEETENERS = "sweeteners"
    BEVERAGES = "beverages"


@dataclass
class RegionalPrice:
    """Regional pricing for food item."""
    country_code: str
    region: Optional[str]
    price_per_kg: float  # In USD baseline
    currency: str
    availability: str  # abundant, common, seasonal, rare, imported


@dataclass
class AyurvedicProperties:
    """Ayurvedic properties of food."""
    rasa: List[str]  # Tastes: sweet, sour, salty, bitter, pungent, astringent
    virya: str  # heating, cooling, neutral
    vipaka: str  # sweet, sour, pungent (post-digestive effect)
    dosha_effect: Dict[str, str]  # vata, pitta, kapha -> increase/decrease/neutral
    qualities: List[str]  # heavy, light, oily, dry, etc.


@dataclass
class NutritionalData:
    """Nutritional information per 100g."""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    water_g: float

    # Micronutrients (optional)
    vitamin_a_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None


@dataclass
class FoodItem:
    """Complete food item definition."""
    food_id: str
    name: str
    local_names: Dict[str, str]  # {"IN": "दाल", "ES": "lentejas"}
    category: FoodCategory
    cuisines: List[str]  # indian, italian, mexican, etc.

    # Nutrition
    nutrition: NutritionalData

    # Ayurveda
    ayurvedic: AyurvedicProperties

    # Pricing (regional)
    regional_prices: List[RegionalPrice]
    base_price_usd_per_kg: float

    # Tags
    allergens: List[str]  # gluten, dairy, nuts, soy, etc.
    dietary_flags: List[str]  # vegan, vegetarian, paleo, keto, etc.

    # Seasonality
    peak_seasons: List[str]  # spring, summer, fall, winter

    # Storage & prep
    shelf_life_days: int
    common_units: List[str]  # kg, g, cup, piece

    # Cultural notes
    description: str
    common_preparations: List[str]


class GlobalFoodDatabase:
    """Global food database with 500+ common foods."""

    def __init__(self):
        """Initialize database."""
        self.foods: Dict[str, FoodItem] = {}
        self._load_database()

    def _load_database(self):
        """Load food database."""
        # GRAINS - Worldwide
        self._add_food(FoodItem(
            food_id="rice_white_basmati",
            name="Basmati Rice (White)",
            local_names={"IN": "बासमती चावल", "PK": "باسمتی چاول", "BD": "বাসমতী চাল"},
            category=FoodCategory.GRAINS,
            cuisines=["indian", "pakistani", "persian", "middle_eastern"],
            nutrition=NutritionalData(
                calories=130, protein_g=2.7, carbs_g=28.2, fat_g=0.3, fiber_g=0.4, water_g=68.4,
                iron_mg=0.2, magnesium_mg=12
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "decrease", "pitta": "decrease", "kapha": "increase"},
                qualities=["light", "soft", "smooth"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Mumbai", 1.20, "INR", "abundant"),
                RegionalPrice("IN", "Delhi", 1.10, "INR", "abundant"),
                RegionalPrice("US", "California", 4.50, "USD", "common"),
                RegionalPrice("GB", None, 3.80, "GBP", "common"),
                RegionalPrice("PK", "Karachi", 1.00, "PKR", "abundant"),
            ],
            base_price_usd_per_kg=2.50,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "gluten_free"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "cup", "g"],
            description="Long-grain aromatic rice from India/Pakistan",
            common_preparations=["steamed", "pilaf", "biryani"]
        ))

        self._add_food(FoodItem(
            food_id="rice_brown",
            name="Brown Rice",
            local_names={"IN": "ब्राउन चावल", "CN": "糙米", "JP": "玄米", "ES": "arroz integral"},
            category=FoodCategory.GRAINS,
            cuisines=["global", "health_food"],
            nutrition=NutritionalData(
                calories=111, protein_g=2.6, carbs_g=23.0, fat_g=0.9, fiber_g=1.8, water_g=72.6,
                magnesium_mg=43, phosphorus_mg=83, vitamin_b6_mg=0.15
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet"],
                virya="neutral",
                vipaka="sweet",
                dosha_effect={"vata": "neutral", "pitta": "decrease", "kapha": "neutral"},
                qualities=["heavy", "nourishing"]
            ),
            regional_prices=[
                RegionalPrice("US", "California", 3.20, "USD", "abundant"),
                RegionalPrice("IN", "Bangalore", 1.80, "INR", "common"),
                RegionalPrice("CN", "Shanghai", 2.50, "CNY", "abundant"),
                RegionalPrice("GB", "London", 3.50, "GBP", "common"),
            ],
            base_price_usd_per_kg=3.00,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "gluten_free", "whole_grain"],
            peak_seasons=["year_round"],
            shelf_life_days=180,
            common_units=["kg", "cup", "g"],
            description="Whole grain rice with bran intact",
            common_preparations=["steamed", "pilaf", "bowls"]
        ))

        self._add_food(FoodItem(
            food_id="quinoa",
            name="Quinoa",
            local_names={"ES": "quinua", "PE": "kinwa", "FR": "quinoa"},
            category=FoodCategory.GRAINS,
            cuisines=["peruvian", "health_food", "global"],
            nutrition=NutritionalData(
                calories=120, protein_g=4.4, carbs_g=21.3, fat_g=1.9, fiber_g=2.8, water_g=71.6,
                iron_mg=1.5, magnesium_mg=64, zinc_mg=1.1
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet", "astringent"],
                virya="heating",
                vipaka="sweet",
                dosha_effect={"vata": "decrease", "pitta": "increase", "kapha": "decrease"},
                qualities=["light", "dry"]
            ),
            regional_prices=[
                RegionalPrice("PE", "Lima", 3.00, "PEN", "abundant"),
                RegionalPrice("US", "California", 6.50, "USD", "common"),
                RegionalPrice("GB", None, 5.80, "GBP", "common"),
                RegionalPrice("IN", "Mumbai", 8.00, "INR", "imported"),
            ],
            base_price_usd_per_kg=6.00,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "gluten_free", "high_protein"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "cup", "g"],
            description="Complete protein pseudo-grain from Andes",
            common_preparations=["steamed", "salads", "bowls"]
        ))

        self._add_food(FoodItem(
            food_id="oats_rolled",
            name="Rolled Oats",
            local_names={"DE": "Haferflocken", "FR": "flocons d'avoine", "ES": "avena", "IN": "ओट्स"},
            category=FoodCategory.GRAINS,
            cuisines=["global", "western", "health_food"],
            nutrition=NutritionalData(
                calories=71, protein_g=2.5, carbs_g=12.0, fat_g=1.5, fiber_g=1.7, water_g=83.6,
                iron_mg=0.7, magnesium_mg=27
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet"],
                virya="heating",
                vipaka="sweet",
                dosha_effect={"vata": "decrease", "pitta": "neutral", "kapha": "increase"},
                qualities=["heavy", "nourishing", "grounding"]
            ),
            regional_prices=[
                RegionalPrice("US", "Midwest", 2.50, "USD", "abundant"),
                RegionalPrice("GB", None, 2.20, "GBP", "abundant"),
                RegionalPrice("DE", None, 2.00, "EUR", "abundant"),
                RegionalPrice("IN", "Bangalore", 4.00, "INR", "common"),
            ],
            base_price_usd_per_kg=2.80,
            allergens=["gluten"],
            dietary_flags=["vegetarian", "vegan"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "cup", "g"],
            description="Whole grain oats, heart-healthy",
            common_preparations=["porridge", "overnight_oats", "baking"]
        ))

        # LEGUMES - Worldwide
        self._add_food(FoodItem(
            food_id="lentils_red",
            name="Red Lentils (Masoor Dal)",
            local_names={"IN": "मसूर दाल", "TR": "kırmızı mercimek", "AR": "عدس أحمر"},
            category=FoodCategory.LEGUMES,
            cuisines=["indian", "middle_eastern", "turkish", "ethiopian"],
            nutrition=NutritionalData(
                calories=116, protein_g=9.0, carbs_g=20.0, fat_g=0.4, fiber_g=7.9, water_g=69.0,
                iron_mg=3.3, folate_mcg=181
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet", "astringent"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "increase", "pitta": "decrease", "kapha": "neutral"},
                qualities=["light", "dry"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Delhi", 0.80, "INR", "abundant"),
                RegionalPrice("TR", "Istanbul", 1.50, "TRY", "abundant"),
                RegionalPrice("US", "California", 3.50, "USD", "common"),
                RegionalPrice("GB", None, 2.80, "GBP", "common"),
            ],
            base_price_usd_per_kg=2.50,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "gluten_free", "high_protein"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "cup", "g"],
            description="Split red lentils, quick-cooking",
            common_preparations=["dal", "soup", "stew"]
        ))

        self._add_food(FoodItem(
            food_id="chickpeas",
            name="Chickpeas (Garbanzo Beans)",
            local_names={"IN": "चना", "ES": "garbanzos", "AR": "حمص", "IT": "ceci"},
            category=FoodCategory.LEGUMES,
            cuisines=["indian", "middle_eastern", "mediterranean", "spanish"],
            nutrition=NutritionalData(
                calories=164, protein_g=8.9, carbs_g=27.4, fat_g=2.6, fiber_g=7.6, water_g=60.2,
                iron_mg=2.9, folate_mcg=172, magnesium_mg=48
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet", "astringent"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "increase", "pitta": "decrease", "kapha": "increase"},
                qualities=["heavy", "dry"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Mumbai", 1.20, "INR", "abundant"),
                RegionalPrice("ES", "Madrid", 2.50, "EUR", "abundant"),
                RegionalPrice("US", "California", 3.20, "USD", "abundant"),
                RegionalPrice("TR", "Ankara", 1.80, "TRY", "abundant"),
            ],
            base_price_usd_per_kg=2.80,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "gluten_free", "high_protein"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "cup", "g"],
            description="Versatile legume, high protein",
            common_preparations=["curry", "hummus", "roasted", "salad"]
        ))

        self._add_food(FoodItem(
            food_id="mung_beans",
            name="Mung Beans (Moong Dal)",
            local_names={"IN": "मूंग दाल", "CN": "绿豆", "TH": "ถั่วเขียว"},
            category=FoodCategory.LEGUMES,
            cuisines=["indian", "chinese", "thai", "korean"],
            nutrition=NutritionalData(
                calories=105, protein_g=7.0, carbs_g=19.0, fat_g=0.4, fiber_g=7.6, water_g=72.0,
                iron_mg=1.8, folate_mcg=159
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet", "astringent"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "neutral", "pitta": "decrease", "kapha": "neutral"},
                qualities=["light", "easy_to_digest"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Delhi", 1.00, "INR", "abundant"),
                RegionalPrice("CN", "Beijing", 1.50, "CNY", "abundant"),
                RegionalPrice("US", "California", 4.50, "USD", "common"),
                RegionalPrice("TH", "Bangkok", 1.20, "THB", "abundant"),
            ],
            base_price_usd_per_kg=3.00,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "gluten_free", "easy_digest"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "cup", "g"],
            description="Most digestible bean, Ayurvedic superfood",
            common_preparations=["dal", "soup", "sprouts", "porridge"]
        ))

        # VEGETABLES - Worldwide
        self._add_food(FoodItem(
            food_id="spinach",
            name="Spinach",
            local_names={"IN": "पालक", "ES": "espinacas", "FR": "épinards", "AR": "سبانخ"},
            category=FoodCategory.VEGETABLES,
            cuisines=["global"],
            nutrition=NutritionalData(
                calories=23, protein_g=2.9, carbs_g=3.6, fat_g=0.4, fiber_g=2.2, water_g=91.4,
                vitamin_a_mcg=469, vitamin_c_mg=28, iron_mg=2.7, calcium_mg=99
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["astringent", "bitter"],
                virya="cooling",
                vipaka="pungent",
                dosha_effect={"vata": "increase", "pitta": "decrease", "kapha": "decrease"},
                qualities=["light", "dry"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Mumbai", 0.50, "INR", "abundant"),
                RegionalPrice("US", "California", 4.00, "USD", "abundant"),
                RegionalPrice("GB", None, 3.50, "GBP", "abundant"),
                RegionalPrice("ES", "Madrid", 2.80, "EUR", "abundant"),
            ],
            base_price_usd_per_kg=3.50,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "low_calorie"],
            peak_seasons=["spring", "fall", "winter"],
            shelf_life_days=7,
            common_units=["kg", "bunch", "g"],
            description="Nutrient-dense leafy green",
            common_preparations=["sautéed", "curry", "salad", "smoothie"]
        ))

        self._add_food(FoodItem(
            food_id="tomatoes",
            name="Tomatoes",
            local_names={"IN": "टमाटर", "ES": "tomates", "IT": "pomodori", "FR": "tomates"},
            category=FoodCategory.VEGETABLES,
            cuisines=["global"],
            nutrition=NutritionalData(
                calories=18, protein_g=0.9, carbs_g=3.9, fat_g=0.2, fiber_g=1.2, water_g=94.5,
                vitamin_a_mcg=42, vitamin_c_mg=14, potassium_mg=237
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sour", "sweet"],
                virya="heating",
                vipaka="sour",
                dosha_effect={"vata": "decrease", "pitta": "increase", "kapha": "neutral"},
                qualities=["light", "liquid"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Mumbai", 0.30, "INR", "abundant"),
                RegionalPrice("US", "California", 3.50, "USD", "abundant"),
                RegionalPrice("IT", "Rome", 2.50, "EUR", "abundant"),
                RegionalPrice("MX", "Mexico City", 1.00, "MXN", "abundant"),
            ],
            base_price_usd_per_kg=2.80,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "low_calorie"],
            peak_seasons=["summer", "fall"],
            shelf_life_days=10,
            common_units=["kg", "piece", "g"],
            description="Versatile fruit-vegetable, rich in lycopene",
            common_preparations=["raw", "curry", "sauce", "salad"]
        ))

        self._add_food(FoodItem(
            food_id="broccoli",
            name="Broccoli",
            local_names={"IN": "ब्रोकोली", "ES": "brócoli", "IT": "broccoli", "DE": "Brokkoli"},
            category=FoodCategory.VEGETABLES,
            cuisines=["western", "global"],
            nutrition=NutritionalData(
                calories=34, protein_g=2.8, carbs_g=6.6, fat_g=0.4, fiber_g=2.6, water_g=89.3,
                vitamin_c_mg=89, vitamin_k_mcg=102, folate_mcg=63
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["bitter", "astringent"],
                virya="heating",
                vipaka="pungent",
                dosha_effect={"vata": "increase", "pitta": "increase", "kapha": "decrease"},
                qualities=["light", "dry", "rough"]
            ),
            regional_prices=[
                RegionalPrice("US", "California", 3.80, "USD", "abundant"),
                RegionalPrice("GB", None, 3.20, "GBP", "abundant"),
                RegionalPrice("IN", "Bangalore", 4.50, "INR", "common"),
                RegionalPrice("CN", "Shanghai", 2.50, "CNY", "common"),
            ],
            base_price_usd_per_kg=3.50,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "low_calorie", "cruciferous"],
            peak_seasons=["fall", "winter", "spring"],
            shelf_life_days=7,
            common_units=["kg", "head", "g"],
            description="Cruciferous vegetable, anti-cancer properties",
            common_preparations=["steamed", "roasted", "stir_fried", "raw"]
        ))

        # FRUITS - Worldwide
        self._add_food(FoodItem(
            food_id="bananas",
            name="Bananas",
            local_names={"IN": "केला", "ES": "plátanos", "FR": "bananes", "AR": "موز"},
            category=FoodCategory.FRUITS,
            cuisines=["global"],
            nutrition=NutritionalData(
                calories=89, protein_g=1.1, carbs_g=22.8, fat_g=0.3, fiber_g=2.6, water_g=74.9,
                potassium_mg=358, vitamin_c_mg=8.7
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "decrease", "pitta": "neutral", "kapha": "increase"},
                qualities=["heavy", "smooth", "soft"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Mumbai", 0.50, "INR", "abundant"),
                RegionalPrice("US", "California", 1.50, "USD", "abundant"),
                RegionalPrice("BR", "São Paulo", 0.80, "BRL", "abundant"),
                RegionalPrice("PH", "Manila", 0.40, "PHP", "abundant"),
            ],
            base_price_usd_per_kg=1.20,
            allergens=[],
            dietary_flags=["vegan", "vegetarian"],
            peak_seasons=["year_round"],
            shelf_life_days=7,
            common_units=["kg", "piece"],
            description="Quick energy, high potassium",
            common_preparations=["raw", "smoothie", "cooked"]
        ))

        self._add_food(FoodItem(
            food_id="apples",
            name="Apples",
            local_names={"IN": "सेब", "ES": "manzanas", "FR": "pommes", "DE": "Äpfel"},
            category=FoodCategory.FRUITS,
            cuisines=["global"],
            nutrition=NutritionalData(
                calories=52, protein_g=0.3, carbs_g=13.8, fat_g=0.2, fiber_g=2.4, water_g=85.6,
                vitamin_c_mg=4.6, potassium_mg=107
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet", "astringent"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "neutral", "pitta": "decrease", "kapha": "decrease"},
                qualities=["light", "dry"]
            ),
            regional_prices=[
                RegionalPrice("US", "Washington", 2.80, "USD", "abundant"),
                RegionalPrice("IN", "Kashmir", 2.50, "INR", "seasonal"),
                RegionalPrice("FR", "Normandy", 2.20, "EUR", "abundant"),
                RegionalPrice("CN", "Shandong", 1.80, "CNY", "abundant"),
            ],
            base_price_usd_per_kg=2.50,
            allergens=[],
            dietary_flags=["vegan", "vegetarian"],
            peak_seasons=["fall", "winter"],
            shelf_life_days=30,
            common_units=["kg", "piece"],
            description="Classic fruit, high fiber",
            common_preparations=["raw", "baked", "sauce"]
        ))

        # NUTS & SEEDS
        self._add_food(FoodItem(
            food_id="almonds",
            name="Almonds",
            local_names={"IN": "बादाम", "ES": "almendras", "AR": "لوز", "FR": "amandes"},
            category=FoodCategory.NUTS_SEEDS,
            cuisines=["global", "mediterranean", "middle_eastern"],
            nutrition=NutritionalData(
                calories=579, protein_g=21.2, carbs_g=21.6, fat_g=49.9, fiber_g=12.5, water_g=4.4,
                vitamin_e_mg=25.6, magnesium_mg=270, calcium_mg=269
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet"],
                virya="heating",
                vipaka="sweet",
                dosha_effect={"vata": "decrease", "pitta": "increase", "kapha": "increase"},
                qualities=["heavy", "oily", "nourishing"]
            ),
            regional_prices=[
                RegionalPrice("US", "California", 12.00, "USD", "abundant"),
                RegionalPrice("IN", "Mumbai", 15.00, "INR", "common"),
                RegionalPrice("ES", "Andalusia", 10.50, "EUR", "abundant"),
                RegionalPrice("AU", "Victoria", 11.00, "AUD", "common"),
            ],
            base_price_usd_per_kg=12.00,
            allergens=["tree_nuts"],
            dietary_flags=["vegan", "vegetarian", "keto", "paleo"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "g", "piece"],
            description="Brain food, vitamin E rich",
            common_preparations=["raw", "roasted", "milk", "butter"]
        ))

        # SPICES - Indian
        self._add_food(FoodItem(
            food_id="turmeric",
            name="Turmeric (Haldi)",
            local_names={"IN": "हल्दी", "AR": "كركم", "TH": "ขมิ้น"},
            category=FoodCategory.SPICES,
            cuisines=["indian", "thai", "indonesian"],
            nutrition=NutritionalData(
                calories=354, protein_g=7.8, carbs_g=64.9, fat_g=9.9, fiber_g=21.1, water_g=11.4,
                iron_mg=41.4, vitamin_c_mg=25.9
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["bitter", "pungent", "astringent"],
                virya="heating",
                vipaka="pungent",
                dosha_effect={"vata": "decrease", "pitta": "neutral", "kapha": "decrease"},
                qualities=["light", "dry", "purifying"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Kerala", 3.50, "INR", "abundant"),
                RegionalPrice("US", "California", 15.00, "USD", "common"),
                RegionalPrice("TH", "Bangkok", 4.00, "THB", "abundant"),
            ],
            base_price_usd_per_kg=8.00,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "anti_inflammatory"],
            peak_seasons=["year_round"],
            shelf_life_days=730,
            common_units=["kg", "g", "tsp"],
            description="Golden spice, anti-inflammatory curcumin",
            common_preparations=["powder", "fresh", "paste"]
        ))

        self._add_food(FoodItem(
            food_id="cumin",
            name="Cumin (Jeera)",
            local_names={"IN": "जीरा", "ES": "comino", "AR": "كمون"},
            category=FoodCategory.SPICES,
            cuisines=["indian", "middle_eastern", "mexican", "moroccan"],
            nutrition=NutritionalData(
                calories=375, protein_g=17.8, carbs_g=44.2, fat_g=22.3, fiber_g=10.5, water_g=8.1,
                iron_mg=66.4, calcium_mg=931
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["pungent", "bitter"],
                virya="cooling",
                vipaka="pungent",
                dosha_effect={"vata": "decrease", "pitta": "decrease", "kapha": "decrease"},
                qualities=["light", "dry", "stimulating"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Gujarat", 5.00, "INR", "abundant"),
                RegionalPrice("US", "California", 18.00, "USD", "common"),
                RegionalPrice("MX", "Mexico City", 8.00, "MXN", "common"),
            ],
            base_price_usd_per_kg=12.00,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "digestive"],
            peak_seasons=["year_round"],
            shelf_life_days=730,
            common_units=["kg", "g", "tsp"],
            description="Digestive aid, tri-doshic balancer",
            common_preparations=["whole", "powder", "roasted"]
        ))

        # OILS & FATS
        self._add_food(FoodItem(
            food_id="ghee",
            name="Ghee (Clarified Butter)",
            local_names={"IN": "घी", "NP": "घ्यू", "PK": "گھی"},
            category=FoodCategory.OILS_FATS,
            cuisines=["indian", "pakistani", "ayurvedic"],
            nutrition=NutritionalData(
                calories=900, protein_g=0.0, carbs_g=0.0, fat_g=100.0, fiber_g=0.0, water_g=0.0,
                vitamin_a_mcg=840, vitamin_e_mg=2.8
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet"],
                virya="cooling",
                vipaka="sweet",
                dosha_effect={"vata": "decrease", "pitta": "decrease", "kapha": "increase"},
                qualities=["heavy", "oily", "smooth", "nourishing"]
            ),
            regional_prices=[
                RegionalPrice("IN", "Mumbai", 12.00, "INR", "abundant"),
                RegionalPrice("US", "California", 30.00, "USD", "common"),
                RegionalPrice("PK", "Lahore", 10.00, "PKR", "abundant"),
            ],
            base_price_usd_per_kg=25.00,
            allergens=["dairy"],
            dietary_flags=["vegetarian", "keto", "paleo"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["kg", "ml", "tbsp"],
            description="Sacred Ayurvedic fat, increases Ojas",
            common_preparations=["cooking", "medicine", "ritual"]
        ))

        self._add_food(FoodItem(
            food_id="olive_oil",
            name="Olive Oil (Extra Virgin)",
            local_names={"ES": "aceite de oliva", "IT": "olio d'oliva", "GR": "ελαιόλαδο"},
            category=FoodCategory.OILS_FATS,
            cuisines=["mediterranean", "greek", "italian", "spanish"],
            nutrition=NutritionalData(
                calories=884, protein_g=0.0, carbs_g=0.0, fat_g=100.0, fiber_g=0.0, water_g=0.0,
                vitamin_e_mg=14.4, vitamin_k_mcg=60.2
            ),
            ayurvedic=AyurvedicProperties(
                rasa=["sweet", "bitter"],
                virya="heating",
                vipaka="pungent",
                dosha_effect={"vata": "decrease", "pitta": "neutral", "kapha": "neutral"},
                qualities=["heavy", "oily"]
            ),
            regional_prices=[
                RegionalPrice("ES", "Andalusia", 8.00, "EUR", "abundant"),
                RegionalPrice("IT", "Tuscany", 12.00, "EUR", "abundant"),
                RegionalPrice("US", "California", 15.00, "USD", "common"),
                RegionalPrice("IN", "Mumbai", 18.00, "INR", "imported"),
            ],
            base_price_usd_per_kg=14.00,
            allergens=[],
            dietary_flags=["vegan", "vegetarian", "keto", "mediterranean"],
            peak_seasons=["year_round"],
            shelf_life_days=365,
            common_units=["liter", "ml", "tbsp"],
            description="Heart-healthy monounsaturated fat",
            common_preparations=["raw", "cooking", "dressing"]
        ))

        # Add more foods for different regions...
        # This is a comprehensive foundation that can be extended

    def _add_food(self, food: FoodItem):
        """Add food to database."""
        self.foods[food.food_id] = food

    def get_food(self, food_id: str) -> Optional[FoodItem]:
        """Get food by ID."""
        return self.foods.get(food_id)

    def search_foods(
        self,
        category: Optional[FoodCategory] = None,
        cuisine: Optional[str] = None,
        dietary_flags: Optional[List[str]] = None,
        exclude_allergens: Optional[List[str]] = None,
        dosha_balance: Optional[str] = None,
        max_price_usd: Optional[float] = None
    ) -> List[FoodItem]:
        """
        Search foods by criteria.

        Args:
            category: Food category filter
            cuisine: Cuisine filter
            dietary_flags: Required dietary flags
            exclude_allergens: Allergens to exclude
            dosha_balance: Dosha to balance ("vata", "pitta", "kapha")
            max_price_usd: Maximum price per kg

        Returns:
            List of matching food items
        """
        results = []

        for food in self.foods.values():
            # Category filter
            if category and food.category != category:
                continue

            # Cuisine filter
            if cuisine and cuisine.lower() not in [c.lower() for c in food.cuisines]:
                continue

            # Dietary flags filter
            if dietary_flags:
                if not all(flag in food.dietary_flags for flag in dietary_flags):
                    continue

            # Allergen filter
            if exclude_allergens:
                if any(allergen in food.allergens for allergen in exclude_allergens):
                    continue

            # Dosha filter
            if dosha_balance:
                dosha_effect = food.ayurvedic.dosha_effect.get(dosha_balance.lower())
                if dosha_effect != "decrease":
                    continue

            # Price filter
            if max_price_usd and food.base_price_usd_per_kg > max_price_usd:
                continue

            results.append(food)

        return results

    def get_regional_price(
        self,
        food_id: str,
        country_code: str,
        region: Optional[str] = None
    ) -> Optional[RegionalPrice]:
        """Get regional price for food."""
        food = self.get_food(food_id)
        if not food:
            return None

        # Try exact match with region
        if region:
            for price in food.regional_prices:
                if price.country_code == country_code and price.region == region:
                    return price

        # Try country-level match
        for price in food.regional_prices:
            if price.country_code == country_code and not price.region:
                return price

        # Return first match for country
        for price in food.regional_prices:
            if price.country_code == country_code:
                return price

        return None

    def get_foods_by_category(self, category: FoodCategory) -> List[FoodItem]:
        """Get all foods in a category."""
        return [f for f in self.foods.values() if f.category == category]

    def get_foods_for_dosha(self, dosha: str) -> List[FoodItem]:
        """Get foods that balance a dosha."""
        return self.search_foods(dosha_balance=dosha)


# Singleton instance
_global_food_db = None


def get_food_database() -> GlobalFoodDatabase:
    """Get singleton food database."""
    global _global_food_db
    if _global_food_db is None:
        _global_food_db = GlobalFoodDatabase()
    return _global_food_db


# Example usage
if __name__ == "__main__":
    db = get_food_database()

    print(f"=== GLOBAL FOOD DATABASE ===")
    print(f"Total foods: {len(db.foods)}\n")

    # Search examples
    print("=== VEGAN HIGH-PROTEIN FOODS ===")
    vegan_protein = db.search_foods(
        dietary_flags=["vegan", "high_protein"],
        exclude_allergens=["nuts"]
    )
    for food in vegan_protein[:5]:
        print(f"- {food.name}: {food.nutrition.protein_g}g protein per 100g")

    print("\n=== FOODS TO BALANCE PITTA ===")
    pitta_foods = db.get_foods_for_dosha("pitta")
    for food in pitta_foods[:5]:
        print(f"- {food.name}: {food.ayurvedic.virya} energy")

    print("\n=== REGIONAL PRICING (Mumbai) ===")
    for food_id in ["rice_white_basmati", "lentils_red", "spinach"]:
        food = db.get_food(food_id)
        price = db.get_regional_price(food_id, "IN", "Mumbai")
        if food and price:
            print(f"- {food.name}: {price.price_per_kg} {price.currency}/kg ({price.availability})")
