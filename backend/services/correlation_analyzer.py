"""
Advanced Correlation Analysis Engine
Finds patterns and correlations in user health data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import logging

logger = logging.getLogger(__name__)


class HealthCorrelationAnalyzer:
    """
    Analyzes correlations between different health metrics
    to provide insights and recommendations
    """

    def __init__(self):
        """Initialize correlation analyzer"""
        self.min_data_points = 7  # Minimum days of data needed

    async def analyze_user_data(
        self,
        user_health_data: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Comprehensive correlation analysis

        Args:
            user_health_data: DataFrame with columns:
                - date
                - sleep_hours
                - steps
                - stress_level (from EEG)
                - mood
                - calories
                - weight
                etc.

        Returns:
            Analysis results with correlations and insights
        """
        if len(user_health_data) < self.min_data_points:
            return {
                "success": False,
                "message": f"Need at least {self.min_data_points} days of data"
            }

        insights = {
            "correlations": {},
            "patterns": {},
            "predictions": {},
            "recommendations": []
        }

        # 1. Correlation Analysis
        correlations = self._calculate_correlations(user_health_data)
        insights["correlations"] = correlations

        # 2. Pattern Detection
        patterns = self._detect_patterns(user_health_data)
        insights["patterns"] = patterns

        # 3. Trend Analysis
        trends = self._analyze_trends(user_health_data)
        insights["trends"] = trends

        # 4. Generate Recommendations
        recommendations = self._generate_recommendations(
            correlations, patterns, trends
        )
        insights["recommendations"] = recommendations

        # 5. Predictions
        predictions = self._make_predictions(user_health_data)
        insights["predictions"] = predictions

        return {
            "success": True,
            "insights": insights,
            "data_points": len(user_health_data),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_correlations(
        self,
        data: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Calculate correlations between metrics

        Key correlations to analyze:
        - Sleep vs Stress
        - Sleep vs Mood
        - Exercise vs Sleep
        - Diet vs Energy
        """
        correlations = {}

        # Numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns

        # Correlation matrix
        corr_matrix = data[numeric_cols].corr()

        # Extract significant correlations
        significant = []

        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i < j:  # Avoid duplicates
                    corr = corr_matrix.loc[col1, col2]

                    # Check if significant (|r| > 0.3)
                    if abs(corr) > 0.3 and not np.isnan(corr):
                        # Calculate p-value
                        n = len(data)
                        t_stat = corr * np.sqrt((n - 2) / (1 - corr ** 2))
                        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))

                        significant.append({
                            "factor1": col1,
                            "factor2": col2,
                            "correlation": round(corr, 3),
                            "strength": self._correlation_strength(corr),
                            "direction": "positive" if corr > 0 else "negative",
                            "p_value": round(p_value, 4),
                            "significant": p_value < 0.05
                        })

        correlations["significant_pairs"] = sorted(
            significant,
            key=lambda x: abs(x["correlation"]),
            reverse=True
        )

        # Key insights
        correlations["key_insights"] = self._extract_key_insights(significant)

        return correlations

    def _correlation_strength(self, r: float) -> str:
        """Classify correlation strength"""
        abs_r = abs(r)
        if abs_r >= 0.7:
            return "strong"
        elif abs_r >= 0.4:
            return "moderate"
        elif abs_r >= 0.2:
            return "weak"
        else:
            return "negligible"

    def _extract_key_insights(self, correlations: List[Dict]) -> List[str]:
        """Extract human-readable insights from correlations"""
        insights = []

        for corr in correlations[:5]:  # Top 5
            f1, f2 = corr["factor1"], corr["factor2"]
            strength = corr["strength"]
            direction = corr["direction"]

            if "sleep" in f1.lower() and "stress" in f2.lower():
                if direction == "negative":
                    insights.append(
                        f"More sleep is {strength}ly associated with lower stress levels"
                    )
                else:
                    insights.append(
                        f"Less sleep correlates with higher stress (investigate sleep quality)"
                    )

            elif "steps" in f1.lower() or "steps" in f2.lower():
                if direction == "positive":
                    insights.append(
                        f"{strength.title()} positive relationship: more physical activity improves {f2 if 'steps' in f1 else f1}"
                    )

            elif "mood" in f1.lower() or "mood" in f2.lower():
                other = f2 if "mood" in f1.lower() else f1
                insights.append(
                    f"Mood is {strength}ly {direction}ly correlated with {other}"
                )

        return insights

    def _detect_patterns(self, data: pd.DataFrame) -> Dict[str, any]:
        """Detect patterns in time series data"""
        patterns = {}

        # Weekly patterns
        if "date" in data.columns:
            data["day_of_week"] = pd.to_datetime(data["date"]).dt.dayofweek

            # Check if weekends differ from weekdays
            for col in ["sleep_hours", "steps", "stress_level"]:
                if col in data.columns:
                    weekday_data = data[data["day_of_week"] < 5][col]
                    weekend_data = data[data["day_of_week"] >= 5][col]

                    if len(weekday_data) > 0 and len(weekend_data) > 0:
                        t_stat, p_val = stats.ttest_ind(weekday_data, weekend_data)

                        if p_val < 0.05:
                            weekday_mean = weekday_data.mean()
                            weekend_mean = weekend_data.mean()
                            diff_pct = ((weekend_mean - weekday_mean) / weekday_mean) * 100

                            patterns[f"{col}_weekly"] = {
                                "weekday_avg": round(weekday_mean, 2),
                                "weekend_avg": round(weekend_mean, 2),
                                "difference_percent": round(diff_pct, 1),
                                "insight": f"{col.replace('_', ' ').title()} {'increases' if diff_pct > 0 else 'decreases'} by {abs(round(diff_pct, 1))}% on weekends"
                            }

        # Cyclical patterns (detect peaks/troughs)
        for col in ["stress_level", "mood", "energy"]:
            if col in data.columns and len(data[col]) > 7:
                values = data[col].values

                # Find peaks (high stress days, etc.)
                peaks, _ = find_peaks(values, distance=2)
                troughs, _ = find_peaks(-values, distance=2)

                if len(peaks) > 0:
                    patterns[f"{col}_peaks"] = {
                        "count": len(peaks),
                        "average_value": round(values[peaks].mean(), 2),
                        "days": peaks.tolist()[:5]  # First 5 peaks
                    }

        return patterns

    def _analyze_trends(self, data: pd.DataFrame) -> Dict[str, any]:
        """Analyze trends over time"""
        trends = {}

        # Linear trends
        for col in ["stress_level", "sleep_hours", "mood", "weight"]:
            if col in data.columns and len(data[col]) >= 7:
                x = np.arange(len(data))
                y = data[col].values

                # Remove NaN
                mask = ~np.isnan(y)
                if mask.sum() < 3:
                    continue

                x_clean = x[mask]
                y_clean = y[mask]

                # Linear regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)

                # Determine trend
                if p_value < 0.05:
                    if slope > 0:
                        direction = "increasing"
                    else:
                        direction = "decreasing"

                    # Calculate percent change
                    start_val = intercept
                    end_val = slope * len(data) + intercept
                    pct_change = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0

                    trends[col] = {
                        "direction": direction,
                        "slope": round(slope, 4),
                        "percent_change": round(pct_change, 1),
                        "confidence": round(r_value ** 2, 3),  # R-squared
                        "insight": f"{col.replace('_', ' ').title()} is {direction} by {abs(round(pct_change, 1))}% over time"
                    }

        return trends

    def _generate_recommendations(
        self,
        correlations: Dict,
        patterns: Dict,
        trends: Dict
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations"""
        recommendations = []

        # From correlations
        for insight in correlations.get("key_insights", []):
            if "sleep" in insight.lower() and "stress" in insight.lower():
                recommendations.append({
                    "category": "sleep",
                    "priority": "high",
                    "recommendation": "Prioritize 7-8 hours of sleep to reduce stress levels",
                    "evidence": insight
                })

            if "steps" in insight.lower() or "activity" in insight.lower():
                recommendations.append({
                    "category": "exercise",
                    "priority": "medium",
                    "recommendation": "Maintain regular physical activity for improved well-being",
                    "evidence": insight
                })

        # From trends
        for metric, trend_info in trends.items():
            if metric == "stress_level" and trend_info["direction"] == "increasing":
                recommendations.append({
                    "category": "stress_management",
                    "priority": "high",
                    "recommendation": "Stress levels are rising. Consider stress-reduction techniques (meditation, breathing exercises)",
                    "evidence": trend_info["insight"]
                })

            if metric == "sleep_hours" and trend_info["direction"] == "decreasing":
                recommendations.append({
                    "category": "sleep",
                    "priority": "high",
                    "recommendation": "Sleep duration is declining. Establish consistent sleep schedule",
                    "evidence": trend_info["insight"]
                })

        # From patterns
        for pattern_name, pattern_info in patterns.items():
            if "weekly" in pattern_name:
                recommendations.append({
                    "category": "lifestyle",
                    "priority": "low",
                    "recommendation": f"Maintain consistency: {pattern_info.get('insight', '')}",
                    "evidence": f"Weekend vs weekday difference detected"
                })

        return recommendations

    def _make_predictions(self, data: pd.DataFrame) -> Dict[str, any]:
        """Make simple predictions for next week"""
        predictions = {}

        # Predict stress level
        if "stress_level" in data.columns and len(data) >= 7:
            recent_stress = data["stress_level"].tail(7).mean()
            overall_stress = data["stress_level"].mean()

            predictions["stress_next_week"] = {
                "predicted_level": round(recent_stress, 2),
                "confidence": "medium",
                "trend": "increasing" if recent_stress > overall_stress else "stable",
                "recommendation": "Monitor and intervene if continues rising" if recent_stress > overall_stress else "Continue current practices"
            }

        return predictions


# Factory function
def create_correlation_analyzer() -> HealthCorrelationAnalyzer:
    """Create correlation analyzer instance"""
    return HealthCorrelationAnalyzer()
