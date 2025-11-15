"""
Tests for EEG Analysis Module
"""
import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from ml.eeg_analysis.processor import EEGProcessor
from ml.eeg_analysis.classifier import EEGClassifier


class TestEEGProcessor:
    """Test EEG signal processing"""

    def setup_method(self):
        """Setup test fixtures"""
        self.processor = EEGProcessor()

    def test_load_eeg_data(self):
        """Test loading EEG data from CSV"""
        # Create sample data
        sample_data = np.random.randn(14, 2560)  # 14 channels, 10s @ 256Hz

        # Process
        result = self.processor.process_eeg(sample_data)

        assert result is not None
        assert "features" in result
        assert "band_powers" in result

    def test_band_power_extraction(self):
        """Test frequency band power extraction"""
        # Create signal with known frequency
        duration = 10
        sample_rate = 256
        t = np.linspace(0, duration, duration * sample_rate)

        # 10 Hz signal (alpha band)
        signal = np.sin(2 * np.pi * 10 * t)

        features = self.processor._extract_features(signal, sample_rate)

        # Alpha power should be highest
        assert "alpha" in features
        assert features["alpha"] > features.get("delta", 0)

    def test_mental_state_classification(self):
        """Test mental state classification"""
        sample_data = np.random.randn(14, 2560)

        result = self.processor.analyze_eeg_file(sample_data)

        assert "stress" in result
        assert "focus" in result
        assert "relaxation" in result
        assert "drowsiness" in result

        # Probabilities should sum to ~1
        total = sum([result["stress"], result["focus"],
                    result["relaxation"], result["drowsiness"]])
        assert 0.9 <= total <= 1.1


class TestEEGClassifier:
    """Test EEG classifier model"""

    def test_classifier_initialization(self):
        """Test model initialization"""
        model = EEGClassifier(n_channels=14, n_features=29, n_classes=4)

        assert model is not None
        assert hasattr(model, 'conv1')
        assert hasattr(model, 'lstm')

    def test_forward_pass(self):
        """Test model forward pass"""
        import torch

        model = EEGClassifier(n_channels=14, n_features=29, n_classes=4)
        model.eval()

        # Create dummy input
        batch_size = 4
        x = torch.randn(batch_size, 14, 29)

        # Forward pass
        with torch.no_grad():
            output = model(x)

        assert output.shape == (batch_size, 4)
        # Should be probabilities (0-1)
        assert torch.all(output >= 0) and torch.all(output <= 1)


class TestIntegration:
    """Integration tests"""

    def test_end_to_end_eeg_analysis(self):
        """Test complete EEG analysis pipeline"""
        # Generate sample EEG
        sample_eeg = np.random.randn(14, 2560)

        # Process
        processor = EEGProcessor()
        result = processor.analyze_eeg_file(sample_eeg)

        # Verify output format
        assert isinstance(result, dict)
        assert "stress" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
