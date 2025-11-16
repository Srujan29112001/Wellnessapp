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

    async def store_analysis(self, db, results: Dict, raw_data: Optional[np.ndarray] = None):
        """
        Store EEG analysis results in database

        Args:
            db: Database session
            results: Analysis results
            raw_data: Optional raw EEG data to store

        Returns:
            Stored record IDs
        """
        from backend.models.postgres_models import EEGAnalysis, MentalState, HealthMetric
        from backend.models.mongo_schemas import COLLECTION_EEG_RAW_DATA
        from backend.database.mongo import get_collection
        from sqlalchemy import select
        from datetime import date

        mongo_data_id = None

        # Store raw data in MongoDB if provided
        if raw_data is not None:
            mongo_collection = get_collection(COLLECTION_EEG_RAW_DATA)
            raw_data_doc = {
                "user_id": results['user_id'],
                "timestamp": datetime.now(),
                "channels": raw_data.tolist(),
                "channel_names": [f"CH{i+1}" for i in range(raw_data.shape[0])],
                "sample_rate": results['sample_rate'],
                "duration_seconds": results['duration_seconds'],
                "session_id": None
            }
            mongo_result = await mongo_collection.insert_one(raw_data_doc)
            mongo_data_id = str(mongo_result.inserted_id)

        # Map mental state string to enum
        state_mapping = {
            'stressed': MentalState.STRESSED,
            'focused': MentalState.FOCUSED,
            'relaxed': MentalState.RELAXED,
            'drowsy': MentalState.DROWSY,
            'anxious': MentalState.ANXIOUS
        }
        mental_state_enum = state_mapping.get(results['mental_state'].lower(), MentalState.STRESSED)

        # Store analysis in PostgreSQL
        analysis = EEGAnalysis(
            user_id=results['user_id'],
            timestamp=datetime.now(),
            mental_state=mental_state_enum,
            stress_level=results['stress'],
            focus_level=results['focus'],
            relaxation_level=results['relaxation'],
            drowsiness_level=results['drowsiness'],
            delta_power=results['band_powers'].get('delta'),
            theta_power=results['band_powers'].get('theta'),
            alpha_power=results['band_powers'].get('alpha'),
            beta_power=results['band_powers'].get('beta'),
            gamma_power=results['band_powers'].get('gamma'),
            dominant_band=results['dominant_band'],
            mongo_data_id=mongo_data_id,
            duration_seconds=results['duration_seconds'],
            channels_used=results['channels_analyzed'],
            sample_rate=results['sample_rate']
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        # Update today's health metric with stress/focus levels
        today = date.today()
        stmt = select(HealthMetric).where(
            HealthMetric.user_id == results['user_id'],
            HealthMetric.date == today
        )
        result = await db.execute(stmt)
        health_metric = result.scalar_one_or_none()

        if health_metric:
            # Update existing metric
            health_metric.stress_level = results['stress']
            health_metric.focus_level = results['focus']
            await db.commit()
        else:
            # Create new metric for today
            health_metric = HealthMetric(
                user_id=results['user_id'],
                date=today,
                stress_level=results['stress'],
                focus_level=results['focus']
            )
            db.add(health_metric)
            await db.commit()

        return {
            "analysis_id": analysis.id,
            "mongo_data_id": mongo_data_id
        }
