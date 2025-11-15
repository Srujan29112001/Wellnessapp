"""
EEG Signal Processing Pipeline

Processes raw EEG signals through:
1. Filtering (bandpass, notch)
2. Artifact removal
3. Feature extraction (PSD, band powers)
4. Mental state classification
"""
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EEGProcessor:
    """
    EEG Signal Processor

    Handles filtering, feature extraction, and preprocessing of EEG signals
    """

    def __init__(
        self,
        sample_rate: int = 256,
        num_channels: int = 14,
        lowcut: float = 0.5,
        highcut: float = 50.0,
        notch_freq: float = 60.0  # Power line frequency (50Hz EU, 60Hz US)
    ):
        """
        Initialize EEG processor

        Args:
            sample_rate: Sampling rate in Hz
            num_channels: Number of EEG channels
            lowcut: Low cutoff frequency for bandpass filter
            highcut: High cutoff frequency for bandpass filter
            notch_freq: Notch filter frequency (power line)
        """
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.lowcut = lowcut
        self.highcut = highcut
        self.notch_freq = notch_freq

        # EEG frequency bands
        self.bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 50)
        }

    def bandpass_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter to EEG data

        Args:
            data: Raw EEG data (channels x samples)

        Returns:
            Filtered EEG data
        """
        nyquist = self.sample_rate / 2
        low = self.lowcut / nyquist
        high = self.highcut / nyquist

        # Design Butterworth bandpass filter
        b, a = signal.butter(4, [low, high], btype='band')

        # Apply filter to each channel
        filtered_data = np.zeros_like(data)
        for ch in range(data.shape[0]):
            filtered_data[ch] = signal.filtfilt(b, a, data[ch])

        return filtered_data

    def notch_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply notch filter to remove power line interference

        Args:
            data: EEG data (channels x samples)

        Returns:
            Notch-filtered data
        """
        nyquist = self.sample_rate / 2
        freq = self.notch_freq / nyquist
        quality = 30.0  # Q factor

        # Design notch filter
        b, a = signal.iirnotch(freq, quality, self.sample_rate)

        # Apply filter
        filtered_data = np.zeros_like(data)
        for ch in range(data.shape[0]):
            filtered_data[ch] = signal.filtfilt(b, a, data[ch])

        return filtered_data

    def remove_baseline(self, data: np.ndarray) -> np.ndarray:
        """
        Remove baseline drift

        Args:
            data: EEG data (channels x samples)

        Returns:
            Baseline-corrected data
        """
        return data - np.mean(data, axis=1, keepdims=True)

    def compute_psd(
        self,
        data: np.ndarray,
        window: str = 'hann'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Power Spectral Density using Welch's method

        Args:
            data: EEG data (channels x samples)
            window: Window function for Welch's method

        Returns:
            (frequencies, psd) where psd is (channels x frequencies)
        """
        nperseg = min(self.sample_rate * 2, data.shape[1])  # 2-second windows

        freqs, psd = signal.welch(
            data,
            fs=self.sample_rate,
            window=window,
            nperseg=nperseg,
            axis=1
        )

        return freqs, psd

    def compute_band_power(
        self,
        psd: np.ndarray,
        freqs: np.ndarray,
        band: Tuple[float, float]
    ) -> np.ndarray:
        """
        Compute power in a specific frequency band

        Args:
            psd: Power spectral density (channels x frequencies)
            freqs: Frequency array
            band: (low_freq, high_freq) tuple

        Returns:
            Band power for each channel
        """
        # Find frequency indices in band
        idx = np.logical_and(freqs >= band[0], freqs <= band[1])

        # Integrate PSD over frequency band
        band_power = np.trapz(psd[:, idx], freqs[idx], axis=1)

        return band_power

    def extract_features(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract comprehensive features from EEG data

        Args:
            data: Preprocessed EEG data (channels x samples)

        Returns:
            Dictionary of features
        """
        features = {}

        # Compute PSD
        freqs, psd = self.compute_psd(data)

        # Band powers
        for band_name, band_range in self.bands.items():
            band_power = self.compute_band_power(psd, freqs, band_range)
            features[f'{band_name}_power'] = band_power

        # Relative band powers (normalized)
        total_power = sum(features[f'{band}_power'] for band in self.bands.keys())
        for band_name in self.bands.keys():
            features[f'{band_name}_relative'] = features[f'{band_name}_power'] / (total_power + 1e-10)

        # Statistical features
        features['mean'] = np.mean(data, axis=1)
        features['std'] = np.std(data, axis=1)
        features['variance'] = np.var(data, axis=1)
        features['skewness'] = self._compute_skewness(data)
        features['kurtosis'] = self._compute_kurtosis(data)

        # Spectral features
        features['spectral_centroid'] = self._compute_spectral_centroid(psd, freqs)
        features['dominant_frequency'] = freqs[np.argmax(psd, axis=1)]

        return features

    def _compute_skewness(self, data: np.ndarray) -> np.ndarray:
        """Compute skewness for each channel"""
        mean = np.mean(data, axis=1, keepdims=True)
        std = np.std(data, axis=1, keepdims=True) + 1e-10
        skewness = np.mean(((data - mean) / std) ** 3, axis=1)
        return skewness

    def _compute_kurtosis(self, data: np.ndarray) -> np.ndarray:
        """Compute kurtosis for each channel"""
        mean = np.mean(data, axis=1, keepdims=True)
        std = np.std(data, axis=1, keepdims=True) + 1e-10
        kurtosis = np.mean(((data - mean) / std) ** 4, axis=1) - 3
        return kurtosis

    def _compute_spectral_centroid(self, psd: np.ndarray, freqs: np.ndarray) -> np.ndarray:
        """Compute spectral centroid (center of mass of spectrum)"""
        centroid = np.sum(psd * freqs, axis=1) / (np.sum(psd, axis=1) + 1e-10)
        return centroid

    def preprocess(self, raw_data: np.ndarray) -> np.ndarray:
        """
        Full preprocessing pipeline

        Args:
            raw_data: Raw EEG data (channels x samples)

        Returns:
            Preprocessed EEG data
        """
        logger.info(f"Preprocessing EEG data: shape {raw_data.shape}")

        # 1. Remove baseline
        data = self.remove_baseline(raw_data)

        # 2. Apply notch filter
        data = self.notch_filter(data)

        # 3. Apply bandpass filter
        data = self.bandpass_filter(data)

        logger.info("EEG preprocessing complete")
        return data

    def analyze(self, raw_data: np.ndarray) -> Dict[str, any]:
        """
        Complete EEG analysis pipeline

        Args:
            raw_data: Raw EEG data (channels x samples) or (samples,) for single channel

        Returns:
            Dictionary with analysis results
        """
        # Ensure 2D array
        if raw_data.ndim == 1:
            raw_data = raw_data.reshape(1, -1)

        # Preprocess
        preprocessed = self.preprocess(raw_data)

        # Extract features
        features = self.extract_features(preprocessed)

        # Compute aggregate metrics across channels
        results = {
            'band_powers': {
                band: float(np.mean(features[f'{band}_power']))
                for band in self.bands.keys()
            },
            'relative_powers': {
                band: float(np.mean(features[f'{band}_relative']))
                for band in self.bands.keys()
            },
            'features': features,
            'preprocessed_data': preprocessed
        }

        # Determine dominant band
        relative_powers = results['relative_powers']
        dominant_band = max(relative_powers, key=relative_powers.get)
        results['dominant_band'] = dominant_band

        logger.info(f"EEG analysis complete - Dominant band: {dominant_band}")

        return results

    @staticmethod
    def load_csv(file_path: str) -> np.ndarray:
        """
        Load EEG data from CSV file

        Expected format: Each row is a channel, or each column is a channel

        Args:
            file_path: Path to CSV file

        Returns:
            EEG data array (channels x samples)
        """
        df = pd.read_csv(file_path, header=None)
        data = df.values

        # If shape is (samples, channels), transpose
        if data.shape[0] > data.shape[1]:
            data = data.T

        logger.info(f"Loaded EEG data from {file_path}: shape {data.shape}")
        return data
