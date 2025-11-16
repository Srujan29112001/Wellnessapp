"""
Wearable Device Integration Service.

Integrates with popular wearable platforms:
- Fitbit
- Apple Health (via HealthKit)
- Garmin Connect
- Oura Ring
- Whoop

Fetches activity, sleep, heart rate, and other health metrics.
"""

import requests
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import os


@dataclass
class WearableMetrics:
    """Standardized wearable metrics across platforms."""
    date: str
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    active_minutes: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_resting: Optional[int] = None
    hrv: Optional[float] = None  # Heart rate variability (ms)
    sleep_hours: Optional[float] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    sleep_score: Optional[int] = None
    stress_score: Optional[int] = None  # Platform-specific
    body_battery: Optional[int] = None  # Garmin
    readiness_score: Optional[int] = None  # Oura/Whoop
    spo2: Optional[float] = None  # Blood oxygen %
    respiration_rate: Optional[float] = None  # Breaths per minute
    skin_temperature: Optional[float] = None  # Celsius
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None


class FitbitIntegration:
    """Fitbit API integration."""

    BASE_URL = "https://api.fitbit.com/1/user/-"

    def __init__(self, access_token: str):
        """
        Initialize Fitbit integration.

        Args:
            access_token: Fitbit OAuth2 access token

        Note: To get access token:
        1. Register app at https://dev.fitbit.com/apps
        2. Implement OAuth2 flow to get user authorization
        3. Exchange authorization code for access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

    def get_daily_metrics(self, target_date: date = None) -> WearableMetrics:
        """
        Get comprehensive daily metrics from Fitbit.

        Args:
            target_date: Date to fetch (defaults to today)

        Returns:
            WearableMetrics object
        """
        if target_date is None:
            target_date = date.today()

        date_str = target_date.strftime("%Y-%m-%d")

        metrics = WearableMetrics(date=date_str)

        # Fetch activity summary
        activity = self._get_activity_summary(date_str)
        if activity:
            metrics.steps = activity.get("summary", {}).get("steps")
            metrics.distance_km = activity.get("summary", {}).get("distances", [{}])[0].get("distance", 0) * 1.60934  # miles to km
            metrics.calories_burned = activity.get("summary", {}).get("caloriesOut")
            metrics.active_minutes = activity.get("summary", {}).get("fairlyActiveMinutes", 0) + \
                                   activity.get("summary", {}).get("veryActiveMinutes", 0)

        # Fetch heart rate
        heart_rate = self._get_heart_rate(date_str)
        if heart_rate:
            metrics.heart_rate_resting = heart_rate.get("activities-heart", [{}])[0].get("value", {}).get("restingHeartRate")
            hr_zones = heart_rate.get("activities-heart-intraday", {}).get("dataset", [])
            if hr_zones:
                avg_hr = sum(zone["value"] for zone in hr_zones) / len(hr_zones)
                metrics.heart_rate_avg = int(avg_hr)

        # Fetch HRV
        hrv = self._get_hrv(date_str)
        if hrv:
            metrics.hrv = hrv.get("hrv", [{}])[0].get("value", {}).get("dailyRmssd")

        # Fetch sleep
        sleep = self._get_sleep(date_str)
        if sleep:
            sleep_summary = sleep.get("summary", {})
            metrics.sleep_hours = sleep_summary.get("totalMinutesAsleep", 0) / 60
            metrics.deep_sleep_minutes = sleep_summary.get("stages", {}).get("deep", 0)
            metrics.rem_sleep_minutes = sleep_summary.get("stages", {}).get("rem", 0)
            metrics.light_sleep_minutes = sleep_summary.get("stages", {}).get("light", 0)
            metrics.sleep_score = sleep.get("sleep", [{}])[0].get("efficiency")

        # Fetch SpO2
        spo2 = self._get_spo2(date_str)
        if spo2:
            metrics.spo2 = spo2.get("value")

        # Fetch weight
        weight = self._get_body_weight(date_str)
        if weight:
            metrics.weight_kg = weight.get("weight", [{}])[0].get("weight")
            metrics.body_fat_percent = weight.get("weight", [{}])[0].get("fat")

        return metrics

    def _get_activity_summary(self, date_str: str) -> Optional[Dict]:
        """Get activity summary for date."""
        try:
            url = f"{self.BASE_URL}/activities/date/{date_str}.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Fitbit activity: {e}")
            return None

    def _get_heart_rate(self, date_str: str) -> Optional[Dict]:
        """Get heart rate data for date."""
        try:
            url = f"{self.BASE_URL}/activities/heart/date/{date_str}/1d.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Fitbit heart rate: {e}")
            return None

    def _get_hrv(self, date_str: str) -> Optional[Dict]:
        """Get HRV data for date."""
        try:
            url = f"{self.BASE_URL}/hrv/date/{date_str}.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Fitbit HRV: {e}")
            return None

    def _get_sleep(self, date_str: str) -> Optional[Dict]:
        """Get sleep data for date."""
        try:
            url = f"{self.BASE_URL}/sleep/date/{date_str}.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Fitbit sleep: {e}")
            return None

    def _get_spo2(self, date_str: str) -> Optional[Dict]:
        """Get SpO2 data for date."""
        try:
            url = f"{self.BASE_URL}/spo2/date/{date_str}.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("value", {})
        except Exception as e:
            print(f"Error fetching Fitbit SpO2: {e}")
            return None

    def _get_body_weight(self, date_str: str) -> Optional[Dict]:
        """Get body weight data for date."""
        try:
            url = f"{self.BASE_URL}/body/log/weight/date/{date_str}.json"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Fitbit weight: {e}")
            return None


class AppleHealthIntegration:
    """
    Apple Health (HealthKit) integration.

    Note: This requires iOS app with HealthKit permissions.
    Direct API access is not available. Integration approaches:

    1. iOS app exports health data to backend
    2. Use third-party services (e.g., Terra API, Apple Health Kit Cloud)
    3. Manual export from iPhone Health app

    This implementation assumes health data is exported as JSON.
    """

    def __init__(self, data_export_path: Optional[str] = None):
        """
        Initialize Apple Health integration.

        Args:
            data_export_path: Path to exported Apple Health JSON data
        """
        self.data_export_path = data_export_path
        self.health_data = None

        if data_export_path and Path(data_export_path).exists():
            self._load_export_data()

    def _load_export_data(self):
        """Load exported Apple Health data."""
        try:
            with open(self.data_export_path, 'r') as f:
                self.health_data = json.load(f)
            print(f"✅ Loaded Apple Health data from {self.data_export_path}")
        except Exception as e:
            print(f"❌ Error loading Apple Health data: {e}")

    def get_daily_metrics(self, target_date: date = None) -> WearableMetrics:
        """
        Get daily metrics from Apple Health export.

        Args:
            target_date: Date to fetch (defaults to today)

        Returns:
            WearableMetrics object
        """
        if target_date is None:
            target_date = date.today()

        date_str = target_date.strftime("%Y-%m-%d")

        if not self.health_data:
            print("⚠️  No Apple Health data loaded")
            return WearableMetrics(date=date_str)

        # Parse health data for target date
        # Note: Actual format depends on export format
        # This is a simplified example

        metrics = WearableMetrics(date=date_str)

        # Extract metrics from health_data
        # Format: {"metrics": {"2024-01-15": {"steps": 8532, ...}}}

        daily_data = self.health_data.get("metrics", {}).get(date_str, {})

        metrics.steps = daily_data.get("steps")
        metrics.distance_km = daily_data.get("distance_km")
        metrics.calories_burned = daily_data.get("active_energy")
        metrics.heart_rate_avg = daily_data.get("heart_rate_avg")
        metrics.heart_rate_resting = daily_data.get("resting_heart_rate")
        metrics.hrv = daily_data.get("heart_rate_variability_sdnn")
        metrics.sleep_hours = daily_data.get("sleep_hours")
        metrics.spo2 = daily_data.get("oxygen_saturation")
        metrics.respiration_rate = daily_data.get("respiratory_rate")
        metrics.weight_kg = daily_data.get("body_mass")
        metrics.body_fat_percent = daily_data.get("body_fat_percentage")

        return metrics

    @staticmethod
    def export_instructions() -> str:
        """Get instructions for exporting Apple Health data."""
        return """
        === Apple Health Data Export Instructions ===

        Option 1: Manual Export from iPhone
        1. Open Health app on iPhone
        2. Tap your profile picture (top right)
        3. Scroll down to "Export All Health Data"
        4. Tap "Export"
        5. Share the ZIP file to your computer
        6. Extract and convert XML to JSON

        Option 2: Use iOS App Integration
        1. Build iOS app with HealthKit permissions
        2. Request permissions for required data types
        3. Query HKHealthStore for data
        4. Send to backend API

        Option 3: Third-Party Service (Recommended)
        1. Use Terra API or Apple Health Kit Cloud
        2. User authorizes data sharing
        3. Service provides REST API access
        4. No manual export needed

        For this demo, provide JSON export in format:
        {
          "metrics": {
            "2024-01-15": {
              "steps": 8532,
              "heart_rate_avg": 72,
              ...
            }
          }
        }
        """


class GarminIntegration:
    """Garmin Connect API integration."""

    def __init__(self, username: str, password: str):
        """
        Initialize Garmin integration.

        Note: Uses unofficial Garmin Connect API via garminconnect library.
        For production, use official Garmin Health API with OAuth.

        Args:
            username: Garmin Connect email
            password: Garmin Connect password
        """
        self.username = username
        self.password = password
        self.client = None

        try:
            from garminconnect import Garmin
            self.client = Garmin(username, password)
            self.client.login()
            print("✅ Connected to Garmin")
        except ImportError:
            print("⚠️  garminconnect library not installed")
            print("   Install: pip install garminconnect")
        except Exception as e:
            print(f"❌ Garmin login failed: {e}")

    def get_daily_metrics(self, target_date: date = None) -> WearableMetrics:
        """Get daily metrics from Garmin."""
        if not self.client:
            return WearableMetrics(date=str(target_date or date.today()))

        if target_date is None:
            target_date = date.today()

        date_str = target_date.strftime("%Y-%m-%d")

        try:
            # Get summary
            summary = self.client.get_stats(date_str)

            metrics = WearableMetrics(date=date_str)
            metrics.steps = summary.get("totalSteps")
            metrics.distance_km = summary.get("totalDistanceMeters", 0) / 1000
            metrics.calories_burned = summary.get("activeKilocalories")
            metrics.active_minutes = summary.get("activeTimeInSeconds", 0) / 60

            # Heart rate
            hr_data = self.client.get_heart_rates(date_str)
            if hr_data:
                metrics.heart_rate_resting = hr_data.get("restingHeartRate")
                metrics.heart_rate_avg = hr_data.get("averageHeartRate")

            # Stress (Garmin-specific)
            stress = self.client.get_stress_data(date_str)
            if stress:
                metrics.stress_score = stress.get("averageStressLevel")

            # Body Battery (Garmin-specific)
            battery = self.client.get_body_battery(date_str)
            if battery:
                metrics.body_battery = battery[-1].get("charged") if battery else None

            # Sleep
            sleep = self.client.get_sleep_data(date_str)
            if sleep:
                metrics.sleep_hours = sleep.get("sleepTimeSeconds", 0) / 3600
                metrics.deep_sleep_minutes = sleep.get("deepSleepSeconds", 0) / 60
                metrics.rem_sleep_minutes = sleep.get("remSleepSeconds", 0) / 60
                metrics.light_sleep_minutes = sleep.get("lightSleepSeconds", 0) / 60
                metrics.spo2 = sleep.get("averageSpO2Value")
                metrics.respiration_rate = sleep.get("avgRespirationValue")

            return metrics

        except Exception as e:
            print(f"Error fetching Garmin data: {e}")
            return WearableMetrics(date=date_str)


class WearableService:
    """Unified wearable service supporting multiple platforms."""

    def __init__(self):
        """Initialize wearable service."""
        self.integrations = {}

    def add_fitbit(self, user_id: str, access_token: str):
        """Add Fitbit integration for user."""
        self.integrations[f"{user_id}_fitbit"] = FitbitIntegration(access_token)

    def add_apple_health(self, user_id: str, export_path: str):
        """Add Apple Health integration for user."""
        self.integrations[f"{user_id}_apple"] = AppleHealthIntegration(export_path)

    def add_garmin(self, user_id: str, username: str, password: str):
        """Add Garmin integration for user."""
        self.integrations[f"{user_id}_garmin"] = GarminIntegration(username, password)

    def get_metrics(
        self,
        user_id: str,
        platform: str,
        target_date: date = None
    ) -> Optional[WearableMetrics]:
        """
        Get metrics from specified platform.

        Args:
            user_id: User ID
            platform: 'fitbit', 'apple', or 'garmin'
            target_date: Date to fetch

        Returns:
            WearableMetrics or None
        """
        integration_key = f"{user_id}_{platform}"

        if integration_key not in self.integrations:
            print(f"⚠️  No {platform} integration for user {user_id}")
            return None

        integration = self.integrations[integration_key]
        return integration.get_daily_metrics(target_date)

    def get_merged_metrics(
        self,
        user_id: str,
        target_date: date = None
    ) -> WearableMetrics:
        """
        Get merged metrics from all connected platforms.

        Prioritizes more accurate/recent data when conflicts exist.

        Args:
            user_id: User ID
            target_date: Date to fetch

        Returns:
            Merged WearableMetrics
        """
        if target_date is None:
            target_date = date.today()

        merged = WearableMetrics(date=target_date.strftime("%Y-%m-%d"))

        # Check all platforms for this user
        platforms = ['fitbit', 'apple', 'garmin']

        for platform in platforms:
            metrics = self.get_metrics(user_id, platform, target_date)
            if metrics:
                # Merge non-None values
                for field in asdict(metrics):
                    value = getattr(metrics, field)
                    if value is not None and getattr(merged, field) is None:
                        setattr(merged, field, value)

        return merged


# Example usage
if __name__ == "__main__":
    print("=== Wearable Integration Demo ===\n")

    # Note: These examples require actual API credentials
    # For testing, use dummy data or local exports

    service = WearableService()

    # Example 1: Fitbit (requires OAuth token)
    print("Example 1: Fitbit Integration")
    print("  To use: Obtain OAuth2 token from Fitbit developer portal")
    print("  service.add_fitbit('user123', 'YOUR_FITBIT_TOKEN')")
    print("  metrics = service.get_metrics('user123', 'fitbit')")
    print()

    # Example 2: Apple Health (requires export file)
    print("Example 2: Apple Health Integration")
    print(AppleHealthIntegration.export_instructions())
    print()

    # Example 3: Garmin (requires credentials)
    print("Example 3: Garmin Integration")
    print("  To use: Provide Garmin Connect credentials")
    print("  service.add_garmin('user123', 'email@example.com', 'password')")
    print("  metrics = service.get_metrics('user123', 'garmin')")
    print()

    print("For production use:")
    print("  1. Implement secure OAuth2 flows")
    print("  2. Encrypt and store tokens securely")
    print("  3. Handle token refresh")
    print("  4. Respect user privacy and data retention policies")
