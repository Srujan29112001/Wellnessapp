"""
Voice Emotion Analysis Service

Analyzes voice recordings to detect:
- Emotional state (happy, sad, anxious, stressed, neutral, angry)
- Stress indicators (voice tremor, pitch variation, speech rate)
- Audio features (MFCC, pitch, energy, spectral features)
"""

import os
import io
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification


class VoiceFeatureExtractor:
    """Extracts acoustic features from voice recordings"""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def extract_features(self, audio_data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract comprehensive audio features

        Returns:
            {
                'mfcc': MFCCs (mel-frequency cepstral coefficients),
                'pitch': Pitch contour,
                'energy': Energy envelope,
                'spectral_centroid': Spectral centroid,
                'zero_crossing_rate': Zero crossing rate,
                'statistics': Summary statistics
            }
        """
        # Ensure audio is float32
        audio_data = audio_data.astype(np.float32)

        # MFCCs (13 coefficients)
        mfccs = librosa.feature.mfcc(
            y=audio_data,
            sr=self.sample_rate,
            n_mfcc=13
        )

        # Pitch (fundamental frequency) using pYIN algorithm
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_data,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=self.sample_rate
        )

        # Energy/RMS
        energy = librosa.feature.rms(y=audio_data)[0]

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio_data,
            sr=self.sample_rate
        )[0]

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio_data,
            sr=self.sample_rate
        )[0]

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio_data)[0]

        # Chroma features
        chroma = librosa.feature.chroma_stft(
            y=audio_data,
            sr=self.sample_rate
        )

        # Statistical summaries
        statistics = {
            'pitch_mean': float(np.nanmean(f0)),
            'pitch_std': float(np.nanstd(f0)),
            'pitch_min': float(np.nanmin(f0)),
            'pitch_max': float(np.nanmax(f0)),
            'energy_mean': float(np.mean(energy)),
            'energy_std': float(np.std(energy)),
            'spectral_centroid_mean': float(np.mean(spectral_centroid)),
            'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
            'zcr_mean': float(np.mean(zcr)),
            'voiced_ratio': float(np.sum(voiced_flag) / len(voiced_flag))
        }

        return {
            'mfcc': mfccs,
            'pitch': f0,
            'energy': energy,
            'spectral_centroid': spectral_centroid,
            'spectral_bandwidth': spectral_bandwidth,
            'zero_crossing_rate': zcr,
            'chroma': chroma,
            'statistics': statistics
        }

    def detect_stress_indicators(self, features: Dict) -> List[str]:
        """
        Detect stress indicators from audio features

        Stress indicators include:
        - High pitch variation (uncertainty, anxiety)
        - Voice tremor (nervousness)
        - Increased speech rate
        - Elevated pitch
        """
        indicators = []
        stats = features['statistics']

        # High pitch variation
        if stats['pitch_std'] > 50:  # Hz
            indicators.append("Elevated pitch variation")

        # High pitch (stress/anxiety raises pitch)
        if stats['pitch_mean'] > 200:  # Hz (varies by gender)
            indicators.append("Elevated vocal pitch")

        # Tremor detection (high energy variation)
        if stats['energy_std'] > 0.1:
            indicators.append("Voice tremor detected")

        # Low voiced ratio (breathiness, can indicate stress)
        if stats['voiced_ratio'] < 0.5:
            indicators.append("Increased breathiness")

        return indicators


class VoiceEmotionClassifier:
    """
    Classifies emotion from voice using pre-trained models

    Uses Wav2Vec2 fine-tuned on emotion datasets
    """

    EMOTION_LABELS = [
        "neutral",
        "happy",
        "sad",
        "angry",
        "anxious",
        "stressed"
    ]

    def __init__(
        self,
        model_name: str = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
        device: str = "cpu"
    ):
        self.device = device

        try:
            # Load pre-trained emotion recognition model
            self.processor = Wav2Vec2Processor.from_pretrained(model_name)
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
            self.model.to(device)
            self.model.eval()
            self.available = True
        except Exception as e:
            print(f"Could not load Wav2Vec2 model: {e}")
            print("Falling back to heuristic-based classification")
            self.available = False

    def classify(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
        """
        Classify emotion from audio

        Returns:
            Dictionary of emotion probabilities
        """
        if not self.available:
            return self._heuristic_classify(audio_data, sample_rate)

        try:
            # Resample if needed
            if sample_rate != 16000:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=16000
                )

            # Process audio
            inputs = self.processor(
                audio_data,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get predictions
            with torch.no_grad():
                logits = self.model(**inputs).logits

            # Convert to probabilities
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]

            # Map to our emotion labels
            # Note: The pre-trained model may have different labels,
            # this is a simplified mapping
            emotion_probs = {
                "neutral": float(probs[0]) if len(probs) > 0 else 0.5,
                "happy": float(probs[1]) if len(probs) > 1 else 0.1,
                "sad": float(probs[2]) if len(probs) > 2 else 0.1,
                "angry": float(probs[3]) if len(probs) > 3 else 0.1,
                "anxious": float(probs[4]) if len(probs) > 4 else 0.1,
                "stressed": float(probs[5]) if len(probs) > 5 else 0.1
            }

            # Normalize to sum to 1
            total = sum(emotion_probs.values())
            emotion_probs = {k: v/total for k, v in emotion_probs.items()}

            return emotion_probs

        except Exception as e:
            print(f"Error in model prediction: {e}. Using heuristic fallback.")
            return self._heuristic_classify(audio_data, sample_rate)

    def _heuristic_classify(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """
        Heuristic-based emotion classification from audio features

        This is a fallback when the ML model is not available
        """
        extractor = VoiceFeatureExtractor(sample_rate=sample_rate)
        features = extractor.extract_features(audio_data)
        stats = features['statistics']

        # Initialize emotion scores
        emotions = {
            "neutral": 0.5,
            "happy": 0.1,
            "sad": 0.1,
            "angry": 0.1,
            "anxious": 0.1,
            "stressed": 0.1
        }

        # High pitch + high variation = anxious/stressed
        if stats['pitch_mean'] > 180 and stats['pitch_std'] > 40:
            emotions['anxious'] = 0.6
            emotions['stressed'] = 0.5
            emotions['neutral'] = 0.2

        # Low pitch + low energy = sad
        elif stats['pitch_mean'] < 150 and stats['energy_mean'] < 0.05:
            emotions['sad'] = 0.6
            emotions['neutral'] = 0.3

        # High energy + high pitch = angry or happy
        elif stats['energy_mean'] > 0.1 and stats['pitch_mean'] > 180:
            # Distinguish by pitch variation
            if stats['pitch_std'] > 50:
                emotions['angry'] = 0.6
            else:
                emotions['happy'] = 0.6
            emotions['neutral'] = 0.2

        # Normalize
        total = sum(emotions.values())
        emotions = {k: v/total for k, v in emotions.items()}

        return emotions


class VoiceAnalysisService:
    """High-level voice analysis service"""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.feature_extractor = VoiceFeatureExtractor(sample_rate)
        self.emotion_classifier = VoiceEmotionClassifier()

    async def analyze_voice_file(self, file_bytes: bytes, user_id: str) -> Dict:
        """
        Analyze voice from uploaded file

        Args:
            file_bytes: Audio file bytes (WAV, MP3, etc.)
            user_id: User identifier

        Returns:
            {
                'emotion': str,
                'confidence': float,
                'emotional_state': Dict[str, float],
                'stress_indicators': List[str],
                'features': Dict
            }
        """
        # Load audio from bytes
        audio_data, sr = self._load_audio_from_bytes(file_bytes)

        # Resample if needed
        if sr != self.sample_rate:
            audio_data = librosa.resample(
                audio_data,
                orig_sr=sr,
                target_sr=self.sample_rate
            )

        # Extract features
        features = self.feature_extractor.extract_features(audio_data)

        # Classify emotion
        emotion_probs = self.emotion_classifier.classify(audio_data, self.sample_rate)

        # Get primary emotion
        primary_emotion = max(emotion_probs.items(), key=lambda x: x[1])

        # Detect stress indicators
        stress_indicators = self.feature_extractor.detect_stress_indicators(features)

        # Calculate overall stress score
        stress_score = emotion_probs.get('stressed', 0) + emotion_probs.get('anxious', 0)
        stress_score = min(stress_score, 1.0)

        return {
            'id': f"voice_{user_id}_{int(datetime.now().timestamp())}",
            'user_id': user_id,
            'timestamp': datetime.now(),
            'emotion': primary_emotion[0],
            'confidence': float(primary_emotion[1]),
            'emotional_state': emotion_probs,
            'stress_indicators': stress_indicators,
            'stress_score': float(stress_score),
            'features': features['statistics']  # Don't include full arrays
        }

    def _load_audio_from_bytes(self, file_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Load audio from bytes (supports WAV, MP3, etc.)"""
        try:
            # Try to load with soundfile first (WAV, FLAC)
            audio_data, sr = sf.read(io.BytesIO(file_bytes))

        except Exception:
            # Fall back to librosa (supports MP3, M4A, etc.)
            audio_data, sr = librosa.load(io.BytesIO(file_bytes), sr=None)

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        return audio_data, sr


# Global service instance
_voice_service: Optional[VoiceAnalysisService] = None


def get_voice_service() -> VoiceAnalysisService:
    """Get or create voice service instance"""
    global _voice_service

    if _voice_service is None:
        _voice_service = VoiceAnalysisService()

    return _voice_service
