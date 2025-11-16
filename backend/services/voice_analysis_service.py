"""
Voice Emotion Analysis Service

Analyzes voice recordings for emotion and stress detection
"""
import numpy as np
import librosa
from typing import Dict, Optional
import logging
from datetime import datetime

from backend.models.postgres_models import VoiceAnalysis
from backend.models.mongo_schemas import VoiceRecording, COLLECTION_VOICE_RECORDINGS
from backend.database.mongo import get_collection

logger = logging.getLogger(__name__)


class VoiceAnalysisService:
    """Service for voice emotion and stress analysis"""

    def __init__(self):
        """Initialize voice analysis service"""
        # In production, load a trained emotion detection model
        # For now, use feature-based heuristics
        self.sample_rate = 16000

    async def analyze_audio_file(
        self,
        db,
        user_id: str,
        audio_path: str,
        store_raw: bool = True
    ) -> Dict:
        """
        Analyze audio file for emotion and stress

        Args:
            db: Database session
            user_id: User ID
            audio_path: Path to audio file
            store_raw: Whether to store raw audio features in MongoDB

        Returns:
            Analysis results
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(audio) / sr

            # Extract features
            features = self._extract_features(audio, sr)

            # Classify emotion
            emotion_result = self._classify_emotion(features)

            # Detect stress indicators
            stress_level = self._detect_stress(features)

            # Store in MongoDB if requested
            mongo_id = None
            if store_raw:
                mongo_id = await self._store_audio_metadata(
                    user_id,
                    audio_path,
                    duration,
                    features
                )

            # Store analysis in PostgreSQL
            analysis = VoiceAnalysis(
                user_id=user_id,
                timestamp=datetime.now(),
                emotion=emotion_result['emotion'],
                confidence=emotion_result['confidence'],
                emotion_scores=emotion_result['scores'],
                stress_level=stress_level,
                voice_tremor_detected=features.get('tremor_detected', False),
                pitch_variability=features.get('pitch_variability'),
                speech_rate=features.get('speech_rate'),
                duration_seconds=duration,
                mongo_audio_id=mongo_id
            )

            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)

            return {
                "analysis_id": analysis.id,
                "emotion": emotion_result['emotion'],
                "confidence": emotion_result['confidence'],
                "stress_level": stress_level,
                "features": {
                    "pitch_variability": features.get('pitch_variability'),
                    "speech_rate": features.get('speech_rate'),
                    "energy": features.get('energy')
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing audio: {e}", exc_info=True)
            raise

    def _extract_features(self, audio: np.ndarray, sr: int) -> Dict:
        """Extract audio features for emotion detection"""
        features = {}

        # MFCC (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        features['mfcc_mean'] = np.mean(mfccs, axis=1)
        features['mfcc_std'] = np.std(mfccs, axis=1)

        # Pitch (fundamental frequency)
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        if pitch_values:
            features['pitch_mean'] = np.mean(pitch_values)
            features['pitch_std'] = np.std(pitch_values)
            features['pitch_variability'] = np.std(pitch_values) / np.mean(pitch_values) if np.mean(pitch_values) > 0 else 0
        else:
            features['pitch_mean'] = 0
            features['pitch_std'] = 0
            features['pitch_variability'] = 0

        # Energy
        energy = np.sum(librosa.feature.rms(y=audio))
        features['energy'] = float(energy)

        # Zero crossing rate (indicator of voice quality)
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
        features['zcr'] = float(zcr)

        # Spectral features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
        features['spectral_centroid'] = float(spectral_centroid)

        # Speech rate (approximate)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
        features['speech_rate'] = float(tempo)  # Rough approximation

        # Tremor detection (high pitch variability)
        features['tremor_detected'] = features['pitch_variability'] > 0.15

        return features

    def _classify_emotion(self, features: Dict) -> Dict:
        """
        Classify emotion from features (simplified heuristic-based)

        In production, use a trained ML model
        """
        scores = {
            'neutral': 0.2,
            'happy': 0.0,
            'sad': 0.0,
            'angry': 0.0,
            'anxious': 0.0,
            'stressed': 0.0
        }

        # Heuristics based on features
        pitch_var = features.get('pitch_variability', 0)
        energy = features.get('energy', 0)
        speech_rate = features.get('speech_rate', 0)

        # High pitch variability + high energy = anxious/stressed
        if pitch_var > 0.12 and energy > 1000:
            scores['anxious'] = 0.6
            scores['stressed'] = 0.4

        # High speech rate = stressed/anxious
        elif speech_rate > 150:
            scores['stressed'] = 0.5
            scores['anxious'] = 0.3

        # Low energy + low pitch = sad
        elif energy < 500 and features.get('pitch_mean', 0) < 150:
            scores['sad'] = 0.6

        # High energy + moderate pitch = happy
        elif energy > 1500 and 150 < features.get('pitch_mean', 0) < 250:
            scores['happy'] = 0.6

        # Otherwise neutral
        else:
            scores['neutral'] = 0.7

        # Normalize scores
        total = sum(scores.values())
        scores = {k: v/total for k, v in scores.items()}

        # Get dominant emotion
        emotion = max(scores, key=scores.get)
        confidence = scores[emotion]

        return {
            'emotion': emotion,
            'confidence': float(confidence),
            'scores': {k: float(v) for k, v in scores.items()}
        }

    def _detect_stress(self, features: Dict) -> float:
        """
        Detect stress level from voice features (0-1)
        """
        stress_score = 0.0

        # High pitch variability indicates stress
        pitch_var = features.get('pitch_variability', 0)
        if pitch_var > 0.1:
            stress_score += 0.3

        # Tremor indicates stress/anxiety
        if features.get('tremor_detected', False):
            stress_score += 0.2

        # High speech rate indicates stress
        speech_rate = features.get('speech_rate', 0)
        if speech_rate > 150:
            stress_score += 0.3

        # High zero crossing rate can indicate voice tension
        zcr = features.get('zcr', 0)
        if zcr > 0.1:
            stress_score += 0.2

        return min(stress_score, 1.0)

    async def _store_audio_metadata(
        self,
        user_id: str,
        file_path: str,
        duration: float,
        features: Dict
    ) -> str:
        """Store audio metadata in MongoDB"""
        collection = get_collection(COLLECTION_VOICE_RECORDINGS)

        doc = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "file_path": file_path,
            "duration_seconds": duration,
            "format": file_path.split('.')[-1],
            "sample_rate": self.sample_rate,
            "mfcc_features": features.get('mfcc_mean', []).tolist() if 'mfcc_mean' in features else None,
            "pitch_contour": None,  # Could store full pitch contour if needed
            "energy_contour": None,
            "created_at": datetime.now()
        }

        result = await collection.insert_one(doc)
        return str(result.inserted_id)
