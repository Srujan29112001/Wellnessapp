"""
Tests for EEG Analysis Module
"""

import pytest
import numpy as np
from ml.eeg_analysis.processor import EEGProcessor
from ml.eeg_analysis.classifier import EEGClassifier


class TestEEGProcessor:
    """Test EEG signal processing"""

    @pytest.fixture
    def processor(self):
        """Create EEG processor instance"""
        return EEGProcessor(sample_rate=256, num_channels=14)

    @pytest.fixture
    def sample_eeg_data(self):
        """Generate sample EEG data"""
        # 14 channels, 2 seconds at 256 Hz
        return np.random.randn(14, 512)

    def test_bandpass_filter(self, processor, sample_eeg_data):
        """Test bandpass filtering"""
        filtered = processor.apply_bandpass_filter(sample_eeg_data)

        assert filtered.shape == sample_eeg_data.shape
        assert not np.array_equal(filtered, sample_eeg_data)  # Should be different

    def test_feature_extraction(self, processor, sample_eeg_data):
        """Test feature extraction"""
        features = processor.extract_features(sample_eeg_data)

        assert "band_powers" in features
        assert "delta" in features["band_powers"]
        assert "theta" in features["band_powers"]
        assert "alpha" in features["band_powers"]
        assert "beta" in features["band_powers"]
        assert "gamma" in features["band_powers"]

    def test_psd_calculation(self, processor, sample_eeg_data):
        """Test PSD calculation"""
        freqs, psd = processor.compute_psd(sample_eeg_data[0])

        assert len(freqs) == len(psd)
        assert np.all(psd >= 0)  # PSD should be positive

    def test_preprocess_pipeline(self, processor, sample_eeg_data):
        """Test full preprocessing pipeline"""
        processed = processor.preprocess(sample_eeg_data)

        assert processed.shape == sample_eeg_data.shape


class TestEEGClassifier:
    """Test EEG classification model"""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance"""
        return EEGClassifier(
            num_channels=14,
            num_features=5,
            num_classes=4,
            hidden_dim=64
        )

    @pytest.fixture
    def sample_features(self):
        """Generate sample features"""
        # Batch of 10, 14 channels, 5 features
        return np.random.randn(10, 14, 5).astype(np.float32)

    def test_forward_pass(self, classifier, sample_features):
        """Test model forward pass"""
        import torch

        inputs = torch.FloatTensor(sample_features)
        outputs = classifier(inputs)

        assert outputs.shape == (10, 4)  # Batch size 10, 4 classes
        assert torch.all(outputs >= 0)  # Softmax outputs should be positive

    def test_predict_mental_state(self, classifier, sample_features):
        """Test mental state prediction"""
        state = classifier.predict_mental_state(sample_features[0])

        assert state in ["focused", "relaxed", "stressed", "drowsy"]

    def test_model_parameters(self, classifier):
        """Test model has trainable parameters"""
        params = sum(p.numel() for p in classifier.parameters())
        assert params > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
