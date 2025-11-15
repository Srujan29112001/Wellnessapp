"""
Spiking Neural Network (SNN) for EEG Classification

SNNs are bio-inspired neural networks that process information using spikes
(discrete events) similar to biological neurons. They are particularly suited
for temporal data like EEG signals and are energy-efficient.

This implementation uses a simplified SNN approach for demonstration.
For production, consider using frameworks like Norse, BindsNET, or snnTorch.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class LIFNeuron(nn.Module):
    """
    Leaky Integrate-and-Fire (LIF) Neuron

    The basic building block of SNNs. Accumulates input current and
    fires a spike when threshold is reached.
    """

    def __init__(
        self,
        threshold: float = 1.0,
        tau_mem: float = 10.0,  # Membrane time constant
        reset: str = 'subtract'  # 'subtract' or 'zero'
    ):
        """
        Initialize LIF neuron

        Args:
            threshold: Spike threshold
            tau_mem: Membrane time constant
            reset: Reset behavior after spike
        """
        super(LIFNeuron, self).__init__()
        self.threshold = threshold
        self.tau_mem = tau_mem
        self.reset = reset

    def forward(self, input_current: torch.Tensor, membrane: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Single time step update

        Args:
            input_current: Input current at this timestep
            membrane: Current membrane potential

        Returns:
            (spikes, updated_membrane)
        """
        # Leak
        alpha = np.exp(-1 / self.tau_mem)
        membrane = alpha * membrane + input_current

        # Spike
        spikes = (membrane >= self.threshold).float()

        # Reset
        if self.reset == 'subtract':
            membrane = membrane - spikes * self.threshold
        else:  # zero
            membrane = membrane * (1 - spikes)

        return spikes, membrane


class SNNLayer(nn.Module):
    """
    Spiking Neural Network Layer

    Applies linear transformation + LIF neurons
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        threshold: float = 1.0,
        tau_mem: float = 10.0
    ):
        """
        Initialize SNN layer

        Args:
            in_features: Input dimension
            out_features: Output dimension
            threshold: Spike threshold
            tau_mem: Membrane time constant
        """
        super(SNNLayer, self).__init__()

        self.linear = nn.Linear(in_features, out_features)
        self.lif = LIFNeuron(threshold, tau_mem)
        self.out_features = out_features

    def forward(self, input_spikes: torch.Tensor, membrane: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for one timestep

        Args:
            input_spikes: Input spikes (batch, in_features)
            membrane: Current membrane state (batch, out_features)

        Returns:
            (output_spikes, updated_membrane)
        """
        # Linear transformation
        current = self.linear(input_spikes)

        # LIF dynamics
        spikes, membrane = self.lif(current, membrane)

        return spikes, membrane


class EEGClassifierSNN(nn.Module):
    """
    Spiking Neural Network for EEG Classification

    Processes EEG features through multiple SNN layers and
    uses spike counting for classification
    """

    def __init__(
        self,
        input_features: int = 70,
        hidden_dims: list = [128, 64],
        num_classes: int = 4,
        num_timesteps: int = 50,  # Number of simulation timesteps
        threshold: float = 1.0,
        tau_mem: float = 10.0
    ):
        """
        Initialize SNN classifier

        Args:
            input_features: Number of input features
            hidden_dims: List of hidden layer dimensions
            num_classes: Number of output classes
            num_timesteps: Number of timesteps to simulate
            threshold: Spike threshold
            tau_mem: Membrane time constant
        """
        super(EEGClassifierSNN, self).__init__()

        self.num_timesteps = num_timesteps
        self.hidden_dims = hidden_dims

        # Build layers
        layers = []
        prev_dim = input_features

        for hidden_dim in hidden_dims:
            layers.append(SNNLayer(prev_dim, hidden_dim, threshold, tau_mem))
            prev_dim = hidden_dim

        # Output layer
        layers.append(SNNLayer(prev_dim, num_classes, threshold, tau_mem))

        self.layers = nn.ModuleList(layers)

        # Input encoding parameters
        self.register_buffer('gain', torch.tensor(10.0))  # Encoding gain

    def encode_input(self, x: torch.Tensor) -> torch.Tensor:
        """
        Encode continuous input into spike trains using rate coding

        Higher input values = higher spike rate

        Args:
            x: Input features (batch, features)

        Returns:
            Spike trains (timesteps, batch, features)
        """
        batch_size = x.shape[0]
        num_features = x.shape[1]

        # Normalize and scale
        x_scaled = torch.relu(x * self.gain)  # Ensure positive

        # Generate Poisson spike trains
        spike_trains = []
        for t in range(self.num_timesteps):
            # Stochastic spiking based on rate
            spikes = (torch.rand_like(x_scaled) < x_scaled / self.num_timesteps).float()
            spike_trains.append(spikes)

        spike_trains = torch.stack(spike_trains, dim=0)  # (timesteps, batch, features)

        return spike_trains

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through SNN

        Args:
            x: Input features (batch, features)

        Returns:
            Spike counts for each class (batch, num_classes)
        """
        batch_size = x.shape[0]

        # Encode input to spikes
        input_spike_trains = self.encode_input(x)

        # Initialize membrane potentials
        membranes = [torch.zeros(batch_size, layer.out_features, device=x.device)
                     for layer in self.layers]

        # Accumulate output spikes
        output_spike_count = torch.zeros(batch_size, self.layers[-1].out_features, device=x.device)

        # Simulate over time
        for t in range(self.num_timesteps):
            spikes = input_spike_trains[t]

            # Propagate through layers
            for i, layer in enumerate(self.layers):
                spikes, membranes[i] = layer(spikes, membranes[i])

            # Accumulate output spikes
            output_spike_count += spikes

        # Spike count represents class evidence
        return output_spike_count

    def predict(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict class from input

        Args:
            x: Input features (batch, features)

        Returns:
            (predictions, probabilities)
        """
        spike_counts = self.forward(x)

        # Normalize to probabilities
        probabilities = torch.softmax(spike_counts, dim=1)

        # Get predictions
        predictions = torch.argmax(probabilities, dim=1)

        return predictions, probabilities


class SNNMentalStateClassifier:
    """
    High-level SNN interface for EEG mental state classification
    """

    STATES = ['stressed', 'focused', 'relaxed', 'drowsy']

    def __init__(
        self,
        model_path: str = None,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Initialize SNN classifier

        Args:
            model_path: Path to saved model
            device: Device for inference
        """
        self.device = device

        # Initialize SNN model
        self.model = EEGClassifierSNN(
            input_features=70,
            hidden_dims=[128, 64],
            num_classes=4,
            num_timesteps=50
        ).to(device)

        # Load weights if provided
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=device))
                logger.info(f"Loaded SNN classifier from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load SNN model: {e}")

        self.model.eval()

    def features_to_tensor(self, features: dict) -> torch.Tensor:
        """Convert features to tensor"""
        feature_list = []
        bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']

        for band in bands:
            if f'{band}_relative' in features:
                feature_list.append(features[f'{band}_relative'])

        feature_vector = np.concatenate(feature_list)
        tensor = torch.FloatTensor(feature_vector).unsqueeze(0)

        return tensor.to(self.device)

    def predict(self, features: dict) -> dict:
        """
        Predict mental state using SNN

        Args:
            features: EEG features

        Returns:
            Prediction results
        """
        input_tensor = self.features_to_tensor(features)

        with torch.no_grad():
            predictions, probabilities = self.model.predict(input_tensor)

        probs = probabilities.cpu().numpy()[0]
        predicted_idx = predictions.cpu().numpy()[0]

        results = {
            'mental_state': self.STATES[predicted_idx],
            'confidence': float(probs[predicted_idx]),
            'probabilities': {
                state: float(prob)
                for state, prob in zip(self.STATES, probs)
            },
            'stress': float(probs[0]),
            'focus': float(probs[1]),
            'relaxation': float(probs[2]),
            'drowsiness': float(probs[3]),
            'method': 'SNN'
        }

        logger.info(f"SNN predicted: {results['mental_state']} (confidence: {results['confidence']:.2f})")

        return results


if __name__ == "__main__":
    # Demo
    print("Testing Spiking Neural Network for EEG Classification")

    snn = EEGClassifierSNN(input_features=70, hidden_dims=[128, 64], num_classes=4)

    # Test forward pass
    dummy_input = torch.randn(2, 70)  # Batch of 2
    output = snn(dummy_input)

    print(f"Input shape: {dummy_input.shape}")
    print(f"Output spike counts: {output.shape}")
    print(f"Sample output: {output[0]}")

    # Predict
    preds, probs = snn.predict(dummy_input)
    print(f"Predictions: {preds}")
    print(f"Probabilities: {probs}")
