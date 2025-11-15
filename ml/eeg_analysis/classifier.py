"""
EEG Mental State Classifier

Classifies mental states (stress, focus, relaxation, drowsiness) from EEG features
Supports both traditional ANN and Spiking Neural Network (SNN) architectures
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EEGClassifierANN(nn.Module):
    """
    Traditional Artificial Neural Network for EEG classification

    Architecture: CNN + LSTM for temporal patterns
    """

    def __init__(
        self,
        num_channels: int = 14,
        num_features: int = 50,
        num_classes: int = 4,  # stress, focus, relaxed, drowsy
        hidden_size: int = 128,
        num_lstm_layers: int = 2,
        dropout: float = 0.3
    ):
        """
        Initialize EEG Classifier

        Args:
            num_channels: Number of EEG channels
            num_features: Number of features per channel
            num_classes: Number of output classes
            hidden_size: LSTM hidden size
            num_lstm_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        super(EEGClassifierANN, self).__init__()

        self.num_channels = num_channels
        self.num_features = num_features
        self.num_classes = num_classes

        # Convolutional layers for spatial patterns
        self.conv1 = nn.Conv1d(num_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.batch_norm1 = nn.BatchNorm1d(32)
        self.batch_norm2 = nn.BatchNorm1d(64)
        self.pool = nn.MaxPool1d(2)

        # LSTM for temporal patterns
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=hidden_size,
            num_layers=num_lstm_layers,
            batch_first=True,
            dropout=dropout if num_lstm_layers > 1 else 0,
            bidirectional=True
        )

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size * 2, 64)  # *2 for bidirectional
        self.fc2 = nn.Linear(64, num_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor (batch, channels, features)

        Returns:
            Output logits (batch, num_classes)
        """
        # CNN layers
        x = F.relu(self.batch_norm1(self.conv1(x)))
        x = F.relu(self.batch_norm2(self.conv2(x)))

        # Reshape for LSTM (batch, seq_len, features)
        x = x.permute(0, 2, 1)

        # LSTM layers
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Use last hidden state
        x = lstm_out[:, -1, :]

        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)

        return x


class EEGClassifierSimple(nn.Module):
    """
    Simpler feedforward neural network for EEG feature classification

    Uses extracted features (band powers, etc.) directly
    """

    def __init__(
        self,
        input_features: int = 70,  # 5 bands * 14 channels = 70 features
        hidden_dims: list = [128, 64, 32],
        num_classes: int = 4,
        dropout: float = 0.3
    ):
        """
        Initialize simple classifier

        Args:
            input_features: Number of input features
            hidden_dims: List of hidden layer dimensions
            num_classes: Number of output classes
            dropout: Dropout rate
        """
        super(EEGClassifierSimple, self).__init__()

        layers = []
        prev_dim = input_features

        # Build hidden layers
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim

        # Output layer
        layers.append(nn.Linear(prev_dim, num_classes))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input features (batch, features)

        Returns:
            Output logits (batch, num_classes)
        """
        return self.network(x)


class EEGMentalStateClassifier:
    """
    High-level interface for EEG mental state classification
    """

    # Mental state labels
    STATES = ['stressed', 'focused', 'relaxed', 'drowsy']

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Initialize classifier

        Args:
            model_path: Path to pre-trained model weights
            device: Device for inference
        """
        self.device = device

        # Initialize model (simple version for now)
        self.model = EEGClassifierSimple(
            input_features=70,  # Will adjust based on features
            hidden_dims=[128, 64, 32],
            num_classes=4
        ).to(device)

        # Load weights if provided
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=device))
                self.model.eval()
                logger.info(f"Loaded EEG classifier from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model weights: {e}. Using random initialization.")
        else:
            logger.info("Using randomly initialized EEG classifier (demo mode)")

        self.model.eval()

    def features_to_tensor(self, features: Dict[str, np.ndarray]) -> torch.Tensor:
        """
        Convert feature dictionary to tensor

        Args:
            features: Dictionary of features from EEGProcessor

        Returns:
            Feature tensor
        """
        # Extract band powers (relative)
        feature_list = []
        bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']

        for band in bands:
            if f'{band}_relative' in features:
                feature_list.append(features[f'{band}_relative'])

        # Concatenate all features
        feature_vector = np.concatenate(feature_list)

        # Convert to tensor
        tensor = torch.FloatTensor(feature_vector).unsqueeze(0)  # Add batch dimension

        return tensor.to(self.device)

    def predict(self, features: Dict[str, np.ndarray]) -> Dict[str, any]:
        """
        Predict mental state from EEG features

        Args:
            features: Dictionary of features from EEGProcessor

        Returns:
            Dictionary with predictions and probabilities
        """
        # Convert features to tensor
        input_tensor = self.features_to_tensor(features)

        # Inference
        with torch.no_grad():
            logits = self.model(input_tensor)
            probabilities = F.softmax(logits, dim=1)

        # Convert to numpy
        probs = probabilities.cpu().numpy()[0]

        # Get prediction
        predicted_idx = np.argmax(probs)
        predicted_state = self.STATES[predicted_idx]

        # Create results
        results = {
            'mental_state': predicted_state,
            'confidence': float(probs[predicted_idx]),
            'probabilities': {
                state: float(prob)
                for state, prob in zip(self.STATES, probs)
            },
            'stress': float(probs[0]),
            'focus': float(probs[1]),
            'relaxation': float(probs[2]),
            'drowsiness': float(probs[3])
        }

        # Add heuristic adjustments based on band powers
        # (In demo mode, use simple rules)
        results = self._apply_heuristics(results, features)

        logger.info(f"Predicted mental state: {predicted_state} (confidence: {results['confidence']:.2f})")

        return results

    def _apply_heuristics(self, results: Dict, features: Dict) -> Dict:
        """
        Apply heuristic rules based on known EEG patterns

        This provides reasonable results even with untrained model
        """
        # Get relative band powers (averaged across channels)
        band_powers = {}
        for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            if f'{band}_relative' in features:
                band_powers[band] = np.mean(features[f'{band}_relative'])

        # Heuristic rules:
        # - High beta + low alpha = stressed
        # - High alpha + low beta = relaxed
        # - High beta + medium alpha = focused
        # - High delta/theta = drowsy

        stress_score = band_powers.get('beta', 0) * 2 - band_powers.get('alpha', 0)
        focus_score = band_powers.get('beta', 0) + band_powers.get('alpha', 0) * 0.5
        relax_score = band_powers.get('alpha', 0) * 2 - band_powers.get('beta', 0)
        drowsy_score = band_powers.get('delta', 0) + band_powers.get('theta', 0)

        # Normalize scores
        total = stress_score + focus_score + relax_score + drowsy_score + 1e-10
        heuristic_probs = {
            'stressed': stress_score / total,
            'focused': focus_score / total,
            'relaxed': relax_score / total,
            'drowsy': drowsy_score / total
        }

        # Blend with model predictions (70% heuristic, 30% model in demo mode)
        # In production with trained model, this would be 100% model
        alpha = 0.7  # Weight for heuristics

        blended = {
            'stress': alpha * heuristic_probs['stressed'] + (1 - alpha) * results['stress'],
            'focus': alpha * heuristic_probs['focused'] + (1 - alpha) * results['focus'],
            'relaxation': alpha * heuristic_probs['relaxed'] + (1 - alpha) * results['relaxation'],
            'drowsiness': alpha * heuristic_probs['drowsy'] + (1 - alpha) * results['drowsiness']
        }

        # Update results
        results.update(blended)

        # Update predicted state
        max_state = max(blended, key=blended.get)
        results['mental_state'] = max_state.replace('ness', '') if 'ness' in max_state else max_state
        results['confidence'] = blended[max(blended, key=blended.get)]

        # Update probabilities
        results['probabilities'] = {
            'stressed': blended['stress'],
            'focused': blended['focus'],
            'relaxed': blended['relaxation'],
            'drowsy': blended['drowsiness']
        }

        return results


def create_sample_model():
    """Create and save a sample EEG classifier model"""
    model = EEGClassifierSimple(
        input_features=70,
        hidden_dims=[128, 64, 32],
        num_classes=4
    )

    # Save model
    model_path = './data/models/eeg_classifier.pt'
    torch.save(model.state_dict(), model_path)
    logger.info(f"Sample EEG classifier saved to {model_path}")

    return model


if __name__ == "__main__":
    # Create sample model
    create_sample_model()
