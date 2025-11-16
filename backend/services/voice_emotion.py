"""
Voice Emotion Detection Service

Analyzes voice recordings for:
- Emotion classification
- Stress detection
- Voice characteristics
"""
import logging
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
import torch
import torchaudio
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
import librosa

from config.settings import settings

logger = logging.getLogger(__name__)


class VoiceEmotionAnalyzer:
    """
    Voice emotion and stress analyzer using wav2vec2
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = settings.AUDIO_SAMPLE_RATE

        # Emotion labels
        self.emotions = ["neutral", "happy", "sad", "angry", "fear", "disgust", "surprise"]

        # Try to load pretrained model
        try:
            self.processor = Wav2Vec2Processor.from_pretrained(
                "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                cache_dir=settings.MODEL_CACHE_DIR
            )
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(
                "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                cache_dir=settings.MODEL_CACHE_DIR
            ).to(self.device)
            self.model.eval()
            logger.info("Loaded pretrained voice emotion model")

        except Exception as e:
            logger.warning(f"Could not load pretrained model: {e}")
            self.processor = None
            self.model = None

    def load_audio(self, file_path: str) -> np.ndarray:
        """Load and preprocess audio file"""
        # Load audio with librosa
        audio, sr = librosa.load(file_path, sr=self.sample_rate)

        # Ensure mono
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio)

        return audio

    def extract_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract acoustic features from audio"""
        features = {}

        # Pitch (fundamental frequency)
        try:
            pitches, magnitudes = librosa.piptrack(
                y=audio,
                sr=self.sample_rate,
                fmin=75,
                fmax=400
            )

            # Get mean pitch
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            if pitch_values:
                features["pitch_mean"] = float(np.mean(pitch_values))
                features["pitch_std"] = float(np.std(pitch_values))
                features["pitch_variability"] = float(np.std(pitch_values) / np.mean(pitch_values))
            else:
                features["pitch_mean"] = 0.0
                features["pitch_std"] = 0.0
                features["pitch_variability"] = 0.0

        except Exception as e:
            logger.error(f"Error extracting pitch: {e}")
            features["pitch_mean"] = 0.0
            features["pitch_std"] = 0.0
            features["pitch_variability"] = 0.0

        # Energy/Amplitude
        rms = librosa.feature.rms(y=audio)[0]
        features["energy_mean"] = float(np.mean(rms))
        features["energy_std"] = float(np.std(rms))

        # Zero-crossing rate (voice tremor indicator)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        features["zcr_mean"] = float(np.mean(zcr))
        features["zcr_std"] = float(np.std(zcr))

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)[0]
        features["spectral_centroid_mean"] = float(np.mean(spectral_centroid))

        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)[0]
        features["spectral_rolloff_mean"] = float(np.mean(spectral_rolloff))

        # MFCC (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13)
        for i in range(13):
            features[f"mfcc_{i}_mean"] = float(np.mean(mfccs[i]))
            features[f"mfcc_{i}_std"] = float(np.std(mfccs[i]))

        return features

    def classify_emotion(self, audio: np.ndarray) -> Dict[str, Any]:
        """Classify emotion using wav2vec2 model"""
        if self.model is None or self.processor is None:
            # Fallback to feature-based heuristic
            return self._heuristic_emotion(audio)

        try:
            # Preprocess audio
            inputs = self.processor(
                audio,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding=True
            )

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                logits = self.model(**inputs).logits

            # Get probabilities
            probs = torch.nn.functional.softmax(logits, dim=-1)
            probs = probs.cpu().numpy()[0]

            # Map to emotion labels (model-specific)
            # This model outputs: neutral, calm, happy, sad, angry, fearful, disgust, surprised
            emotion_map = {
                0: "neutral",
                1: "neutral",  # calm -> neutral
                2: "happy",
                3: "sad",
                4: "angry",
                5: "fear",
                6: "disgust",
                7: "surprise"
            }

            emotion_scores = {}
            for i, prob in enumerate(probs):
                emotion = emotion_map.get(i, "neutral")
                if emotion not in emotion_scores:
                    emotion_scores[emotion] = 0.0
                emotion_scores[emotion] += float(prob)

            # Get primary emotion
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[primary_emotion]

            return {
                "emotion": primary_emotion,
                "confidence": confidence,
                "emotion_scores": emotion_scores
            }

        except Exception as e:
            logger.error(f"Error in emotion classification: {e}")
            return self._heuristic_emotion(audio)

    def _heuristic_emotion(self, audio: np.ndarray) -> Dict[str, Any]:
        """Fallback heuristic emotion detection based on acoustic features"""
        features = self.extract_features(audio)

        # Simple rules based on pitch and energy
        pitch_mean = features.get("pitch_mean", 0)
        pitch_var = features.get("pitch_variability", 0)
        energy = features.get("energy_mean", 0)

        # Heuristic classification
        if energy < 0.02:
            emotion = "sad"
            confidence = 0.6
        elif pitch_mean > 200 and energy > 0.05:
            emotion = "happy"
            confidence = 0.6
        elif pitch_var > 0.3 and energy > 0.04:
            emotion = "angry"
            confidence = 0.6
        else:
            emotion = "neutral"
            confidence = 0.5

        return {
            "emotion": emotion,
            "confidence": confidence,
            "emotion_scores": {emotion: confidence}
        }

    def detect_stress(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detect stress indicators in voice"""
        features = self.extract_features(audio)

        # Stress indicators:
        # - High pitch variability
        # - Fast speech rate (high ZCR)
        # - Voice tremor
        # - High energy

        pitch_var = features.get("pitch_variability", 0)
        zcr = features.get("zcr_mean", 0)
        energy = features.get("energy_mean", 0)

        # Calculate stress score (0-1)
        stress_score = 0.0

        # High pitch variability indicates stress
        if pitch_var > 0.3:
            stress_score += 0.3
        elif pitch_var > 0.2:
            stress_score += 0.2

        # High zero-crossing rate (rapid changes)
        if zcr > 0.15:
            stress_score += 0.3
        elif zcr > 0.10:
            stress_score += 0.2

        # Higher energy can indicate stress
        if energy > 0.06:
            stress_score += 0.2

        # Voice tremor detection (high std in pitch)
        pitch_std = features.get("pitch_std", 0)
        voice_tremor = pitch_std > 50

        if voice_tremor:
            stress_score += 0.2

        # Cap at 1.0
        stress_score = min(stress_score, 1.0)

        return {
            "stress_level": stress_score,
            "voice_tremor_detected": voice_tremor,
            "pitch_variability": pitch_var,
            "indicators": {
                "high_pitch_variability": pitch_var > 0.2,
                "rapid_speech": zcr > 0.10,
                "voice_tremor": voice_tremor
            }
        }

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Complete voice analysis

        Args:
            file_path: Path to audio file

        Returns:
            Dict with emotion, stress, and acoustic features
        """
        try:
            # Load audio
            audio = self.load_audio(file_path)

            # Duration
            duration_seconds = len(audio) / self.sample_rate

            # Extract features
            features = self.extract_features(audio)

            # Classify emotion
            emotion_result = self.classify_emotion(audio)

            # Detect stress
            stress_result = self.detect_stress(audio)

            # Combine results
            result = {
                "emotion": emotion_result["emotion"],
                "confidence": emotion_result["confidence"],
                "emotion_scores": emotion_result.get("emotion_scores", {}),
                "stress_level": stress_result["stress_level"],
                "voice_tremor_detected": stress_result["voice_tremor_detected"],
                "pitch_variability": stress_result["pitch_variability"],
                "duration_seconds": duration_seconds,
                "features": features
            }

            logger.info(f"Voice analysis complete: emotion={result['emotion']}, stress={result['stress_level']:.2f}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing voice: {e}")
            raise


# Global analyzer instance
_analyzer = None


def get_voice_analyzer() -> VoiceEmotionAnalyzer:
    """Get or create voice emotion analyzer"""
    global _analyzer
    if _analyzer is None:
        _analyzer = VoiceEmotionAnalyzer()
    return _analyzer
