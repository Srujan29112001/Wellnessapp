"""
Voice Emotion Detection using Deep Learning
Analyzes audio to detect emotions and stress levels
"""

import numpy as np
import torch
import torch.nn as nn
import librosa
import soundfile as sf
from typing import Dict, Tuple, Optional
from pathlib import Path
import logging

from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
from transformers import pipeline

logger = logging.getLogger(__name__)


class VoiceEmotionDetector:
    """
    Voice emotion detection using Wav2Vec2 and audio features

    Detects: neutral, happy, sad, angry, anxious, stressed
    """

    def __init__(
        self,
        model_name: str = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
        use_gpu: bool = True
    ):
        """
        Initialize voice emotion detector

        Args:
            model_name: HuggingFace model for emotion detection
            use_gpu: Whether to use GPU if available
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        logger.info(f"Voice emotion detector using device: {self.device}")

        # Load pretrained model
        try:
            self.emotion_pipeline = pipeline(
                "audio-classification",
                model=model_name,
                device=0 if self.device == "cuda" else -1
            )
            logger.info(f"Loaded emotion detection model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load pretrained model: {e}")
            logger.info("Will use feature-based emotion detection instead")
            self.emotion_pipeline = None

        # Emotion mapping
        self.emotion_map = {
            "neutral": 0,
            "happy": 1,
            "sad": 2,
            "angry": 3,
            "fear": 4,  # Maps to anxious
            "disgust": 5,
            "surprise": 6
        }

        # Target sample rate for models
        self.sample_rate = 16000

    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample if needed

        Args:
            audio_path: Path to audio file

        Returns:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            logger.info(f"Loaded audio: {audio_path}, duration: {len(audio)/sr:.2f}s")
            return audio, sr
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            raise

    def extract_audio_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Extract audio features for emotion detection

        Features:
        - Pitch (fundamental frequency)
        - Pitch variation
        - Energy (RMS)
        - Zero crossing rate
        - Spectral centroid
        - MFCC statistics
        - Speech rate
        """
        features = {}

        # Pitch features
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        if pitch_values:
            features["pitch_mean"] = float(np.mean(pitch_values))
            features["pitch_std"] = float(np.std(pitch_values))
            features["pitch_max"] = float(np.max(pitch_values))
            features["pitch_min"] = float(np.min(pitch_values))
        else:
            features["pitch_mean"] = 0.0
            features["pitch_std"] = 0.0
            features["pitch_max"] = 0.0
            features["pitch_min"] = 0.0

        # Energy features
        rms = librosa.feature.rms(y=audio)[0]
        features["energy_mean"] = float(np.mean(rms))
        features["energy_std"] = float(np.std(rms))
        features["energy_max"] = float(np.max(rms))

        # Zero crossing rate (voice tremor indicator)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        features["zcr_mean"] = float(np.mean(zcr))
        features["zcr_std"] = float(np.std(zcr))

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        features["spectral_centroid_mean"] = float(np.mean(spectral_centroids))
        features["spectral_centroid_std"] = float(np.std(spectral_centroids))

        # MFCC features (timbre)
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        for i in range(13):
            features[f"mfcc_{i}_mean"] = float(np.mean(mfccs[i]))
            features[f"mfcc_{i}_std"] = float(np.std(mfccs[i]))

        # Speech rate (onset detection)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        features["tempo"] = float(tempo[0]) if len(tempo) > 0 else 0.0

        return features

    def predict_emotion(
        self,
        audio_path: str,
        return_features: bool = False
    ) -> Dict[str, any]:
        """
        Predict emotion from audio file

        Args:
            audio_path: Path to audio file
            return_features: Whether to return extracted features

        Returns:
            Dictionary with emotion predictions and metadata
        """
        # Load audio
        audio, sr = self.load_audio(audio_path)

        # Extract features
        audio_features = self.extract_audio_features(audio, sr)

        # Predict using model if available
        if self.emotion_pipeline is not None:
            try:
                # Use pretrained model
                predictions = self.emotion_pipeline(audio_path)

                # Get top emotion
                top_emotion = predictions[0]
                emotion = top_emotion["label"].lower()
                confidence = top_emotion["score"]

                # Map to our emotion categories
                if "angry" in emotion or "anger" in emotion:
                    primary_emotion = "angry"
                elif "sad" in emotion:
                    primary_emotion = "sad"
                elif "happy" in emotion or "joy" in emotion:
                    primary_emotion = "happy"
                elif "fear" in emotion:
                    primary_emotion = "anxious"
                else:
                    primary_emotion = "neutral"

                # Get all emotion probabilities
                emotion_probs = {
                    pred["label"].lower(): pred["score"]
                    for pred in predictions[:6]
                }

            except Exception as e:
                logger.error(f"Error in model prediction: {e}")
                # Fall back to heuristic
                primary_emotion, confidence, emotion_probs = self._heuristic_emotion_detection(
                    audio_features
                )
        else:
            # Use heuristic-based detection
            primary_emotion, confidence, emotion_probs = self._heuristic_emotion_detection(
                audio_features
            )

        # Detect stress indicators
        stress_indicators = self._detect_stress_indicators(audio_features)

        result = {
            "primary_emotion": primary_emotion,
            "confidence": confidence,
            "emotion_probabilities": emotion_probs,
            "stress_level": stress_indicators["stress_level"],
            "stress_indicators": stress_indicators,
            "audio_duration": len(audio) / sr,
        }

        if return_features:
            result["features"] = audio_features

        return result

    def _heuristic_emotion_detection(
        self,
        features: Dict[str, float]
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Heuristic-based emotion detection from features

        Rules:
        - High pitch + high energy = angry/anxious
        - Low pitch + low energy = sad
        - High pitch variation + high energy = happy
        - Low variation + moderate energy = neutral
        """
        pitch_mean = features.get("pitch_mean", 0)
        pitch_std = features.get("pitch_std", 0)
        energy_mean = features.get("energy_mean", 0)
        zcr_std = features.get("zcr_std", 0)

        # Normalize features (simplified)
        pitch_high = pitch_mean > 180
        pitch_low = pitch_mean < 140
        pitch_varied = pitch_std > 30
        energy_high = energy_mean > 0.05
        energy_low = energy_mean < 0.02
        tremor = zcr_std > 0.1

        # Emotion probabilities
        probs = {
            "neutral": 0.3,
            "happy": 0.0,
            "sad": 0.0,
            "angry": 0.0,
            "anxious": 0.0,
        }

        # Angry: high pitch + high energy
        if pitch_high and energy_high:
            probs["angry"] = 0.6
            probs["anxious"] = 0.3

        # Happy: varied pitch + high energy
        elif pitch_varied and energy_high:
            probs["happy"] = 0.7

        # Sad: low pitch + low energy
        elif pitch_low and energy_low:
            probs["sad"] = 0.6

        # Anxious: tremor + varied pitch
        elif tremor and pitch_varied:
            probs["anxious"] = 0.6

        # Normalize
        total = sum(probs.values())
        probs = {k: v / total for k, v in probs.items()}

        # Get primary emotion
        primary = max(probs, key=probs.get)
        confidence = probs[primary]

        return primary, confidence, probs

    def _detect_stress_indicators(
        self,
        features: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Detect stress indicators from voice features

        Stress indicators:
        - Voice tremor (high ZCR variation)
        - Pitch instability (high pitch std)
        - Speaking rate changes
        - Energy fluctuations
        """
        indicators = {}

        # Voice tremor
        zcr_std = features.get("zcr_std", 0)
        indicators["voice_tremor"] = "high" if zcr_std > 0.1 else "normal"

        # Pitch variability
        pitch_std = features.get("pitch_std", 0)
        indicators["pitch_variability"] = "high" if pitch_std > 40 else "normal"

        # Speaking rate
        tempo = features.get("tempo", 0)
        if tempo > 150:
            indicators["speech_rate"] = "fast"
        elif tempo < 80:
            indicators["speech_rate"] = "slow"
        else:
            indicators["speech_rate"] = "normal"

        # Energy instability
        energy_std = features.get("energy_std", 0)
        indicators["energy_stability"] = "unstable" if energy_std > 0.03 else "stable"

        # Calculate overall stress level (0-1)
        stress_score = 0.0
        if indicators["voice_tremor"] == "high":
            stress_score += 0.3
        if indicators["pitch_variability"] == "high":
            stress_score += 0.3
        if indicators["speech_rate"] != "normal":
            stress_score += 0.2
        if indicators["energy_stability"] == "unstable":
            stress_score += 0.2

        indicators["stress_level"] = min(stress_score, 1.0)

        return indicators

    def analyze_voice_trends(
        self,
        audio_paths: list[str]
    ) -> Dict[str, any]:
        """
        Analyze emotion trends across multiple audio samples

        Args:
            audio_paths: List of audio file paths (chronological order)

        Returns:
            Trend analysis results
        """
        results = []
        for path in audio_paths:
            try:
                result = self.predict_emotion(path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {path}: {e}")

        if not results:
            return {}

        # Calculate trends
        emotions = [r["primary_emotion"] for r in results]
        stress_levels = [r["stress_level"] for r in results]

        trend_analysis = {
            "dominant_emotion": max(set(emotions), key=emotions.count),
            "emotion_distribution": {
                emotion: emotions.count(emotion) / len(emotions)
                for emotion in set(emotions)
            },
            "average_stress": float(np.mean(stress_levels)),
            "stress_trend": "increasing" if len(stress_levels) > 1 and stress_levels[-1] > stress_levels[0] else "stable",
            "num_samples": len(results),
        }

        return trend_analysis


def create_voice_emotion_detector(use_gpu: bool = True) -> VoiceEmotionDetector:
    """Factory function to create voice emotion detector"""
    return VoiceEmotionDetector(use_gpu=use_gpu)
