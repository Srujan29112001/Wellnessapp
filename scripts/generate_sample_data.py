"""
Generate sample data for testing the Wellness AI system

This script creates:
- Sample EEG data (CSV format)
- Sample user profiles
- Sample health metrics
- Sample meal images (placeholders)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
import random


def generate_sample_eeg(
    output_path: str = "/home/user/Wellnessapp/data/raw/sample_eeg.csv",
    duration: int = 10,
    sample_rate: int = 256,
    num_channels: int = 14,
    mental_state: str = "stressed"  # or "relaxed", "focused"
):
    """
    Generate synthetic EEG data

    Args:
        output_path: Where to save the CSV
        duration: Duration in seconds
        sample_rate: Sampling rate in Hz
        num_channels: Number of EEG channels
        mental_state: Mental state to simulate
    """
    samples = duration * sample_rate
    time = np.linspace(0, duration, samples)

    eeg_data = []

    for ch in range(num_channels):
        # Base signal with different frequency components
        if mental_state == "stressed":
            # High beta waves (stress/anxiety)
            signal = (
                np.sin(2 * np.pi * 8 * time) * 0.3 +   # Alpha (low)
                np.sin(2 * np.pi * 22 * time) * 0.8 +  # Beta (high - stress)
                np.random.randn(samples) * 0.2         # Noise
            )
        elif mental_state == "relaxed":
            # High alpha waves (relaxation)
            signal = (
                np.sin(2 * np.pi * 10 * time) * 0.9 +  # Alpha (high)
                np.sin(2 * np.pi * 15 * time) * 0.2 +  # Beta (low)
                np.random.randn(samples) * 0.1         # Noise
            )
        else:  # focused
            # Moderate beta, some alpha
            signal = (
                np.sin(2 * np.pi * 10 * time) * 0.5 +  # Alpha (moderate)
                np.sin(2 * np.pi * 18 * time) * 0.6 +  # Beta (moderate - focus)
                np.random.randn(samples) * 0.15        # Noise
            )

        # Add some channel-specific variation
        signal += np.sin(2 * np.pi * (ch + 1) * 0.5 * time) * 0.1

        eeg_data.append(signal)

    # Convert to DataFrame
    eeg_df = pd.DataFrame(eeg_data)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    eeg_df.to_csv(output_path, index=False, header=False)

    print(f"✅ Generated sample EEG data ({mental_state}): {output_path}")
    print(f"   Duration: {duration}s, Channels: {num_channels}, Samples: {samples}")

    return output_path


def generate_user_profiles(
    output_path: str = "/home/user/Wellnessapp/data/sample_users.json",
    num_users: int = 5
):
    """Generate sample user profiles"""

    doshas = ["Vata", "Pitta", "Kapha"]
    goals = [
        "Reduce stress",
        "Improve sleep",
        "Increase energy",
        "Better focus",
        "Weight management",
        "Mental clarity"
    ]

    users = []
    for i in range(num_users):
        user = {
            "id": f"user_{i+1}",
            "email": f"user{i+1}@example.com",
            "name": f"Test User {i+1}",
            "dosha_type": random.choice(doshas),
            "health_goals": random.sample(goals, k=random.randint(2, 4)),
            "age": random.randint(25, 55),
            "current_supplements": random.sample(
                ["Ashwagandha", "Magnesium", "Vitamin D3", "Omega-3", "Brahmi"],
                k=random.randint(0, 3)
            ),
            "medical_conditions": [],
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        users.append(user)

    # Save to JSON
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(users, f, indent=2)

    print(f"✅ Generated {num_users} sample user profiles: {output_path}")
    return users


def generate_health_metrics(
    output_path: str = "/home/user/Wellnessapp/data/sample_health_metrics.json",
    num_days: int = 30
):
    """Generate sample health metrics data"""

    metrics = []
    base_date = datetime.now() - timedelta(days=num_days)

    for day in range(num_days):
        date = base_date + timedelta(days=day)

        metric = {
            "date": date.isoformat(),
            "steps": random.randint(3000, 15000),
            "sleep_hours": round(random.uniform(5.5, 9.0), 1),
            "heart_rate_avg": random.randint(60, 85),
            "heart_rate_resting": random.randint(55, 75),
            "weight_kg": round(random.uniform(60, 90), 1),
            "stress_level": round(random.uniform(0.2, 0.8), 2),
            "mood_score": random.randint(5, 10),
            "water_intake_ml": random.randint(1000, 3000),
            "calories_consumed": random.randint(1600, 2800)
        }
        metrics.append(metric)

    # Save to JSON
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Generated {num_days} days of health metrics: {output_path}")
    return metrics


def generate_meal_logs(
    output_path: str = "/home/user/Wellnessapp/data/sample_meals.json",
    num_meals: int = 20
):
    """Generate sample meal logs"""

    meals = [
        {"name": "Grilled Salmon with Vegetables", "type": "lunch", "calories": 450, "protein": 35, "carbs": 20, "fat": 25},
        {"name": "Chicken Caesar Salad", "type": "lunch", "calories": 380, "protein": 32, "carbs": 15, "fat": 22},
        {"name": "Oatmeal with Berries", "type": "breakfast", "calories": 320, "protein": 10, "carbs": 58, "fat": 6},
        {"name": "Avocado Toast", "type": "breakfast", "calories": 350, "protein": 12, "carbs": 40, "fat": 18},
        {"name": "Steak with Sweet Potato", "type": "dinner", "calories": 620, "protein": 45, "carbs": 35, "fat": 32},
        {"name": "Vegetable Stir Fry with Tofu", "type": "dinner", "calories": 380, "protein": 18, "carbs": 45, "fat": 14},
        {"name": "Greek Yogurt with Nuts", "type": "snack", "calories": 220, "protein": 15, "carbs": 18, "fat": 12},
        {"name": "Protein Smoothie", "type": "snack", "calories": 280, "protein": 25, "carbs": 30, "fat": 8},
    ]

    meal_logs = []
    base_date = datetime.now() - timedelta(days=7)

    for i in range(num_meals):
        date = base_date + timedelta(days=random.randint(0, 7), hours=random.randint(7, 20))
        meal = random.choice(meals)

        log = {
            "id": f"meal_{i+1}",
            "date": date.isoformat(),
            "meal_type": meal["type"],
            "description": meal["name"],
            "calories": meal["calories"],
            "protein_g": meal["protein"],
            "carbs_g": meal["carbs"],
            "fat_g": meal["fat"]
        }
        meal_logs.append(log)

    # Sort by date
    meal_logs.sort(key=lambda x: x["date"])

    # Save to JSON
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(meal_logs, f, indent=2)

    print(f"✅ Generated {num_meals} sample meal logs: {output_path}")
    return meal_logs


def generate_all_sample_data():
    """Generate all sample data"""
    print("🚀 Generating sample data for Wellness AI...\n")

    # Generate different EEG states
    generate_sample_eeg(
        "/home/user/Wellnessapp/data/raw/sample_eeg_stressed.csv",
        duration=10,
        mental_state="stressed"
    )
    generate_sample_eeg(
        "/home/user/Wellnessapp/data/raw/sample_eeg_relaxed.csv",
        duration=10,
        mental_state="relaxed"
    )
    generate_sample_eeg(
        "/home/user/Wellnessapp/data/raw/sample_eeg_focused.csv",
        duration=10,
        mental_state="focused"
    )

    # Generate user profiles
    generate_user_profiles()

    # Generate health metrics
    generate_health_metrics(num_days=30)

    # Generate meal logs
    generate_meal_logs(num_meals=30)

    print("\n✅ All sample data generated successfully!")
    print("\nYou can now test the system with:")
    print("  - EEG analysis: data/raw/sample_eeg_*.csv")
    print("  - User profiles: data/sample_users.json")
    print("  - Health metrics: data/sample_health_metrics.json")
    print("  - Meal logs: data/sample_meals.json")


if __name__ == "__main__":
    generate_all_sample_data()
