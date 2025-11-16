"""
Generate Sample Data for Demo

Creates realistic sample data for:
- EEG recordings
- Health metrics
- Voice recordings
- Food images
"""
import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta


def generate_eeg_sample():
    """Generate sample EEG data CSV"""
    print("Generating sample EEG data...")

    # Simulate 14-channel, 10-second EEG at 256 Hz
    channels = 14
    duration = 10  # seconds
    sample_rate = 256
    samples = duration * sample_rate

    time = np.linspace(0, duration, samples)
    eeg_data = []

    for ch in range(channels):
        # Mix of frequency components (simulating brain rhythms)
        signal = (
            np.sin(2 * np.pi * 2 * time) * 0.3 +   # Delta (2 Hz)
            np.sin(2 * np.pi * 6 * time) * 0.4 +   # Theta (6 Hz)
            np.sin(2 * np.pi * 10 * time) * 0.5 +  # Alpha (10 Hz)
            np.sin(2 * np.pi * 20 * time) * 0.6 +  # Beta (20 Hz) - stress indicator
            np.random.randn(samples) * 0.1          # Noise
        )
        eeg_data.append(signal)

    # Save to CSV
    output_dir = Path("data/raw/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    eeg_df = pd.DataFrame(np.array(eeg_data).T)
    eeg_path = output_dir / "sample_eeg.csv"
    eeg_df.to_csv(eeg_path, index=False, header=False)

    print(f"✓ Sample EEG data saved to {eeg_path}")
    return str(eeg_path)


def generate_health_metrics():
    """Generate sample health metrics"""
    print("Generating sample health metrics...")

    # Generate 30 days of data
    days = 30
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]

    data = []
    for date in dates:
        # Realistic patterns
        sleep_hours = np.random.normal(7, 1.5)  # Average 7 hours
        sleep_hours = max(4, min(10, sleep_hours))  # Clamp

        steps = np.random.normal(7000, 2000)  # Average 7k steps
        steps = max(0, int(steps))

        stress_level = np.random.uniform(3, 8)  # 1-10 scale

        # Correlation: less sleep -> more stress
        if sleep_hours < 6:
            stress_level += 2

        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "sleep_hours": round(sleep_hours, 1),
            "steps": steps,
            "stress_level": round(stress_level, 1),
            "heart_rate": int(np.random.normal(70, 10)),
            "weight_lbs": round(np.random.normal(150, 2), 1)
        })

    output_dir = Path("data/raw/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = output_dir / "health_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Sample health metrics saved to {metrics_path}")
    return str(metrics_path)


def generate_user_profile():
    """Generate sample user profile"""
    print("Generating sample user profile...")

    profile = {
        "user_id": "demo_user",
        "name": "Alex Johnson",
        "age": 28,
        "gender": "Female",
        "dosha": "Vata-Pitta",
        "health_goals": [
            "Reduce stress and anxiety",
            "Improve sleep quality",
            "Increase energy levels"
        ],
        "medical_conditions": [],
        "current_medications": [],
        "allergies": [],
        "dietary_preferences": "Vegetarian",
        "activity_level": "Moderate",
        "created_at": datetime.now().isoformat()
    }

    output_dir = Path("data/raw/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_path = output_dir / "user_profile.json"
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)

    print(f"✓ Sample user profile saved to {profile_path}")
    return str(profile_path)


def create_readme():
    """Create README for sample data"""
    readme_content = """# Sample Data for Wellness AI Demo

This directory contains sample data for testing and demonstration:

## Files

1. **sample_eeg.csv**
   - 14-channel EEG recording
   - 10 seconds duration at 256 Hz
   - Contains mixed frequency components (delta, theta, alpha, beta)
   - Use this to test EEG analysis endpoints

2. **health_metrics.json**
   - 30 days of health data
   - Includes: sleep, steps, stress, heart rate, weight
   - Realistic patterns with correlations (e.g., poor sleep → high stress)
   - Use this to test health tracking and recommendations

3. **user_profile.json**
   - Demo user profile
   - Includes Ayurvedic dosha type, health goals, preferences
   - Use this for personalized recommendations

## Usage

### Upload EEG Data
```bash
curl -X POST "http://localhost:8000/api/v1/eeg/upload" \\
  -F "file=@data/raw/sample_data/sample_eeg.csv"
```

### View in UI
1. Start the application (see QUICKSTART.md)
2. Navigate to "🧠 EEG Analysis" page
3. Upload `sample_eeg.csv`
4. View mental state analysis

### Chat with AI Coach
1. Go to "💬 AI Coach" page
2. Ask: "I feel stressed and anxious"
3. The coach will reference your EEG data and provide personalized advice

## Generating More Data

Run this script again to generate fresh sample data:
```bash
python scripts/generate_sample_data.py
```
"""

    readme_path = Path("data/raw/sample_data/README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"✓ README created at {readme_path}")


def main():
    """Generate all sample data"""
    print("\n" + "="*60)
    print("Generating Sample Data for Wellness AI")
    print("="*60 + "\n")

    # Generate data
    eeg_path = generate_eeg_sample()
    metrics_path = generate_health_metrics()
    profile_path = generate_user_profile()
    create_readme()

    print("\n" + "="*60)
    print("✓ Sample data generation complete!")
    print("="*60)
    print("\nGenerated files:")
    print(f"  - {eeg_path}")
    print(f"  - {metrics_path}")
    print(f"  - {profile_path}")
    print("\nYou can now use this data to test the system.")
    print("See data/raw/sample_data/README.md for usage instructions.\n")


if __name__ == "__main__":
    main()
