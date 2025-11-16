"""
Tests for EEG Analysis
"""

import pytest
import numpy as np
from ml.eeg_analysis.processor import EEGProcessor
from ml.eeg_analysis.classifier import EEGClassifier


@pytest.fixture
def eeg_processor():
    """Create EEG processor instance"""
    return EEGProcessor()


@pytest.fixture
def eeg_classifier():
    """Create EEG classifier instance"""
    return EEGClassifier()


@pytest.fixture
def sample_eeg_data():
    """Generate sample EEG data"""
    # 14 channels, 2560 samples (10 seconds at 256 Hz)
    num_channels = 14
    num_samples = 2560
    return np.random.randn(num_channels, num_samples) * 10  # μV scale


def test_bandpass_filter(eeg_processor, sample_eeg_data):
    """Test bandpass filtering"""
    filtered = eeg_processor.bandpass_filter(sample_eeg_data[0])

    assert filtered.shape == sample_eeg_data[0].shape
    assert not np.array_equal(filtered, sample_eeg_data[0])  # Should be different


def test_notch_filter(eeg_processor, sample_eeg_data):
    """Test notch filtering"""
    filtered = eeg_processor.notch_filter(sample_eeg_data[0])

    assert filtered.shape == sample_eeg_data[0].shape


def test_compute_band_powers(eeg_processor, sample_eeg_data):
    """Test band power computation"""
    band_powers = eeg_processor.compute_band_powers(sample_eeg_data[0])

    assert "delta" in band_powers
    assert "theta" in band_powers
    assert "alpha" in band_powers
    assert "beta" in band_powers
    assert "gamma" in band_powers

    # All powers should be positive
    for power in band_powers.values():
        assert power >= 0


def test_extract_features(eeg_processor, sample_eeg_data):
    """Test feature extraction"""
    features = eeg_processor.extract_features(sample_eeg_data)

    assert isinstance(features, np.ndarray)
    assert len(features.shape) == 1  # Should be 1D feature vector
    assert features.shape[0] > 0  # Should have features


def test_classify_mental_state(eeg_classifier):
    """Test mental state classification"""
    # Create dummy features
    features = np.random.randn(100)

    state = eeg_classifier.classify_mental_state(features)

    assert "stress" in state
    assert "focus" in state
    assert "relaxation" in state
    assert "drowsiness" in state

    # All probabilities should be between 0 and 1
    for prob in state.values():
        assert 0 <= prob <= 1


def test_preprocess_pipeline(eeg_processor, sample_eeg_data):
    """Test full preprocessing pipeline"""
    processed = eeg_processor.preprocess(sample_eeg_data)

    assert processed.shape == sample_eeg_data.shape
    # Should have removed extreme values
    assert np.abs(processed).max() < np.abs(sample_eeg_data).max() * 2
