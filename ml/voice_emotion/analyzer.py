"""
Voice Emotion Detection

Analyzes audio files for emotion and stress indicators
"""
import librosa
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceEmotionAnalyzer:
    """
    Voice emotion and stress detection

    Features extracted:
    - MFCCs (Mel-Frequency Cepstral Coefficients)
    - Pitch/Fundamental frequency
    - Energy/Intensity
    - Speech rate
    - Spectral features

    Stress indicators:
    - High pitch variation
    - Voice tremor (jitter)
    - Increased speech rate
    - Energy fluctuations
    """

    def __init__(self, sample_rate: int = 22050):
        """
        Initialize voice analyzer

        Args:
            sample_rate: Target sample rate for audio
        """
        self.sample_rate = sample_rate
        # In production, load a trained emotion classifier here
        # For now, use heuristic-based analysis

    def analyze(
        self,
        audio_path: str
    ) -> Dict:
        """
        Analyze audio file for emotion and stress

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Dict with emotion, confidence, stress indicators
        """
        # Load audio
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            return self._get_default_response()

        # Extract features
        features = self._extract_features(audio, sr)

        # Analyze emotion (heuristic-based for now)
        emotion_probs = self._analyze_emotion(features)

        # Detect stress indicators
        stress_indicators = self._detect_stress(features, audio, sr)

        # Determine primary emotion
        primary_emotion = max(emotion_probs.items(), key=lambda x: x[1])[0]
        confidence = emotion_probs[primary_emotion]

        return {
            "emotion": primary_emotion,
            "confidence": float(confidence),
            "emotional_state": {k: float(v) for k, v in emotion_probs.items()},
            "stress_indicators": stress_indicators,
            "features": {
                "pitch_mean": float(features["pitch_mean"]),
                "pitch_std": float(features["pitch_std"]),
                "energy_mean": float(features["energy_mean"]),
                "speech_rate": float(features["speech_rate"])
            }
        }

    def _extract_features(
        self,
        audio: np.ndarray,
        sr: int
    ) -> Dict:
        """Extract acoustic features from audio"""
        features = {}

        # MFCCs (spectral shape)
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        features["mfcc_mean"] = np.mean(mfccs, axis=1)
        features["mfcc_std"] = np.std(mfccs, axis=1)

        # Pitch/F0
        try:
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
            # Get pitch values where magnitude is significant
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Valid pitch
                    pitch_values.append(pitch)

            if pitch_values:
                features["pitch_mean"] = np.mean(pitch_values)
                features["pitch_std"] = np.std(pitch_values)
                features["pitch_range"] = np.max(pitch_values) - np.min(pitch_values)
            else:
                features["pitch_mean"] = 0
                features["pitch_std"] = 0
                features["pitch_range"] = 0

        except Exception as e:
            logger.warning(f"Error extracting pitch: {e}")
            features["pitch_mean"] = 0
            features["pitch_std"] = 0
            features["pitch_range"] = 0

        # Energy/RMS
        rms = librosa.feature.rms(y=audio)[0]
        features["energy_mean"] = np.mean(rms)
        features["energy_std"] = np.std(rms)

        # Zero crossing rate (roughness)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        features["zcr_mean"] = np.mean(zcr)

        # Speech rate (approximate from onset detection)
        try:
            onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
            onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
            duration = len(audio) / sr
            features["speech_rate"] = len(onsets) / duration  # onsets per second
        except:
            features["speech_rate"] = 0

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        features["spectral_centroid_mean"] = np.mean(spectral_centroid)

        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        features["spectral_rolloff_mean"] = np.mean(spectral_rolloff)

        return features

    def _analyze_emotion(self, features: Dict) -> Dict[str, float]:
        """
        Analyze emotion from features (heuristic-based)

        In production, this would be a trained neural network
        For now, use acoustic correlates from literature
        """
        # Initialize probabilities
        emotions = {
            "neutral": 0.2,
            "happy": 0.1,
            "sad": 0.1,
            "angry": 0.1,
            "anxious": 0.3,
            "stressed": 0.2
        }

        pitch_mean = features.get("pitch_mean", 0)
        pitch_std = features.get("pitch_std", 0)
        energy_mean = features.get("energy_mean", 0)
        speech_rate = features.get("speech_rate", 0)

        # Anxiety/Stress: high pitch variation, high speech rate
        if pitch_std > 50 and speech_rate > 3:
            emotions["anxious"] += 0.3
            emotions["stressed"] += 0.2

        # Happiness: higher pitch, higher energy, moderate variation
        if pitch_mean > 180 and energy_mean > 0.05:
            emotions["happy"] += 0.3

        # Sadness: lower pitch, lower energy
        if pitch_mean < 150 and energy_mean < 0.03:
            emotions["sad"] += 0.3

        # Anger: high energy, high pitch, high variation
        if energy_mean > 0.06 and pitch_std > 60:
            emotions["angry"] += 0.25

        # Normalize to probabilities
        total = sum(emotions.values())
        emotions = {k: v/total for k, v in emotions.items()}

        return emotions

    def _detect_stress(
        self,
        features: Dict,
        audio: np.ndarray,
        sr: int
    ) -> List[str]:
        """
        Detect stress indicators in voice

        Research shows stress affects:
        - Pitch (F0) increases and becomes more variable
        - Voice tremor (jitter)
        - Speech rate increases
        - Energy/intensity patterns change
        """
        indicators = []

        pitch_std = features.get("pitch_std", 0)
        pitch_mean = features.get("pitch_mean", 0)
        speech_rate = features.get("speech_rate", 0)
        energy_std = features.get("energy_std", 0)

        # High pitch variation
        if pitch_std > 50:
            indicators.append("Elevated pitch variation (stress indicator)")

        # High pitch overall
        if pitch_mean > 200:
            indicators.append("Elevated pitch (possible stress or emotion)")

        # Fast speech rate
        if speech_rate > 3.5:
            indicators.append("Increased speech rate (possible anxiety)")

        # Voice tremor (check energy fluctuations)
        if energy_std > 0.015:
            indicators.append("Voice tremor detected (stress/anxiety indicator)")

        # Low energy (fatigue)
        if features.get("energy_mean", 0) < 0.02:
            indicators.append("Low voice energy (possible fatigue)")

        if not indicators:
            indicators.append("No significant stress indicators detected")

        return indicators

    def _get_default_response(self) -> Dict:
        """Default response when analysis fails"""
        return {
            "emotion": "neutral",
            "confidence": 0.5,
            "emotional_state": {
                "neutral": 0.5,
                "happy": 0.1,
                "sad": 0.1,
                "angry": 0.1,
                "anxious": 0.1,
                "stressed": 0.1
            },
            "stress_indicators": ["Analysis failed - using default values"],
            "features": {
                "pitch_mean": 0,
                "pitch_std": 0,
                "energy_mean": 0,
                "speech_rate": 0
            }
        }


# For production: Trained model using wav2vec2 or similar
class VoiceEmotionModel:
    """
    Deep learning model for voice emotion recognition

    Would use:
    - wav2vec2 for feature extraction
    - Fine-tuned on emotion datasets (RAVDESS, CREMA-D)
    - Multi-class classifier head

    Example architecture:
    ```
    model = Wav2Vec2ForSequenceClassification.from_pretrained(
        "facebook/wav2vec2-base",
        num_labels=6  # neutral, happy, sad, angry, anxious, stressed
    )
    ```
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize trained model

        Args:
            model_path: Path to trained model checkpoint
        """
        # TODO: Load trained model
        # For now, use heuristic analyzer
        self.model = None
        logger.info("Voice emotion model not yet trained. Using heuristic analysis.")

    def predict(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Predict emotion probabilities

        Args:
            audio: Audio waveform

        Returns:
            Dict of emotion probabilities
        """
        # TODO: Implement model inference
        # For now, return uniform probabilities
        return {
            "neutral": 0.2,
            "happy": 0.15,
            "sad": 0.15,
            "angry": 0.15,
            "anxious": 0.2,
            "stressed": 0.15
        }


# Global analyzer instance
_voice_analyzer = None

def get_voice_analyzer() -> VoiceEmotionAnalyzer:
    """Get or create voice analyzer singleton"""
    global _voice_analyzer
    if _voice_analyzer is None:
        _voice_analyzer = VoiceEmotionAnalyzer()
    return _voice_analyzer
