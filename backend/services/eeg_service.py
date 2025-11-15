"""
EEG Analysis Service

High-level service for EEG data processing and analysis
"""
import numpy as np
from typing import Dict, Optional
import logging
from datetime import datetime

from ml.eeg_analysis.processor import EEGProcessor
from ml.eeg_analysis.classifier import EEGMentalStateClassifier
from ml.eeg_analysis.snn_classifier import SNNMentalStateClassifier
from config.settings import settings

logger = logging.getLogger(__name__)


class EEGService:
    """
    Service for EEG data analysis

    Handles end-to-end pipeline from raw EEG data to mental state classification
    """

    def __init__(self, use_snn: bool = False):
        """
        Initialize EEG service

        Args:
            use_snn: Whether to use Spiking Neural Network (True) or traditional ANN (False)
        """
        # Initialize processor
        self.processor = EEGProcessor(
            sample_rate=settings.EEG_SAMPLE_RATE,
            num_channels=settings.EEG_CHANNELS
        )

        # Initialize classifier
        self.use_snn = use_snn
        if use_snn:
            logger.info("Using Spiking Neural Network for EEG classification")
            self.classifier = SNNMentalStateClassifier(
                model_path=settings.EEG_MODEL_PATH.replace('.pt', '_snn.pt') if settings.EEG_MODEL_PATH else None
            )
        else:
            logger.info("Using traditional ANN for EEG classification")
            self.classifier = EEGMentalStateClassifier(
                model_path=settings.EEG_MODEL_PATH if settings.EEG_MODEL_PATH else None
            )

    def analyze_eeg_file(self, file_path: str, user_id: str) -> Dict:
        """
        Analyze EEG data from file

        Args:
            file_path: Path to CSV file with EEG data
            user_id: User ID

        Returns:
            Analysis results
        """
        try:
            # Load data
            raw_data = EEGProcessor.load_csv(file_path)

            # Analyze
            return self.analyze_eeg_data(raw_data, user_id)

        except Exception as e:
            logger.error(f"Error analyzing EEG file: {e}", exc_info=True)
            raise

    def analyze_eeg_data(self, raw_data: np.ndarray, user_id: str) -> Dict:
        """
        Analyze raw EEG data

        Args:
            raw_data: Raw EEG data (channels x samples)
            user_id: User ID

        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info(f"Analyzing EEG data for user {user_id}")

            # Process EEG
            analysis_results = self.processor.analyze(raw_data)

            # Extract features
            features = analysis_results['features']

            # Classify mental state
            classification = self.classifier.predict(features)

            # Combine results
            results = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'mental_state': classification['mental_state'],
                'confidence': classification['confidence'],

                # Probabilities
                'stress': classification['stress'],
                'focus': classification['focus'],
                'relaxation': classification['relaxation'],
                'drowsiness': classification['drowsiness'],

                # Band powers
                'band_powers': analysis_results['band_powers'],
                'relative_powers': analysis_results['relative_powers'],
                'dominant_band': analysis_results['dominant_band'],

                # Recommendations
                'recommendations': self._generate_recommendations(classification, analysis_results),

                # Metadata
                'classifier_type': 'SNN' if self.use_snn else 'ANN',
                'duration_seconds': raw_data.shape[1] / settings.EEG_SAMPLE_RATE,
                'channels_analyzed': raw_data.shape[0],
                'sample_rate': settings.EEG_SAMPLE_RATE
            }

            logger.info(f"EEG analysis complete: {results['mental_state']} (confidence: {results['confidence']:.2f})")

            return results

        except Exception as e:
            logger.error(f"Error in EEG analysis: {e}", exc_info=True)
            raise

    def _generate_recommendations(self, classification: Dict, analysis: Dict) -> list:
        """
        Generate recommendations based on EEG analysis

        Args:
            classification: Classification results
            analysis: Full analysis results

        Returns:
            List of recommendations
        """
        recommendations = []
        mental_state = classification['mental_state']
        stress_level = classification['stress']
        focus_level = classification['focus']
        dominant_band = analysis['dominant_band']

        # Stress recommendations
        if stress_level > 0.6:
            recommendations.append(
                "High stress detected. Consider a 5-10 minute breathing exercise to activate the parasympathetic nervous system."
            )
            recommendations.append(
                "Your beta wave activity is elevated. Try meditation to promote alpha wave activity and relaxation."
            )

        # Focus recommendations
        if focus_level < 0.4 and mental_state != 'drowsy':
            recommendations.append(
                "Focus levels are below optimal. Consider taking a short break or trying a brief mindfulness exercise."
            )

        # Drowsiness recommendations
        if classification['drowsiness'] > 0.5:
            recommendations.append(
                "High drowsiness detected. If possible, take a 15-20 minute nap or get some physical activity."
            )
            recommendations.append(
                "Elevated delta/theta waves suggest low alertness. Ensure adequate sleep tonight."
            )

        # Band-specific recommendations
        if dominant_band == 'beta' and stress_level > 0.5:
            recommendations.append(
                "Dominant beta activity with stress indicates mental overactivity. Progressive muscle relaxation may help."
            )
        elif dominant_band == 'alpha':
            recommendations.append(
                "Good alpha wave activity detected. You're in a relaxed yet alert state - ideal for creative work."
            )

        # General wellness
        if len(recommendations) == 0:
            recommendations.append(
                "Your brainwave patterns look balanced. Maintain your current wellness practices."
            )

        return recommendations

    async def store_analysis(self, results: Dict, raw_data: Optional[np.ndarray] = None):
        """
        Store EEG analysis results in database

        Args:
            results: Analysis results
            raw_data: Optional raw EEG data to store

        Returns:
            Stored record IDs
        """
        # TODO: Implement database storage
        # 1. Store analysis in PostgreSQL (EEGAnalysis table)
        # 2. Optionally store raw data in MongoDB
        # 3. Update user's daily stress/focus metrics in HealthMetric

        pass
