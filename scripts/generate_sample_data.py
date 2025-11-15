"""
Generate Sample Data for Testing

Creates:
- Sample EEG data files (CSV format)
- Sample user profiles
- Sample health metrics
- Sample knowledge base entries
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json


def generate_eeg_sample(
    duration_seconds: int = 60,
    sample_rate: int = 256,
    num_channels: int = 14,
    mental_state: str = "relaxed"
) -> pd.DataFrame:
    """
    Generate synthetic EEG data

    Args:
        duration_seconds: Recording duration
        sample_rate: Samples per second
        num_channels: Number of EEG channels
        mental_state: Target mental state (relaxed, stressed, focused, drowsy)

    Returns:
        DataFrame with EEG data
    """
    num_samples = duration_seconds * sample_rate

    # Time axis
    t = np.linspace(0, duration_seconds, num_samples)

    # Initialize data
    data = {}
    data['timestamp'] = t

    # Channel names (standard 10-20 system)
    channel_names = [
        'AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1',
        'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4'
    ][:num_channels]

    # Generate signals based on mental state
    for i, channel in enumerate(channel_names):
        signal = np.zeros(num_samples)

        if mental_state == "relaxed":
            # Dominant alpha (8-13 Hz)
            signal += 50 * np.sin(2 * np.pi * 10 * t + np.random.rand())
            # Some theta
            signal += 20 * np.sin(2 * np.pi * 6 * t + np.random.rand())
            # Low beta
            signal += 15 * np.sin(2 * np.pi * 18 * t + np.random.rand())

        elif mental_state == "stressed":
            # High beta (18-30 Hz)
            signal += 60 * np.sin(2 * np.pi * 25 * t + np.random.rand())
            signal += 40 * np.sin(2 * np.pi * 20 * t + np.random.rand())
            # Low alpha
            signal += 20 * np.sin(2 * np.pi * 10 * t + np.random.rand())

        elif mental_state == "focused":
            # Beta (13-30 Hz) + some alpha
            signal += 45 * np.sin(2 * np.pi * 18 * t + np.random.rand())
            signal += 35 * np.sin(2 * np.pi * 12 * t + np.random.rand())
            signal += 25 * np.sin(2 * np.pi * 22 * t + np.random.rand())

        elif mental_state == "drowsy":
            # Dominant theta (4-8 Hz) + delta
            signal += 55 * np.sin(2 * np.pi * 6 * t + np.random.rand())
            signal += 40 * np.sin(2 * np.pi * 3 * t + np.random.rand())
            # Low alpha
            signal += 15 * np.sin(2 * np.pi * 10 * t + np.random.rand())

        # Add noise
        noise = np.random.normal(0, 5, num_samples)
        signal += noise

        # Add occasional artifacts
        artifact_positions = np.random.choice(
            num_samples,
            size=int(num_samples * 0.01),
            replace=False
        )
        signal[artifact_positions] += np.random.normal(0, 30, len(artifact_positions))

        data[channel] = signal

    return pd.DataFrame(data)


def generate_sample_eeg_files():
    """Generate sample EEG files for different mental states"""
    output_dir = Path("/home/user/Wellnessapp/data/sample_eeg")
    output_dir.mkdir(parents=True, exist_ok=True)

    states = ["relaxed", "stressed", "focused", "drowsy"]

    for state in states:
        print(f"Generating {state} EEG data...")

        df = generate_eeg_sample(
            duration_seconds=60,
            sample_rate=256,
            num_channels=14,
            mental_state=state
        )

        filename = output_dir / f"eeg_sample_{state}.csv"
        df.to_csv(filename, index=False)

        print(f"  Saved to {filename}")

    # Also create a mixed state sample
    print("Generating mixed state EEG data...")
    df1 = generate_eeg_sample(duration_seconds=30, mental_state="focused")
    df2 = generate_eeg_sample(duration_seconds=30, mental_state="stressed")

    # Concatenate
    df2['timestamp'] = df2['timestamp'] + 30
    df_mixed = pd.concat([df1, df2], ignore_index=True)

    filename = output_dir / "eeg_sample_mixed.csv"
    df_mixed.to_csv(filename, index=False)
    print(f"  Saved to {filename}")


def generate_sample_health_metrics():
    """Generate sample health metrics data"""
    output_dir = Path("/home/user/Wellnessapp/data/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate 30 days of data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

    metrics = []

    for i, date in enumerate(dates):
        # Simulate improving trend
        baseline_sleep = 6.0 + (i / 30) * 1.5  # Improving from 6 to 7.5 hours
        baseline_stress = 0.7 - (i / 30) * 0.3  # Decreasing from 0.7 to 0.4

        metric = {
            "date": date.strftime("%Y-%m-%d"),
            "steps": int(np.random.normal(8000, 2000)),
            "sleep_hours": round(baseline_sleep + np.random.normal(0, 0.5), 1),
            "heart_rate_avg": int(np.random.normal(70, 10)),
            "heart_rate_resting": int(np.random.normal(60, 5)),
            "stress_level": round(baseline_stress + np.random.normal(0, 0.1), 2),
            "mood_score": round(5 + (i / 30) * 2 + np.random.normal(0, 0.5), 1),
            "energy_level": round(5 + (i / 30) * 2 + np.random.normal(0, 0.5), 1),
            "weight_kg": round(70 + np.random.normal(0, 0.5), 1)
        }

        metrics.append(metric)

    df = pd.DataFrame(metrics)
    filename = output_dir / "sample_health_metrics.csv"
    df.to_csv(filename, index=False)

    print(f"Generated health metrics: {filename}")


def generate_sample_journal_entries():
    """Generate sample journal entries"""
    output_dir = Path("/home/user/Wellnessapp/data/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    dates = pd.date_range(end=datetime.now(), periods=14, freq='D')

    journal_texts = [
        "Feeling anxious about work deadlines. Tried breathing exercises which helped a bit.",
        "Slept really well last night! Feeling energized and positive today.",
        "Had trouble focusing today. Maybe need to cut back on coffee.",
        "Meditation session was very calming. Should do this more often.",
        "Feeling stressed but yoga practice helped me feel grounded.",
        "Great day! Accomplished a lot and feeling proud of myself.",
        "Low energy today. Going to bed early tonight.",
        "Started taking magnesium supplement. Hope it helps with sleep.",
        "Noticed I'm less anxious when I maintain regular sleep schedule.",
        "Grateful for supportive friends and family.",
        "Feeling overwhelmed but taking it one step at a time.",
        "Exercise really boosted my mood today!",
        "Trying to be more mindful and present. It's helping.",
        "Feeling balanced and content today."
    ]

    for date, text in zip(dates, journal_texts):
        entry = {
            "date": date.strftime("%Y-%m-%d"),
            "mood": np.random.choice(["anxious", "calm", "happy", "stressed", "neutral"]),
            "entry": text,
            "gratitude": [
                np.random.choice([
                    "Family",
                    "Health",
                    "Nature",
                    "Work",
                    "Friends",
                    "Learning"
                ])
            ]
        }
        entries.append(entry)

    with open(output_dir / "sample_journal_entries.json", 'w') as f:
        json.dump(entries, f, indent=2)

    print(f"Generated journal entries: {output_dir / 'sample_journal_entries.json'}")


def generate_sample_user_profile():
    """Generate sample user profile"""
    output_dir = Path("/home/user/Wellnessapp/data/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    profile = {
        "user_id": "demo_user",
        "email": "demo@wellnessai.com",
        "name": "Alex Johnson",
        "age": 32,
        "gender": "non-binary",
        "dosha_type": "vata_pitta",
        "health_goals": [
            "Reduce stress and anxiety",
            "Improve sleep quality",
            "Boost energy levels",
            "Maintain healthy weight"
        ],
        "dietary_restrictions": ["vegetarian", "gluten-sensitive"],
        "medical_conditions": [],
        "current_medications": [],
        "allergies": ["peanuts"],
        "preferences": {
            "notification_preferences": {
                "proactive_check_ins": True,
                "daily_summary": True,
                "achievement_alerts": True
            },
            "privacy_settings": {
                "data_retention_days": 365,
                "share_anonymized_data": False
            },
            "interface_preferences": {
                "theme": "light",
                "language": "en",
                "units": "metric"
            }
        }
    }

    with open(output_dir / "sample_user_profile.json", 'w') as f:
        json.dump(profile, f, indent=2)

    print(f"Generated user profile: {output_dir / 'sample_user_profile.json'}")


def main():
    """Generate all sample data"""
    print("=" * 60)
    print("Generating Sample Data for Wellness AI Platform")
    print("=" * 60)
    print()

    generate_sample_eeg_files()
    print()

    generate_sample_health_metrics()
    print()

    generate_sample_journal_entries()
    print()

    generate_sample_user_profile()
    print()

    print("=" * 60)
    print("Sample data generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
