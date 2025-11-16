"""
Voice Emotion Detection using deep learning

This module implements voice emotion classification using:
- Audio feature extraction (MFCC, spectral features, prosody)
- Pre-trained models from HuggingFace or custom training
- Stress indicator detection (voice tremor, pitch variation)
"""

import numpy as np
import librosa
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class VoiceEmotionClassifier:
    """
    Voice emotion classifier using audio features
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        use_pretrained: bool = True
    ):
        self.sample_rate = 16000
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Emotion labels
        self.emotions = ["neutral", "happy", "sad", "angry", "anxious", "stressed"]

        if use_pretrained:
            self._load_pretrained_model()
        elif model_path:
            self._load_custom_model(model_path)
        else:
            self._create_default_model()

    def _load_pretrained_model(self):
        """Load pretrained model from HuggingFace"""
        try:
            from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

            model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
            self.model = AutoModelForAudioClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()

            print(f"✅ Loaded pretrained voice emotion model: {model_name}")

        except Exception as e:
            print(f"Could not load pretrained model: {e}")
            print("Falling back to feature-based classifier")
            self._create_default_model()

    def _create_default_model(self):
        """Create a simple feature-based classifier"""
        class SimpleEmotionClassifier(nn.Module):
            def __init__(self, input_dim=40, hidden_dim=128, num_classes=6):
                super().__init__()
                self.network = nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(hidden_dim, num_classes),
                    nn.Softmax(dim=1)
                )

            def forward(self, x):
                return self.network(x)

        self.model = SimpleEmotionClassifier(input_dim=40, num_classes=len(self.emotions))
        self.model.to(self.device)
        self.model.eval()

        print("✅ Created default voice emotion classifier")

    def _load_custom_model(self, model_path: str):
        """Load a custom trained model"""
        try:
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            print(f"✅ Loaded custom model from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self._create_default_model()

    def extract_features(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """
        Extract audio features for emotion classification

        Features include:
        - MFCCs (Mel-frequency cepstral coefficients)
        - Spectral features (centroid, rolloff, contrast)
        - Prosodic features (pitch, energy, tempo)
        - Zero-crossing rate
        """
        features = []

        # Resample if necessary
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)

        # MFCCs (13 coefficients)
        mfccs = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
        mfccs_mean = np.mean(mfccs, axis=1)
        mfccs_std = np.std(mfccs, axis=1)
        features.extend(mfccs_mean)
        features.extend(mfccs_std)  # 26 features

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)
        features.append(np.mean(spectral_centroids))
        features.append(np.std(spectral_centroids))

        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate)
        features.append(np.mean(spectral_rolloff))
        features.append(np.std(spectral_rolloff))

        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio_data)
        features.append(np.mean(zcr))
        features.append(np.std(zcr))

        # Chroma features
        chroma = librosa.feature.chroma_stft(y=audio_data, sr=self.sample_rate)
        features.append(np.mean(chroma))
        features.append(np.std(chroma))

        # Tempo and rhythm
        tempo, _ = librosa.beat.beat_track(y=audio_data, sr=self.sample_rate)
        features.append(tempo)

        # RMS Energy
        rms = librosa.feature.rms(y=audio_data)
        features.append(np.mean(rms))
        features.append(np.std(rms))

        # Total: 26 + 2 + 2 + 2 + 2 + 1 + 2 = 37 features
        # Pad to 40
        while len(features) < 40:
            features.append(0.0)

        return np.array(features[:40])

    def detect_stress_indicators(self, audio_data: np.ndarray, sr: int) -> List[str]:
        """
        Detect stress indicators in voice:
        - Voice tremor (high frequency variation)
        - Elevated pitch
        - Increased speech rate
        - Energy variation
        """
        indicators = []

        # Resample if necessary
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)

        # Pitch analysis
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=self.sample_rate)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        if pitch_values:
            mean_pitch = np.mean(pitch_values)
            std_pitch = np.std(pitch_values)

            # High pitch variation indicates stress
            if std_pitch > 30:
                indicators.append("Elevated pitch variation")

            # High average pitch can indicate stress
            if mean_pitch > 200:
                indicators.append("Higher than average pitch")

        # Speech rate (via onset detection)
        onset_env = librosa.onset.onset_strength(y=audio_data, sr=self.sample_rate)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sample_rate)

        speech_rate = len(onsets) / (len(audio_data) / self.sample_rate)  # onsets per second
        if speech_rate > 3.5:
            indicators.append("Increased speech rate")

        # Energy variation
        rms = librosa.feature.rms(y=audio_data)
        rms_std = np.std(rms)
        if rms_std > 0.05:
            indicators.append("High energy variation")

        # Voice tremor detection (spectral flux)
        spectral_flux = np.sqrt(np.sum(np.diff(np.abs(librosa.stft(audio_data)))**2, axis=0))
        if np.mean(spectral_flux) > 100:
            indicators.append("Voice tremor detected")

        return indicators if indicators else ["No stress indicators detected"]

    def analyze(
        self,
        audio_path: str = None,
        audio_data: np.ndarray = None,
        sr: int = None
    ) -> Dict[str, any]:
        """
        Analyze voice for emotion and stress

        Args:
            audio_path: Path to audio file
            audio_data: Audio data as numpy array
            sr: Sample rate (if audio_data provided)

        Returns:
            Dict with emotion predictions and stress indicators
        """
        # Load audio
        if audio_path:
            audio_data, sr = librosa.load(audio_path, sr=self.sample_rate)
        elif audio_data is None:
            raise ValueError("Either audio_path or audio_data must be provided")

        # Extract features
        features = self.extract_features(audio_data, sr)

        # Predict emotion
        if hasattr(self, 'feature_extractor'):
            # Use pretrained transformer model
            inputs = self.feature_extractor(
                audio_data,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]
            probabilities = probabilities.cpu().numpy()

            # Map to our emotion labels (this is simplified - real mapping would be more complex)
            emotion_dict = {emotion: float(prob) for emotion, prob in zip(self.emotions, probabilities[:len(self.emotions)])}

        else:
            # Use feature-based model
            features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)

            with torch.no_grad():
                probabilities = self.model(features_tensor)[0].cpu().numpy()

            emotion_dict = {emotion: float(prob) for emotion, prob in zip(self.emotions, probabilities)}

        # Get primary emotion
        primary_emotion = max(emotion_dict, key=emotion_dict.get)
        confidence = emotion_dict[primary_emotion]

        # Detect stress indicators
        stress_indicators = self.detect_stress_indicators(audio_data, sr)

        return {
            "emotion": primary_emotion,
            "confidence": round(confidence, 3),
            "emotional_state": {k: round(v, 3) for k, v in emotion_dict.items()},
            "stress_indicators": stress_indicators,
            "features": {
                "pitch_mean": float(np.mean(audio_data)),
                "energy_mean": float(np.mean(librosa.feature.rms(y=audio_data))),
                "duration_seconds": len(audio_data) / sr
            }
        }


class VoiceProcessor:
    """
    Process and prepare voice recordings for analysis
    """

    @staticmethod
    def preprocess_audio(
        audio_path: str,
        output_path: str = None,
        target_sr: int = 16000
    ) -> Tuple[np.ndarray, int]:
        """
        Preprocess audio file:
        - Load and resample
        - Remove silence
        - Normalize volume
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=target_sr)

        # Trim silence
        audio, _ = librosa.effects.trim(audio, top_db=20)

        # Normalize
        audio = librosa.util.normalize(audio)

        # Save if output path provided
        if output_path:
            import soundfile as sf
            sf.write(output_path, audio, sr)

        return audio, sr

    @staticmethod
    def split_audio_segments(
        audio: np.ndarray,
        sr: int,
        segment_duration: float = 3.0
    ) -> List[np.ndarray]:
        """
        Split audio into fixed-duration segments
        """
        segment_samples = int(segment_duration * sr)
        segments = []

        for start in range(0, len(audio), segment_samples):
            end = start + segment_samples
            segment = audio[start:end]

            # Pad last segment if too short
            if len(segment) < segment_samples:
                segment = np.pad(segment, (0, segment_samples - len(segment)))

            segments.append(segment)

        return segments


# Convenience function
def analyze_voice_emotion(audio_path: str) -> Dict:
    """
    Quick function to analyze voice emotion from audio file
    """
    classifier = VoiceEmotionClassifier()
    return classifier.analyze(audio_path=audio_path)
