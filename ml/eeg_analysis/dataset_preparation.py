"""
EEG Dataset Preparation for Mental State Classification.

Supports multiple EEG datasets:
- DEAP: Database for Emotion Analysis using Physiological Signals
- SEED: SJTU Emotion EEG Dataset
- Custom synthetic data for testing

This script downloads, preprocesses, and prepares EEG data for training
mental state classifiers (stressed, relaxed, focused, drowsy).
"""

import os
import numpy as np
import pickle
from pathlib import Path
from typing import Tuple, Dict, List
import requests
from tqdm import tqdm
import h5py
from scipy.io import loadmat
from sklearn.model_selection import train_test_split
import warnings

warnings.filterwarnings('ignore')


class EEGDatasetPreparation:
    """Prepare EEG datasets for mental state classification."""

    def __init__(self, data_dir: str = "data/eeg_datasets"):
        """
        Initialize dataset preparation.

        Args:
            data_dir: Directory to store datasets
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.datasets_info = {
            "DEAP": {
                "url": "https://www.eecs.qmul.ac.uk/mmv/datasets/deap/",
                "description": "32-channel EEG, 40 subjects, emotion labels (valence, arousal)",
                "channels": 32,
                "sampling_rate": 128,
                "requires_request": True
            },
            "SEED": {
                "url": "https://bcmi.sjtu.edu.cn/home/seed/",
                "description": "62-channel EEG, 15 subjects, 3 emotions (positive, neutral, negative)",
                "channels": 62,
                "sampling_rate": 200,
                "requires_request": True
            }
        }

    def download_dataset(self, dataset_name: str) -> bool:
        """
        Download specified EEG dataset.

        Args:
            dataset_name: Name of dataset (DEAP, SEED)

        Returns:
            Success status
        """
        if dataset_name not in self.datasets_info:
            print(f"❌ Unknown dataset: {dataset_name}")
            print(f"Available datasets: {list(self.datasets_info.keys())}")
            return False

        info = self.datasets_info[dataset_name]

        if info["requires_request"]:
            print(f"\n📋 {dataset_name} Dataset Information:")
            print(f"   URL: {info['url']}")
            print(f"   Description: {info['description']}")
            print(f"\n⚠️  This dataset requires manual download:")
            print(f"   1. Visit {info['url']}")
            print(f"   2. Request access and download the data")
            print(f"   3. Extract to: {self.data_dir / dataset_name.lower()}/")
            print(f"\n💡 For testing, you can generate synthetic data instead:")
            print(f"   python -c \"from dataset_preparation import EEGDatasetPreparation; prep = EEGDatasetPreparation(); prep.generate_synthetic_dataset()\"")
            return False

        return True

    def generate_synthetic_dataset(
        self,
        n_subjects: int = 20,
        n_trials_per_class: int = 50,
        duration: int = 10,
        sampling_rate: int = 256,
        n_channels: int = 14
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic EEG data for testing and development.

        This creates realistic-looking EEG patterns for each mental state
        without needing real datasets.

        Args:
            n_subjects: Number of simulated subjects
            n_trials_per_class: Trials per mental state
            duration: Trial duration in seconds
            sampling_rate: Hz
            n_channels: EEG channels

        Returns:
            X: EEG data (n_trials, n_channels, n_samples)
            y: Labels (n_trials,) - 0: stressed, 1: relaxed, 2: focused, 3: drowsy
        """
        print("🔬 Generating synthetic EEG dataset...")

        n_samples = duration * sampling_rate
        mental_states = 4  # stressed, relaxed, focused, drowsy
        total_trials = n_subjects * n_trials_per_class * mental_states

        X = []
        y = []

        for subject in tqdm(range(n_subjects), desc="Generating subjects"):
            for state in range(mental_states):
                for trial in range(n_trials_per_class):
                    # Generate EEG-like signal for this trial
                    eeg_trial = self._generate_mental_state_eeg(
                        state,
                        n_channels,
                        n_samples,
                        sampling_rate
                    )

                    X.append(eeg_trial)
                    y.append(state)

        X = np.array(X)
        y = np.array(y)

        # Shuffle
        indices = np.arange(len(X))
        np.random.shuffle(indices)
        X = X[indices]
        y = y[indices]

        print(f"✅ Generated synthetic dataset:")
        print(f"   Shape: {X.shape}")
        print(f"   Classes: {mental_states} (0: stressed, 1: relaxed, 2: focused, 3: drowsy)")
        print(f"   Samples per class: {n_subjects * n_trials_per_class}")

        # Save
        save_path = self.data_dir / "synthetic"
        save_path.mkdir(exist_ok=True)

        np.save(save_path / "X_synthetic.npy", X)
        np.save(save_path / "y_synthetic.npy", y)

        print(f"💾 Saved to: {save_path}")

        return X, y

    def _generate_mental_state_eeg(
        self,
        state: int,
        n_channels: int,
        n_samples: int,
        sampling_rate: int
    ) -> np.ndarray:
        """
        Generate EEG signal characteristic of a mental state.

        Args:
            state: 0=stressed, 1=relaxed, 2=focused, 3=drowsy
            n_channels: Number of EEG channels
            n_samples: Samples per trial
            sampling_rate: Sampling frequency

        Returns:
            EEG signal (n_channels, n_samples)
        """
        t = np.arange(n_samples) / sampling_rate
        signal = np.zeros((n_channels, n_samples))

        # Define frequency bands
        delta = (0.5, 4)   # Deep sleep
        theta = (4, 8)     # Drowsiness, meditation
        alpha = (8, 13)    # Relaxation
        beta = (13, 30)    # Active thinking, anxiety
        gamma = (30, 50)   # High-level processing

        for ch in range(n_channels):
            # Base noise
            noise = np.random.randn(n_samples) * 5

            # Mental state-specific patterns
            if state == 0:  # Stressed
                # High beta (anxiety), low alpha
                beta_wave = 15 * np.sin(2 * np.pi * 20 * t + np.random.rand())
                alpha_wave = 5 * np.sin(2 * np.pi * 10 * t + np.random.rand())
                gamma_wave = 8 * np.sin(2 * np.pi * 35 * t + np.random.rand())
                signal[ch] = beta_wave + alpha_wave + gamma_wave + noise

            elif state == 1:  # Relaxed
                # High alpha, low beta
                alpha_wave = 20 * np.sin(2 * np.pi * 10 * t + np.random.rand())
                beta_wave = 5 * np.sin(2 * np.pi * 15 * t + np.random.rand())
                theta_wave = 8 * np.sin(2 * np.pi * 6 * t + np.random.rand())
                signal[ch] = alpha_wave + beta_wave + theta_wave + noise

            elif state == 2:  # Focused
                # Moderate beta, moderate alpha
                beta_wave = 12 * np.sin(2 * np.pi * 18 * t + np.random.rand())
                alpha_wave = 12 * np.sin(2 * np.pi * 10 * t + np.random.rand())
                gamma_wave = 10 * np.sin(2 * np.pi * 40 * t + np.random.rand())
                signal[ch] = beta_wave + alpha_wave + gamma_wave + noise

            elif state == 3:  # Drowsy
                # High delta, high theta, low alpha/beta
                delta_wave = 18 * np.sin(2 * np.pi * 2 * t + np.random.rand())
                theta_wave = 15 * np.sin(2 * np.pi * 6 * t + np.random.rand())
                alpha_wave = 5 * np.sin(2 * np.pi * 10 * t + np.random.rand())
                signal[ch] = delta_wave + theta_wave + alpha_wave + noise

            # Add some channel-specific variation
            signal[ch] += np.random.randn(n_samples) * 2

        return signal

    def prepare_deap_dataset(self, deap_dir: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare DEAP dataset for mental state classification.

        DEAP contains valence/arousal labels. We convert to mental states:
        - High arousal + Low valence = Stressed
        - Low arousal + High valence = Relaxed
        - High arousal + High valence = Focused
        - Low arousal + Low valence = Drowsy

        Args:
            deap_dir: Path to DEAP dataset directory

        Returns:
            X: EEG data, y: Mental state labels
        """
        print("📥 Loading DEAP dataset...")

        deap_path = Path(deap_dir)
        if not deap_path.exists():
            print(f"❌ DEAP directory not found: {deap_dir}")
            return None, None

        X_all = []
        y_all = []

        # DEAP has 32 participants (s01.dat to s32.dat)
        for subject_id in tqdm(range(1, 33), desc="Loading subjects"):
            file_path = deap_path / f"s{subject_id:02d}.dat"

            if not file_path.exists():
                continue

            # Load preprocessed data
            with open(file_path, 'rb') as f:
                data = pickle.load(f, encoding='latin1')

            # data['data']: (40 trials, 40 channels, 8064 samples)
            # data['labels']: (40 trials, 4 values: valence, arousal, dominance, liking)
            eeg_data = data['data'][:, :32, :]  # First 32 channels are EEG
            labels = data['labels']

            # Convert valence/arousal to mental states
            for trial_idx in range(eeg_data.shape[0]):
                valence = labels[trial_idx, 0]  # 1-9
                arousal = labels[trial_idx, 1]  # 1-9

                # Map to mental state
                if arousal > 5 and valence < 5:
                    state = 0  # Stressed
                elif arousal < 5 and valence > 5:
                    state = 1  # Relaxed
                elif arousal > 5 and valence > 5:
                    state = 2  # Focused
                else:  # arousal < 5 and valence < 5
                    state = 3  # Drowsy

                X_all.append(eeg_data[trial_idx])
                y_all.append(state)

        X = np.array(X_all)
        y = np.array(y_all)

        print(f"✅ DEAP dataset prepared:")
        print(f"   Shape: {X.shape}")
        print(f"   Classes: {len(np.unique(y))}")

        return X, y

    def save_prepared_dataset(
        self,
        X: np.ndarray,
        y: np.ndarray,
        dataset_name: str,
        test_size: float = 0.2
    ):
        """
        Save prepared dataset with train/test split.

        Args:
            X: EEG data
            y: Labels
            dataset_name: Name for saving
            test_size: Fraction for test set
        """
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )

        # Save
        save_dir = self.data_dir / dataset_name
        save_dir.mkdir(exist_ok=True)

        np.save(save_dir / "X_train.npy", X_train)
        np.save(save_dir / "X_test.npy", X_test)
        np.save(save_dir / "y_train.npy", y_train)
        np.save(save_dir / "y_test.npy", y_test)

        print(f"\n💾 Saved to {save_dir}:")
        print(f"   Train: {X_train.shape}, {y_train.shape}")
        print(f"   Test: {X_test.shape}, {y_test.shape}")

        # Save metadata
        metadata = {
            "n_channels": X.shape[1],
            "n_samples": X.shape[2],
            "n_classes": len(np.unique(y)),
            "classes": ["stressed", "relaxed", "focused", "drowsy"],
            "train_size": len(X_train),
            "test_size": len(X_test),
        }

        import json
        with open(save_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)


def main():
    """Main preparation workflow."""

    print("=== EEG Dataset Preparation ===\n")

    prep = EEGDatasetPreparation()

    # Menu
    print("Available options:")
    print("1. Generate synthetic dataset (for testing/development)")
    print("2. Prepare DEAP dataset (requires manual download)")
    print("3. Prepare SEED dataset (requires manual download)")
    print("4. Show dataset information")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == "1":
        # Generate synthetic
        X, y = prep.generate_synthetic_dataset(
            n_subjects=20,
            n_trials_per_class=50,
            duration=10,
            sampling_rate=256,
            n_channels=14
        )
        prep.save_prepared_dataset(X, y, "synthetic")

    elif choice == "2":
        # DEAP
        deap_dir = input("Enter DEAP dataset directory path: ").strip()
        X, y = prep.prepare_deap_dataset(deap_dir)
        if X is not None:
            prep.save_prepared_dataset(X, y, "deap")

    elif choice == "3":
        # SEED
        print("\n⚠️  SEED dataset preparation not yet implemented.")
        print("Please use synthetic dataset for now or prepare DEAP.")

    elif choice == "4":
        # Show info
        print("\n📊 Dataset Information:\n")
        for name, info in prep.datasets_info.items():
            print(f"{name}:")
            print(f"  URL: {info['url']}")
            print(f"  Description: {info['description']}")
            print(f"  Channels: {info['channels']}")
            print(f"  Sampling Rate: {info['sampling_rate']} Hz")
            print()

    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
