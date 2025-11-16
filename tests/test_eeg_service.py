"""
Tests for EEG Analysis Service
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.services.eeg_service import EEGService


@pytest.fixture
def eeg_service():
    """Create EEG service instance"""
    return EEGService()


@pytest.fixture
def sample_eeg_file():
    """Path to sample EEG file"""
    return Path("/home/user/Wellnessapp/data/sample_eeg/eeg_sample_relaxed.csv")


class TestEEGService:
    """Test EEG analysis service"""

    def test_load_eeg_from_file(self, eeg_service, sample_eeg_file):
        """Test loading EEG data from CSV file"""
        if not sample_eeg_file.exists():
            pytest.skip("Sample EEG file not found")

        result = eeg_service.analyze_eeg_from_file(
            str(sample_eeg_file),
            user_id="test_user"
        )

        assert result is not None
        assert "mental_state" in result
        assert "band_powers" in result
        assert "stress_level" in result

    def test_mental_state_classification(self, eeg_service, sample_eeg_file):
        """Test mental state is classified correctly"""
        if not sample_eeg_file.exists():
            pytest.skip("Sample EEG file not found")

        result = eeg_service.analyze_eeg_from_file(
            str(sample_eeg_file),
            user_id="test_user"
        )

        mental_state = result["mental_state"]

        assert "stress" in mental_state
        assert "focus" in mental_state
        assert "relaxation" in mental_state
        assert "drowsiness" in mental_state

        # All probabilities should sum to ~1
        total = sum(mental_state.values())
        assert 0.9 <= total <= 1.1

    def test_band_powers(self, eeg_service, sample_eeg_file):
        """Test band power extraction"""
        if not sample_eeg_file.exists():
            pytest.skip("Sample EEG file not found")

        result = eeg_service.analyze_eeg_from_file(
            str(sample_eeg_file),
            user_id="test_user"
        )

        band_powers = result["band_powers"]

        # Check all bands are present
        expected_bands = ["delta", "theta", "alpha", "beta", "gamma"]
        for band in expected_bands:
            assert band in band_powers
            assert isinstance(band_powers[band], (int, float))
            assert band_powers[band] >= 0

    def test_recommendations_generated(self, eeg_service, sample_eeg_file):
        """Test that recommendations are generated"""
        if not sample_eeg_file.exists():
            pytest.skip("Sample EEG file not found")

        result = eeg_service.analyze_eeg_from_file(
            str(sample_eeg_file),
            user_id="test_user"
        )

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

    def test_different_mental_states(self, eeg_service):
        """Test classification of different mental states"""
        states = ["relaxed", "stressed", "focused", "drowsy"]
        results = {}

        for state in states:
            file_path = Path(f"/home/user/Wellnessapp/data/sample_eeg/eeg_sample_{state}.csv")

            if not file_path.exists():
                continue

            result = eeg_service.analyze_eeg_from_file(
                str(file_path),
                user_id="test_user"
            )

            results[state] = result["mental_state"]

        # If we have results, check they're different
        if len(results) > 1:
            # Relaxed should have higher relaxation score
            if "relaxed" in results:
                assert results["relaxed"]["relaxation"] > 0.3

            # Stressed should have higher stress score
            if "stressed" in results:
                assert results["stressed"]["stress"] > 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
