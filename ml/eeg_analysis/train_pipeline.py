"""
EEG Model Training Pipeline

Trains the ANN and SNN classifiers for EEG-based mental state detection
Includes data loading, preprocessing, training, and evaluation
"""
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import json
from datetime import datetime

from ml.eeg_analysis.processor import EEGProcessor
from ml.eeg_analysis.classifier import EEGClassifier
from ml.eeg_analysis.snn_classifier import SNNEEGClassifier

logger = logging.getLogger(__name__)


class EEGTrainingPipeline:
    """
    Complete training pipeline for EEG models

    Includes:
    - Data loading from public EEG datasets
    - Preprocessing and feature extraction
    - Model training (ANN and SNN)
    - Evaluation and metrics
    - Model saving and versioning
    """

    def __init__(
        self,
        data_dir: str = "/home/user/Wellnessapp/data/eeg_datasets",
        output_dir: str = "/home/user/Wellnessapp/models/eeg"
    ):
        """Initialize training pipeline"""
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.processor = EEGProcessor(sample_rate=256, num_channels=14)
        self.ann_classifier = None
        self.snn_classifier = None

        logger.info("EEG Training Pipeline initialized")

    def load_sample_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load sample EEG dataset

        In production, would load from:
        - PhysioNet datasets
        - OpenBCI recordings
        - Custom collected data

        For now, generates synthetic data for demonstration
        """
        logger.info("Loading sample EEG dataset...")

        # Synthetic data parameters
        num_samples = 1000  # Number of EEG epochs
        duration_seconds = 2  # Each epoch is 2 seconds
        sample_rate = 256
        num_channels = 14
        num_classes = 4  # stressed, focused, relaxed, drowsy

        samples_per_epoch = duration_seconds * sample_rate

        # Generate synthetic EEG-like data
        X = []
        y = []

        for i in range(num_samples):
            # Assign class
            class_id = i % num_classes

            # Generate signal with class-specific characteristics
            epoch = self._generate_synthetic_eeg(
                class_id, num_channels, samples_per_epoch, sample_rate
            )

            X.append(epoch)
            y.append(class_id)

        X = np.array(X)  # Shape: (num_samples, num_channels, samples_per_epoch)
        y = np.array(y)

        logger.info(f"Loaded dataset: X shape {X.shape}, y shape {y.shape}")

        return X, y

    def _generate_synthetic_eeg(
        self,
        class_id: int,
        num_channels: int,
        num_samples: int,
        sample_rate: int
    ) -> np.ndarray:
        """
        Generate synthetic EEG signal with class-specific characteristics

        Class 0 (Stressed): High beta power, low alpha
        Class 1 (Focused): Moderate alpha and beta
        Class 2 (Relaxed): High alpha, low beta
        Class 3 (Drowsy): High theta and delta, low beta
        """
        t = np.arange(num_samples) / sample_rate

        signal = np.zeros((num_channels, num_samples))

        for ch in range(num_channels):
            # Base noise
            noise = np.random.randn(num_samples) * 5

            # Class-specific frequency components
            if class_id == 0:  # Stressed - high beta (13-30 Hz)
                beta = np.sin(2 * np.pi * 20 * t) * 15
                alpha = np.sin(2 * np.pi * 10 * t) * 5
                signal[ch] = beta + alpha + noise

            elif class_id == 1:  # Focused - moderate alpha and beta
                beta = np.sin(2 * np.pi * 18 * t) * 10
                alpha = np.sin(2 * np.pi * 10 * t) * 10
                signal[ch] = beta + alpha + noise

            elif class_id == 2:  # Relaxed - high alpha (8-13 Hz)
                alpha = np.sin(2 * np.pi * 10 * t) * 20
                beta = np.sin(2 * np.pi * 15 * t) * 5
                signal[ch] = alpha + beta + noise

            elif class_id == 3:  # Drowsy - high theta (4-8 Hz) and delta (0.5-4 Hz)
                theta = np.sin(2 * np.pi * 6 * t) * 15
                delta = np.sin(2 * np.pi * 2 * t) * 10
                signal[ch] = theta + delta + noise

        return signal

    def preprocess_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess EEG data

        Steps:
        1. Filter signals (bandpass, notch)
        2. Extract features (band powers, PSD)
        3. Normalize features
        """
        logger.info("Preprocessing EEG data...")

        X_features = []

        for i, epoch in enumerate(X):
            # Process each epoch
            filtered = self.processor.filter_signal(epoch)

            # Extract features
            features = self.processor.extract_features(filtered)

            # Flatten features to 1D vector
            feature_vec = self._flatten_features(features)

            X_features.append(feature_vec)

            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(X)} epochs")

        X_features = np.array(X_features)

        # Normalize features
        X_features = self._normalize_features(X_features)

        logger.info(f"Preprocessing complete: X_features shape {X_features.shape}")

        return X_features, y

    def _flatten_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Flatten feature dictionary to 1D vector"""
        feature_vec = []

        # Band powers per channel
        for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            band_powers = features['band_powers'].get(band, [])
            feature_vec.extend(band_powers)

        # Global statistics
        feature_vec.append(features.get('dominant_frequency', 0))
        feature_vec.append(features.get('total_power', 0))

        return np.array(feature_vec)

    def _normalize_features(self, X: np.ndarray) -> np.ndarray:
        """Normalize features to zero mean and unit variance"""
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)

        # Avoid division by zero
        std[std == 0] = 1

        X_normalized = (X - mean) / std

        return X_normalized

    def train_ann_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50
    ) -> Dict[str, Any]:
        """
        Train ANN classifier

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            epochs: Number of training epochs

        Returns:
            Training history
        """
        logger.info("Training ANN classifier...")

        input_dim = X_train.shape[1]
        num_classes = len(np.unique(y_train))

        self.ann_classifier = EEGClassifier(
            input_dim=input_dim,
            num_classes=num_classes,
            model_path=str(self.output_dir / "ann_model.pth")
        )

        history = self.ann_classifier.train(
            X_train, y_train,
            X_val=X_val, y_val=y_val,
            epochs=epochs
        )

        logger.info("ANN training complete")

        return history

    def train_snn_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 50
    ) -> Dict[str, Any]:
        """
        Train SNN classifier

        Args:
            X_train: Training features
            y_train: Training labels
            epochs: Number of training epochs

        Returns:
            Training history
        """
        logger.info("Training SNN classifier...")

        input_dim = X_train.shape[1]
        num_classes = len(np.unique(y_train))

        self.snn_classifier = SNNEEGClassifier(
            input_dim=input_dim,
            num_classes=num_classes,
            model_path=str(self.output_dir / "snn_model.pth")
        )

        history = self.snn_classifier.train(
            X_train, y_train,
            epochs=epochs
        )

        logger.info("SNN training complete")

        return history

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate trained models

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Evaluation metrics
        """
        results = {}

        if self.ann_classifier:
            ann_metrics = self.ann_classifier.evaluate(X_test, y_test)
            results['ann'] = ann_metrics
            logger.info(f"ANN Test Accuracy: {ann_metrics['accuracy']:.3f}")

        if self.snn_classifier:
            snn_metrics = self.snn_classifier.evaluate(X_test, y_test)
            results['snn'] = snn_metrics
            logger.info(f"SNN Test Accuracy: {snn_metrics['accuracy']:.3f}")

        return results

    def save_models(self):
        """Save trained models"""
        if self.ann_classifier:
            self.ann_classifier.save_model()
            logger.info(f"ANN model saved to {self.ann_classifier.model_path}")

        if self.snn_classifier:
            self.snn_classifier.save_model()
            logger.info(f"SNN model saved to {self.snn_classifier.model_path}")

    def run_full_pipeline(self, use_snn: bool = True) -> Dict[str, Any]:
        """
        Run complete training pipeline

        Args:
            use_snn: Whether to train SNN in addition to ANN

        Returns:
            Training and evaluation results
        """
        logger.info("="*60)
        logger.info("Starting EEG Training Pipeline")
        logger.info("="*60)

        # 1. Load data
        X, y = self.load_sample_dataset()

        # 2. Split data
        from sklearn.model_selection import train_test_split
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42
        )

        logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

        # 3. Preprocess
        X_train_processed, y_train = self.preprocess_data(X_train, y_train)
        X_val_processed, y_val = self.preprocess_data(X_val, y_val)
        X_test_processed, y_test = self.preprocess_data(X_test, y_test)

        # 4. Train ANN
        ann_history = self.train_ann_model(
            X_train_processed, y_train,
            X_val_processed, y_val,
            epochs=30
        )

        # 5. Train SNN (optional)
        snn_history = None
        if use_snn:
            snn_history = self.train_snn_model(
                X_train_processed, y_train,
                epochs=30
            )

        # 6. Evaluate
        eval_results = self.evaluate(X_test_processed, y_test)

        # 7. Save models
        self.save_models()

        # 8. Save training metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "dataset_size": len(X),
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test),
            "num_channels": self.processor.num_channels,
            "sample_rate": self.processor.sample_rate,
            "num_classes": len(np.unique(y)),
            "class_names": ["stressed", "focused", "relaxed", "drowsy"],
            "eval_results": eval_results
        }

        metadata_path = self.output_dir / "training_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Training metadata saved to {metadata_path}")

        logger.info("="*60)
        logger.info("Training Pipeline Complete!")
        logger.info("="*60)

        return {
            "ann_history": ann_history,
            "snn_history": snn_history,
            "eval_results": eval_results,
            "metadata": metadata
        }


def main():
    """Main training script"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run pipeline
    pipeline = EEGTrainingPipeline()
    results = pipeline.run_full_pipeline(use_snn=True)

    print("\n" + "="*60)
    print("TRAINING RESULTS")
    print("="*60)
    print(f"ANN Test Accuracy: {results['eval_results']['ann']['accuracy']:.3f}")
    if 'snn' in results['eval_results']:
        print(f"SNN Test Accuracy: {results['eval_results']['snn']['accuracy']:.3f}")
    print("="*60)


if __name__ == "__main__":
    main()
