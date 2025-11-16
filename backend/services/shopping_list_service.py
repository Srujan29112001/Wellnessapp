"""
Shopping List Service - Generate optimized shopping lists from meal plans

Features:
- Aggregate ingredients from weekly meal plans
- Group by category (produce, grains, proteins, spices, etc.)
- Calculate total quantities
- Estimate costs with currency conversion
- Support for multiple stores/regions
"""
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from collections import defaultdict
from decimal import Decimal
from pydantic import BaseModel

from backend.models.life_optimization_models import DailyMealPlan, Meal
from backend.services.currency_location_service import get_currency_service
from backend.services.global_food_database import get_food_database


class ShoppingListItem(BaseModel):
    """Single item in shopping list"""
    name: str
    category: str
    total_quantity: float
    unit: str
    estimated_cost: float
    currency: str
    formatted_cost: str
    stores_available: List[str] = []
    notes: Optional[str] = None


class ShoppingList(BaseModel):
    """Complete shopping list"""
    user_id: str
    start_date: date
    end_date: date
    num_days: int
    items: List[ShoppingListItem]
    total_cost: float
    currency: str
    formatted_total_cost: str
    items_by_category: Dict[str, List[ShoppingListItem]]
    total_items: int



class ShoppingListGenerator:
    """Generate shopping lists from meal plans"""

    # Food categories for organization
    CATEGORIES = {
        'produce': ['vegetables', 'fruits', 'greens', 'herbs', 'fresh'],
        'grains': ['rice', 'quinoa', 'oats', 'bread', 'pasta', 'wheat', 'flour'],
        'proteins': ['chicken', 'fish', 'tofu', 'eggs', 'meat', 'dal', 'lentils', 'beans', 'chickpeas'],
        'dairy': ['milk', 'yogurt', 'cheese', 'paneer', 'ghee', 'butter'],
        'spices': ['turmeric', 'cumin', 'coriander', 'pepper', 'salt', 'ginger', 'garlic', 'masala'],
        'oils': ['oil', 'ghee', 'butter'],
        'nuts': ['almonds', 'cashews', 'walnuts', 'peanuts', 'seeds'],
        'condiments': ['sauce', 'vinegar', 'honey', 'syrup'],
        'beverages': ['tea', 'coffee', 'juice'],
        'other': []
    }

    # Unit conversions to standardize quantities
    UNIT_CONVERSIONS = {
        # Weight conversions (to grams)
        'kg': 1000,
        'g': 1,
        'mg': 0.001,
        'lb': 453.592,
        'oz': 28.3495,

        # Volume conversions (to ml)
        'l': 1000,
        'ml': 1,
        'cup': 240,
        'tbsp': 15,
        'tsp': 5,
        'fl oz': 29.5735,

        # Count-based
        'piece': 1,
        'whole': 1,
        'unit': 1,
        'clove': 1,
        'bunch': 1,
        'handful': 1,
    }

    def __init__(self):
        self.currency_service = get_currency_service()
        self.food_db = get_food_database()

    def generate_shopping_list(
        self,
        meal_plans: List[DailyMealPlan],
        user_id: str,
        location: Optional[Dict] = None
    ) -> ShoppingList:
        """
        Generate shopping list from multiple daily meal plans

        Args:
            meal_plans: List of DailyMealPlan objects
            user_id: User identifier
            location: User location for pricing (auto-detected if None)

        Returns:
            ShoppingList with aggregated items and costs
        """
        if not meal_plans:
            return self._empty_shopping_list(user_id)

        # Detect location if not provided
        if not location:
            location = self.currency_service.detect_location_from_ip()

        # Extract dates
        start_date = min(plan.date for plan in meal_plans)
        end_date = max(plan.date for plan in meal_plans)
        num_days = len(meal_plans)

        # Aggregate ingredients
        ingredient_map = self._aggregate_ingredients(meal_plans)

        # Convert to shopping list items with categories and costs
        items = self._create_shopping_items(ingredient_map, location)

        # Calculate total cost
        total_cost = sum(item.estimated_cost for item in items)
        currency = location.get('currency', 'USD')
        formatted_total = self.currency_service.format_currency(total_cost, currency)

        # Group by category
        items_by_category = self._group_by_category(items)

        return ShoppingList(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            num_days=num_days,
            items=items,
            total_cost=total_cost,
            currency=currency,
            formatted_total_cost=formatted_total,
            items_by_category=items_by_category,
            total_items=len(items)
        )

    def _aggregate_ingredients(self, meal_plans: List[DailyMealPlan]) -> Dict[str, Dict]:
        """
        Aggregate ingredients across all meals

        Returns:
            Dict mapping ingredient name to {quantity, unit, occurrences, meals}
        """
        ingredient_map = defaultdict(lambda: {
            'quantities': [],  # List of (quantity, unit) tuples
            'occurrences': 0,
            'meals': [],
            'reasons': []
        })

        for plan in meal_plans:
            for meal in plan.meals:
                for ingredient in meal.ingredients:
                    name = ingredient.name.lower().strip()

                    # Store quantity info
                    ingredient_map[name]['quantities'].append((
                        ingredient.quantity,
                        ingredient.unit.lower()
                    ))
                    ingredient_map[name]['occurrences'] += 1
                    ingredient_map[name]['meals'].append(meal.name)
                    if ingredient.reason:
                        ingredient_map[name]['reasons'].append(ingredient.reason)

        return dict(ingredient_map)

    def _create_shopping_items(
        self,
        ingredient_map: Dict[str, Dict],
        location: Dict
    ) -> List[ShoppingListItem]:
        """Create shopping list items with aggregated quantities and costs"""
        items = []

        for ingredient_name, data in ingredient_map.items():
            # Aggregate quantities (handle unit conversions)
            total_qty, final_unit = self._aggregate_quantities(data['quantities'])

            # Determine category
            category = self._categorize_ingredient(ingredient_name)

            # Estimate cost
            estimated_cost, currency = self._estimate_cost(
                ingredient_name,
                total_qty,
                final_unit,
                location
            )

            # Format cost
            formatted_cost = self.currency_service.format_currency(estimated_cost, currency)

            # Create notes
            notes = f"Used in {data['occurrences']} meal(s)"
            if data['reasons']:
                unique_reasons = list(set(data['reasons']))[:2]
                notes += f" - {', '.join(unique_reasons)}"

            item = ShoppingListItem(
                name=ingredient_name.title(),
                category=category,
                total_quantity=round(total_qty, 2),
                unit=final_unit,
                estimated_cost=estimated_cost,
                currency=currency,
                formatted_cost=formatted_cost,
                stores_available=self._get_available_stores(ingredient_name, location),
                notes=notes
            )

            items.append(item)

        # Sort by category, then by name
        items.sort(key=lambda x: (x.category, x.name))

        return items

    def _aggregate_quantities(self, quantities: List[Tuple[float, str]]) -> Tuple[float, str]:
        """
        Aggregate quantities with unit conversion

        Returns:
            (total_quantity, standardized_unit)
        """
        if not quantities:
            return 0.0, 'unit'

        # Group by unit type (weight, volume, count)
        weight_units = ['kg', 'g', 'mg', 'lb', 'oz']
        volume_units = ['l', 'ml', 'cup', 'tbsp', 'tsp', 'fl oz']

        # Separate quantities by type
        weights = []
        volumes = []
        counts = []

        for qty, unit in quantities:
            unit_lower = unit.lower()
            if unit_lower in weight_units:
                # Convert to grams
                weights.append(qty * self.UNIT_CONVERSIONS.get(unit_lower, 1))
            elif unit_lower in volume_units:
                # Convert to ml
                volumes.append(qty * self.UNIT_CONVERSIONS.get(unit_lower, 1))
            else:
                # Count-based
                counts.append(qty)

        # Determine primary unit type and sum
        if weights:
            total_grams = sum(weights)
            if total_grams >= 1000:
                return total_grams / 1000, 'kg'
            else:
                return total_grams, 'g'
        elif volumes:
            total_ml = sum(volumes)
            if total_ml >= 1000:
                return total_ml / 1000, 'L'
            else:
                return total_ml, 'ml'
        elif counts:
            return sum(counts), 'pieces'
        else:
            return sum(q for q, _ in quantities), quantities[0][1]

    def _categorize_ingredient(self, ingredient_name: str) -> str:
        """Categorize ingredient for shopping list organization"""
        name_lower = ingredient_name.lower()

        for category, keywords in self.CATEGORIES.items():
            if category == 'other':
                continue
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return 'other'

    def _estimate_cost(
        self,
        ingredient_name: str,
        quantity: float,
        unit: str,
        location: Dict
    ) -> Tuple[float, str]:
        """
        Estimate cost of ingredient based on quantity and location

        Returns:
            (cost, currency)
        """
        # Try to get from food database
        food_item = self.food_db.get_food_by_name(ingredient_name)

        base_cost_usd = 0.0

        if food_item:
            # Use database cost
            base_cost_usd = food_item.get('cost_per_unit_usd', 1.0) * quantity
        else:
            # Fallback: estimate based on category
            category = self._categorize_ingredient(ingredient_name)
            cost_per_100g = {
                'produce': 0.5,
                'grains': 0.3,
                'proteins': 2.0,
                'dairy': 1.0,
                'spices': 0.8,
                'oils': 1.5,
                'nuts': 3.0,
                'condiments': 0.7,
                'beverages': 1.0,
                'other': 1.0
            }

            # Estimate assuming 100g units
            base_cost_usd = cost_per_100g.get(category, 1.0) * (quantity / 100)

        # Convert to local currency and adjust for region
        currency = location.get('currency', 'USD')
        local_cost, _ = self.currency_service.calculate_local_food_cost(
            base_cost_usd,
            location
        )

        return local_cost, currency

    def _get_available_stores(self, ingredient_name: str, location: Dict) -> List[str]:
        """Get list of stores where ingredient is commonly available"""
        country = location.get('country_code', 'US')

        # Generic stores by country
        stores_by_country = {
            'US': ['Whole Foods', 'Trader Joe\'s', 'Walmart', 'Kroger'],
            'IN': ['Big Bazaar', 'Reliance Fresh', 'DMart', 'More Megastore'],
            'UK': ['Tesco', 'Sainsbury\'s', 'Waitrose', 'Asda'],
            'CA': ['Loblaws', 'Metro', 'Whole Foods', 'Walmart'],
            'AU': ['Woolworths', 'Coles', 'IGA', 'Aldi'],
        }

        return stores_by_country.get(country, ['Local grocery store'])[:3]

    def _group_by_category(self, items: List[ShoppingListItem]) -> Dict[str, List[ShoppingListItem]]:
        """Group items by category"""
        grouped = defaultdict(list)
        for item in items:
            grouped[item.category].append(item)
        return dict(grouped)

    def _empty_shopping_list(self, user_id: str) -> ShoppingList:
        """Return empty shopping list"""
        return ShoppingList(
            user_id=user_id,
            start_date=date.today(),
            end_date=date.today(),
            num_days=0,
            items=[],
            total_cost=0.0,
            currency='USD',
            formatted_total_cost='$0.00',
            items_by_category={},
            total_items=0
        )

    def optimize_shopping_list(
        self,
        shopping_list: ShoppingList,
        optimization_strategy: str = 'cost'
    ) -> ShoppingList:
        """
        Optimize shopping list based on strategy

        Strategies:
        - 'cost': Minimize total cost by suggesting substitutions
        - 'time': Minimize shopping time by grouping stores
        - 'health': Prioritize nutrient-dense options
        """
        if optimization_strategy == 'cost':
            # TODO: Suggest cheaper alternatives
            pass
        elif optimization_strategy == 'time':
            # TODO: Optimize store routing
            pass
        elif optimization_strategy == 'health':
            # TODO: Prioritize organic/whole foods
            pass

        return shopping_list


# Singleton instance
_shopping_list_generator = None


def get_shopping_list_generator() -> ShoppingListGenerator:
    """Get singleton instance of shopping list generator"""
    global _shopping_list_generator
    if _shopping_list_generator is None:
        _shopping_list_generator = ShoppingListGenerator()
    return _shopping_list_generator
