"""
Multi-Modal Fusion for Holistic Wellness Assessment.

Combines multiple modalities for comprehensive health assessment:
- EEG (brain activity)
- Voice (emotion, stress)
- Images (food, supplements)
- Text (journaling, self-reports)
- Wearables (activity, sleep, heart rate)

Creates unified embeddings and provides cross-modal reasoning
for personalized wellness recommendations.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')


@dataclass
class ModalityData:
    """Container for single modality data."""
    modality_type: str  # 'eeg', 'voice', 'image', 'text', 'wearable'
    features: np.ndarray
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = None


@dataclass
class MultiModalAssessment:
    """Result of multi-modal fusion."""
    overall_wellness_score: float  # 0-100
    stress_level: float  # 0-10
    mental_state: str  # 'stressed', 'relaxed', 'focused', 'drowsy'
    energy_level: float  # 0-10
    confidence: float  # 0-1
    contributing_modalities: List[str]
    modality_weights: Dict[str, float]
    recommendations: List[str]
    insights: List[str]
    fusion_embedding: np.ndarray


class ModalityEncoder(nn.Module):
    """Encode each modality into a common embedding space."""

    def __init__(self, input_dim: int, embedding_dim: int = 128):
        """
        Args:
            input_dim: Input feature dimension
            embedding_dim: Common embedding dimension
        """
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, embedding_dim),
            nn.Tanh()  # Normalize to [-1, 1]
        )

    def forward(self, x):
        return self.encoder(x)


class AttentionFusion(nn.Module):
    """Attention-based fusion of multiple modalities."""

    def __init__(self, embedding_dim: int = 128):
        """
        Args:
            embedding_dim: Dimension of modality embeddings
        """
        super().__init__()

        self.attention = nn.Sequential(
            nn.Linear(embedding_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

    def forward(self, embeddings: torch.Tensor, mask: Optional[torch.Tensor] = None):
        """
        Args:
            embeddings: (batch, n_modalities, embedding_dim)
            mask: (batch, n_modalities) - 1 for valid, 0 for invalid

        Returns:
            fused: (batch, embedding_dim)
            weights: (batch, n_modalities)
        """
        # Compute attention scores
        scores = self.attention(embeddings).squeeze(-1)  # (batch, n_modalities)

        # Apply mask if provided
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        # Softmax to get attention weights
        weights = torch.softmax(scores, dim=-1)  # (batch, n_modalities)

        # Weighted sum
        fused = torch.sum(embeddings * weights.unsqueeze(-1), dim=1)  # (batch, embedding_dim)

        return fused, weights


class CrossModalReasoning(nn.Module):
    """Cross-modal reasoning for wellness assessment."""

    def __init__(self, embedding_dim: int = 128, n_outputs: int = 4):
        """
        Args:
            embedding_dim: Dimension of fused embedding
            n_outputs: Number of output predictions
        """
        super().__init__()

        self.reasoning = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, n_outputs)
        )

    def forward(self, fused_embedding):
        return self.reasoning(fused_embedding)


class MultiModalFusionEngine:
    """Main engine for multi-modal health assessment."""

    def __init__(self, embedding_dim: int = 128, device: str = "cpu"):
        """
        Initialize fusion engine.

        Args:
            embedding_dim: Common embedding dimension
            device: 'cuda' or 'cpu'
        """
        self.embedding_dim = embedding_dim
        self.device = device

        # Modality-specific encoders (input dimensions)
        self.encoders = {
            'eeg': ModalityEncoder(10, embedding_dim),  # 10 EEG features (band powers, etc.)
            'voice': ModalityEncoder(40, embedding_dim),  # 40 voice features (MFCCs, etc.)
            'image': ModalityEncoder(512, embedding_dim),  # 512 image features (CNN)
            'text': ModalityEncoder(384, embedding_dim),  # 384 text features (BERT)
            'wearable': ModalityEncoder(20, embedding_dim),  # 20 wearable features
        }

        # Attention-based fusion
        self.fusion = AttentionFusion(embedding_dim)

        # Cross-modal reasoning
        self.reasoning = CrossModalReasoning(embedding_dim, n_outputs=4)

        # Feature scalers
        self.scalers = {
            'eeg': StandardScaler(),
            'voice': StandardScaler(),
            'wearable': StandardScaler(),
        }

        # Move to device
        for encoder in self.encoders.values():
            encoder.to(device)
        self.fusion.to(device)
        self.reasoning.to(device)

        # Set to eval mode
        self.eval()

    def eval(self):
        """Set all modules to evaluation mode."""
        for encoder in self.encoders.values():
            encoder.eval()
        self.fusion.eval()
        self.reasoning.eval()

    def extract_eeg_features(self, eeg_data: Dict) -> np.ndarray:
        """
        Extract features from EEG analysis.

        Args:
            eeg_data: Output from EEGService.analyze()

        Returns:
            Feature vector (10,)
        """
        features = np.array([
            eeg_data.get('delta_power', 0),
            eeg_data.get('theta_power', 0),
            eeg_data.get('alpha_power', 0),
            eeg_data.get('beta_power', 0),
            eeg_data.get('gamma_power', 0),
            eeg_data.get('mental_state_prob_stressed', 0),
            eeg_data.get('mental_state_prob_relaxed', 0),
            eeg_data.get('mental_state_prob_focused', 0),
            eeg_data.get('mental_state_prob_drowsy', 0),
            eeg_data.get('overall_brain_activity', 0),
        ])
        return features

    def extract_voice_features(self, voice_data: Dict) -> np.ndarray:
        """
        Extract features from voice analysis.

        Args:
            voice_data: Output from VoiceService.analyze()

        Returns:
            Feature vector (40,)
        """
        # Placeholder - actual implementation would use MFCCs, pitch, etc.
        features = np.zeros(40)
        features[0] = voice_data.get('emotion_confidence', 0)
        features[1] = voice_data.get('stress_score', 0)
        features[2] = voice_data.get('pitch_mean', 0)
        features[3] = voice_data.get('energy_mean', 0)
        # ... (populate with actual voice features)
        return features

    def extract_wearable_features(self, wearable_data: Dict) -> np.ndarray:
        """
        Extract features from wearable data.

        Args:
            wearable_data: Recent wearable metrics

        Returns:
            Feature vector (20,)
        """
        features = np.array([
            wearable_data.get('heart_rate', 70),
            wearable_data.get('hrv', 50),
            wearable_data.get('steps', 5000),
            wearable_data.get('calories_burned', 1800),
            wearable_data.get('sleep_hours', 7),
            wearable_data.get('deep_sleep_percent', 20),
            wearable_data.get('rem_sleep_percent', 25),
            wearable_data.get('resting_heart_rate', 60),
            wearable_data.get('stress_score', 50),
            wearable_data.get('body_battery', 70),
            wearable_data.get('spo2', 98),
            wearable_data.get('respiration_rate', 16),
            wearable_data.get('active_minutes', 30),
            wearable_data.get('sedentary_minutes', 600),
            wearable_data.get('elevation_gain', 10),
            wearable_data.get('temperature', 36.5),
            wearable_data.get('hydration_ml', 2000),
            wearable_data.get('weight_kg', 70),
            wearable_data.get('body_fat_percent', 20),
            wearable_data.get('muscle_mass_percent', 40),
        ])
        return features

    def fuse_modalities(
        self,
        modality_data: List[ModalityData]
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Fuse multiple modalities into unified embedding.

        Args:
            modality_data: List of modality data

        Returns:
            fused_embedding, modality_weights
        """
        if not modality_data:
            raise ValueError("No modality data provided")

        # Prepare embeddings
        embeddings_list = []
        modality_names = []
        confidences = []

        for data in modality_data:
            if data.modality_type not in self.encoders:
                print(f"⚠️  Unknown modality: {data.modality_type}, skipping")
                continue

            # Scale features if applicable
            features = data.features
            if data.modality_type in self.scalers:
                # Note: In production, scalers should be fit on training data
                # For now, we skip scaling or use simple normalization
                features = (features - features.mean()) / (features.std() + 1e-8)

            # Encode to common space
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
                embedding = self.encoders[data.modality_type](features_tensor)
                embeddings_list.append(embedding)

            modality_names.append(data.modality_type)
            confidences.append(data.confidence)

        if not embeddings_list:
            raise ValueError("No valid modalities to fuse")

        # Stack embeddings
        embeddings = torch.cat(embeddings_list, dim=0).unsqueeze(0)  # (1, n_modalities, emb_dim)

        # Confidence-based mask (all 1s for now, can be dynamic)
        mask = torch.ones(1, len(embeddings_list)).to(self.device)

        # Fuse with attention
        with torch.no_grad():
            fused_embedding, attention_weights = self.fusion(embeddings, mask)

        # Convert to numpy
        fused_embedding = fused_embedding.squeeze(0).cpu().numpy()
        attention_weights = attention_weights.squeeze(0).cpu().numpy()

        # Create weights dictionary
        weights = {
            name: float(weight)
            for name, weight in zip(modality_names, attention_weights)
        }

        return fused_embedding, weights

    def assess_wellness(
        self,
        modality_data: List[ModalityData],
        user_profile: Optional[Dict] = None
    ) -> MultiModalAssessment:
        """
        Perform comprehensive multi-modal wellness assessment.

        Args:
            modality_data: List of modality data
            user_profile: Optional user context (dosha, goals, etc.)

        Returns:
            MultiModalAssessment with unified insights
        """
        # Fuse modalities
        fused_embedding, modality_weights = self.fuse_modalities(modality_data)

        # Cross-modal reasoning
        with torch.no_grad():
            embedding_tensor = torch.FloatTensor(fused_embedding).unsqueeze(0).to(self.device)
            predictions = self.reasoning(embedding_tensor).squeeze(0).cpu().numpy()

        # Extract predictions
        wellness_score = float(np.clip(predictions[0] * 50 + 50, 0, 100))  # Scale to 0-100
        stress_level = float(np.clip(predictions[1] * 5 + 5, 0, 10))  # Scale to 0-10
        energy_level = float(np.clip(predictions[2] * 5 + 5, 0, 10))  # Scale to 0-10
        focus_score = float(np.clip(predictions[3] * 50 + 50, 0, 100))

        # Determine mental state from individual modality data
        mental_state = self._determine_mental_state(modality_data, predictions)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            wellness_score,
            stress_level,
            energy_level,
            mental_state,
            modality_data,
            user_profile
        )

        # Generate insights
        insights = self._generate_insights(modality_data, modality_weights)

        # Overall confidence (weighted average of modality confidences)
        overall_confidence = float(np.average(
            [d.confidence for d in modality_data],
            weights=[modality_weights.get(d.modality_type, 0.25) for d in modality_data]
        ))

        return MultiModalAssessment(
            overall_wellness_score=wellness_score,
            stress_level=stress_level,
            mental_state=mental_state,
            energy_level=energy_level,
            confidence=overall_confidence,
            contributing_modalities=[d.modality_type for d in modality_data],
            modality_weights=modality_weights,
            recommendations=recommendations,
            insights=insights,
            fusion_embedding=fused_embedding
        )

    def _determine_mental_state(
        self,
        modality_data: List[ModalityData],
        predictions: np.ndarray
    ) -> str:
        """Determine mental state from modality data and predictions."""

        # Check if EEG data available
        eeg_data = next((d for d in modality_data if d.modality_type == 'eeg'), None)
        if eeg_data and eeg_data.metadata:
            eeg_state = eeg_data.metadata.get('mental_state')
            if eeg_state:
                return eeg_state.lower()

        # Fallback to predictions
        if predictions[1] > 1.0:  # High stress
            return 'stressed'
        elif predictions[2] < -0.5:  # Low energy
            return 'drowsy'
        elif predictions[3] > 0.5:  # High focus
            return 'focused'
        else:
            return 'relaxed'

    def _generate_recommendations(
        self,
        wellness_score: float,
        stress_level: float,
        energy_level: float,
        mental_state: str,
        modality_data: List[ModalityData],
        user_profile: Optional[Dict]
    ) -> List[str]:
        """Generate personalized recommendations based on assessment."""

        recommendations = []

        # Stress-based recommendations
        if stress_level > 7:
            recommendations.append("Your stress levels are elevated. Consider a 5-minute breathing exercise now.")
            recommendations.append("Ashwagandha (300-600mg) can help reduce cortisol levels.")

        # Energy-based recommendations
        if energy_level < 4:
            recommendations.append("Low energy detected. Ensure you're getting 7-9 hours of sleep.")
            recommendations.append("Consider B-complex vitamins and CoQ10 for energy support.")

        # Mental state specific
        if mental_state == 'stressed':
            recommendations.append("High beta brain waves detected. Try a 10-minute meditation to shift to alpha waves.")
        elif mental_state == 'drowsy':
            recommendations.append("Elevated delta/theta waves. Exposure to bright light and light exercise can help alertness.")

        # Wellness score
        if wellness_score < 50:
            recommendations.append("Overall wellness score is low. Focus on sleep, nutrition, and stress management this week.")

        # Modality-specific
        for data in modality_data:
            if data.modality_type == 'wearable' and data.metadata:
                if data.metadata.get('sleep_hours', 7) < 6:
                    recommendations.append("Sleep duration is below optimal. Aim for 7-9 hours tonight.")

        return recommendations[:5]  # Top 5

    def _generate_insights(
        self,
        modality_data: List[ModalityData],
        modality_weights: Dict[str, float]
    ) -> List[str]:
        """Generate cross-modal insights."""

        insights = []

        # Identify dominant modality
        if modality_weights:
            dominant = max(modality_weights, key=modality_weights.get)
            weight = modality_weights[dominant]
            insights.append(f"Your {dominant} data had the strongest signal (weight: {weight:.2f}) in this assessment.")

        # Cross-modal correlations
        has_eeg = any(d.modality_type == 'eeg' for d in modality_data)
        has_wearable = any(d.modality_type == 'wearable' for d in modality_data)

        if has_eeg and has_wearable:
            insights.append("Both brain activity and physical metrics were considered for a comprehensive view.")

        # Data recency
        recent_count = sum(1 for d in modality_data if
                          (datetime.now() - d.timestamp).total_seconds() < 3600)
        if recent_count == len(modality_data):
            insights.append("All data is from the past hour, providing real-time assessment.")

        return insights


# Singleton instance
_fusion_engine = None

def get_fusion_engine() -> MultiModalFusionEngine:
    """Get singleton fusion engine."""
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = MultiModalFusionEngine()
    return _fusion_engine


# Example usage
if __name__ == "__main__":
    print("=== Multi-Modal Fusion Demo ===\n")

    # Create sample modality data
    modality_data = [
        ModalityData(
            modality_type='eeg',
            features=np.array([15, 20, 10, 65, 25, 0.7, 0.1, 0.15, 0.05, 80]),
            timestamp=datetime.now(),
            confidence=0.9,
            metadata={'mental_state': 'stressed'}
        ),
        ModalityData(
            modality_type='wearable',
            features=np.array([85, 45, 3000, 1500, 5.5, 15, 20, 70, 75, 50, 97, 18, 20, 700, 5, 36.8, 1500, 70, 22, 38]),
            timestamp=datetime.now() - timedelta(minutes=10),
            confidence=0.95,
            metadata={'sleep_hours': 5.5}
        ),
    ]

    # Get fusion engine
    engine = get_fusion_engine()

    # Assess wellness
    assessment = engine.assess_wellness(modality_data)

    # Print results
    print(f"Overall Wellness Score: {assessment.overall_wellness_score:.1f}/100")
    print(f"Stress Level: {assessment.stress_level:.1f}/10")
    print(f"Energy Level: {assessment.energy_level:.1f}/10")
    print(f"Mental State: {assessment.mental_state}")
    print(f"Confidence: {assessment.confidence:.2f}")

    print(f"\nModality Weights:")
    for mod, weight in assessment.modality_weights.items():
        print(f"  {mod}: {weight:.3f}")

    print(f"\nRecommendations:")
    for i, rec in enumerate(assessment.recommendations, 1):
        print(f"  {i}. {rec}")

    print(f"\nInsights:")
    for insight in assessment.insights:
        print(f"  • {insight}")
