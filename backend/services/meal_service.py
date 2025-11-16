"""
Meal and Nutrition Service Layer

Handles meal logging, nutrition tracking, and food recognition
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import logging

from backend.database.mongo import get_collection
from backend.models.mongo_schemas import COLLECTION_MEAL_IMAGES

logger = logging.getLogger(__name__)


class MealService:
    """Service for managing meals and nutrition"""

    @staticmethod
    async def log_meal(
        user_id: str,
        meal_type: str,  # breakfast, lunch, dinner, snack
        foods: List[Dict[str, Any]],
        timestamp: datetime = None,
        notes: str = None,
        image_id: str = None
    ) -> dict:
        """
        Log a meal

        Args:
            user_id: User ID
            meal_type: Type of meal
            foods: List of food items with details
            timestamp: When the meal was consumed
            notes: Optional notes
            image_id: Reference to meal image if any

        Returns:
            Created meal log document
        """
        try:
            collection = get_collection("meal_logs")

            meal_log = {
                "user_id": user_id,
                "meal_type": meal_type,
                "foods": foods,  # [{"name": "Salad", "calories": 150, "protein_g": 5, ...}]
                "timestamp": timestamp or datetime.now(),
                "notes": notes,
                "image_id": image_id,
                "created_at": datetime.now()
            }

            # Calculate totals
            totals = MealService._calculate_nutrition_totals(foods)
            meal_log["nutrition_totals"] = totals

            result = await collection.insert_one(meal_log)
            meal_log["_id"] = str(result.inserted_id)

            logger.info(f"Logged {meal_type} for user {user_id}")
            return meal_log

        except Exception as e:
            logger.error(f"Error logging meal: {e}")
            raise

    @staticmethod
    def _calculate_nutrition_totals(foods: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total nutrition from list of foods"""
        totals = {
            "calories": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0,
            "fiber_g": 0,
            "sugar_g": 0
        }

        for food in foods:
            for key in totals.keys():
                totals[key] += food.get(key, 0)

        return totals

    @staticmethod
    async def get_meal_logs(
        user_id: str,
        start_date: date = None,
        end_date: date = None,
        meal_type: str = None,
        limit: int = 50
    ) -> List[dict]:
        """Get meal logs for a user"""
        try:
            collection = get_collection("meal_logs")

            # Build query
            query = {"user_id": user_id}

            if start_date or end_date:
                timestamp_query = {}
                if start_date:
                    timestamp_query["$gte"] = datetime.combine(start_date, datetime.min.time())
                if end_date:
                    timestamp_query["$lte"] = datetime.combine(end_date, datetime.max.time())
                query["timestamp"] = timestamp_query

            if meal_type:
                query["meal_type"] = meal_type

            # Execute query
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            meals = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for meal in meals:
                meal["_id"] = str(meal["_id"])

            return meals

        except Exception as e:
            logger.error(f"Error fetching meal logs: {e}")
            raise

    @staticmethod
    async def get_nutrition_summary(
        user_id: str,
        start_date: date = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get nutrition summary for a period

        Returns daily averages and totals
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=days-1)

            end_date = start_date + timedelta(days=days-1)

            meals = await MealService.get_meal_logs(
                user_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )

            if not meals:
                return {
                    "period_days": days,
                    "total_meals": 0,
                    "daily_averages": {},
                    "totals": {}
                }

            # Calculate totals
            totals = {
                "calories": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fat_g": 0,
                "fiber_g": 0,
                "sugar_g": 0
            }

            for meal in meals:
                nutrition = meal.get("nutrition_totals", {})
                for key in totals.keys():
                    totals[key] += nutrition.get(key, 0)

            # Calculate daily averages
            daily_averages = {k: round(v / days, 1) for k, v in totals.items()}

            # Meal type breakdown
            meal_type_counts = {}
            for meal in meals:
                meal_type = meal.get("meal_type", "unknown")
                meal_type_counts[meal_type] = meal_type_counts.get(meal_type, 0) + 1

            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_meals": len(meals),
                "meal_type_breakdown": meal_type_counts,
                "daily_averages": daily_averages,
                "totals": totals
            }

        except Exception as e:
            logger.error(f"Error getting nutrition summary: {e}")
            raise

    @staticmethod
    async def save_meal_image(
        user_id: str,
        image_path: str,
        image_format: str,
        detected_foods: List[Dict[str, Any]] = None,
        ocr_text: str = None
    ) -> str:
        """
        Save meal image metadata

        Returns: Image document ID
        """
        try:
            collection = get_collection(COLLECTION_MEAL_IMAGES)

            image_doc = {
                "user_id": user_id,
                "timestamp": datetime.now(),
                "image_path": image_path,
                "image_format": image_format,
                "detected_foods": detected_foods or [],
                "ocr_text": ocr_text,
                "extracted_info": None,
                "meal_log_id": None,
                "created_at": datetime.now()
            }

            result = await collection.insert_one(image_doc)
            logger.info(f"Saved meal image for user {user_id}")

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving meal image: {e}")
            raise

    @staticmethod
    async def get_meal_image(image_id: str) -> Optional[dict]:
        """Get meal image by ID"""
        try:
            from bson import ObjectId

            collection = get_collection(COLLECTION_MEAL_IMAGES)
            image = await collection.find_one({"_id": ObjectId(image_id)})

            if image:
                image["_id"] = str(image["_id"])

            return image

        except Exception as e:
            logger.error(f"Error fetching meal image: {e}")
            return None

    @staticmethod
    async def analyze_dietary_patterns(
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze user's dietary patterns and provide insights

        Returns:
            Dictionary with patterns and recommendations
        """
        try:
            summary = await MealService.get_nutrition_summary(user_id, days=days)

            if summary["total_meals"] == 0:
                return {"insights": ["Start logging meals to get personalized insights!"]}

            insights = []
            daily_avg = summary["daily_averages"]

            # Calorie analysis
            calories = daily_avg.get("calories", 0)
            if calories < 1200:
                insights.append("Your average calorie intake seems low. Consider consulting a nutritionist.")
            elif calories > 3000:
                insights.append("High calorie intake detected. Focus on nutrient-dense, lower-calorie foods.")

            # Protein analysis
            protein = daily_avg.get("protein_g", 0)
            if protein < 50:
                insights.append("Low protein intake. Add protein-rich foods like lean meats, legumes, or nuts.")
            elif protein > 150:
                insights.append("Very high protein intake. Ensure adequate hydration and balance with other nutrients.")

            # Fiber analysis
            fiber = daily_avg.get("fiber_g", 0)
            if fiber < 25:
                insights.append("Increase fiber intake with whole grains, vegetables, and fruits for better digestion.")

            # Sugar analysis
            sugar = daily_avg.get("sugar_g", 0)
            if sugar > 50:
                insights.append("High sugar intake detected. Reduce processed sugars and opt for natural sources.")

            # Macronutrient balance
            protein_cal = protein * 4
            carbs_cal = daily_avg.get("carbs_g", 0) * 4
            fat_cal = daily_avg.get("fat_g", 0) * 9
            total_cal = protein_cal + carbs_cal + fat_cal

            if total_cal > 0:
                protein_pct = (protein_cal / total_cal) * 100
                carbs_pct = (carbs_cal / total_cal) * 100
                fat_pct = (fat_cal / total_cal) * 100

                macro_balance = {
                    "protein_percent": round(protein_pct, 1),
                    "carbs_percent": round(carbs_pct, 1),
                    "fat_percent": round(fat_pct, 1)
                }

                # Check balance
                if carbs_pct > 65:
                    insights.append("High carbohydrate ratio. Consider balancing with more protein and healthy fats.")
                if fat_pct < 20:
                    insights.append("Low fat intake. Healthy fats from nuts, avocados, and fish are essential.")

            else:
                macro_balance = None

            # Meal frequency
            meals_per_day = summary["total_meals"] / days
            if meals_per_day < 2:
                insights.append("Consider eating more frequent, smaller meals to maintain energy levels.")

            return {
                "summary": summary,
                "macronutrient_balance": macro_balance,
                "insights": insights,
                "analysis_period_days": days
            }

        except Exception as e:
            logger.error(f"Error analyzing dietary patterns: {e}")
            raise
