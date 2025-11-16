"""
EEG Model Training Pipeline
Train and evaluate EEG mental state classification models
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from pathlib import Path
import json
import logging
from typing import Tuple, Dict, List
from datetime import datetime

# MLOps imports
try:
    import mlflow
    import mlflow.pytorch
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow not available")

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    logging.warning("Weights & Biases not available")

from ml.eeg_analysis.classifier import EEGClassifier
from ml.eeg_analysis.processor import EEGProcessor

logger = logging.getLogger(__name__)


class EEGDataset(Dataset):
    """PyTorch Dataset for EEG data"""

    def __init__(
        self,
        features: np.ndarray,
        labels: np.ndarray
    ):
        """
        Args:
            features: EEG features (N, num_channels, num_features)
            labels: Mental state labels (N,)
        """
        self.features = torch.FloatTensor(features)
        self.labels = torch.LongTensor(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class EEGTrainer:
    """
    Training pipeline for EEG classification models
    """

    def __init__(
        self,
        model_config: Dict,
        use_mlflow: bool = True,
        use_wandb: bool = False,
        experiment_name: str = "eeg_classification"
    ):
        """
        Initialize trainer

        Args:
            model_config: Model configuration
            use_mlflow: Use MLflow tracking
            use_wandb: Use Weights & Biases
            experiment_name: Experiment name
        """
        self.model_config = model_config
        self.experiment_name = experiment_name

        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Training on device: {self.device}")

        # MLOps setup
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        self.use_wandb = use_wandb and WANDB_AVAILABLE

        if self.use_mlflow:
            mlflow.set_experiment(experiment_name)

        if self.use_wandb:
            wandb.init(project=experiment_name)

    def prepare_data(
        self,
        eeg_signals_list: List[np.ndarray],
        labels_list: List[int],
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Prepare data loaders

        Args:
            eeg_signals_list: List of EEG signal arrays (each N_samples x N_channels)
            labels_list: List of labels
            test_size: Test set proportion
            val_size: Validation set proportion

        Returns:
            train_loader, val_loader, test_loader
        """
        logger.info(f"Preparing data: {len(eeg_signals_list)} samples")

        # Process EEG signals to extract features
        processor = EEGProcessor(
            sample_rate=self.model_config.get("sample_rate", 256),
            num_channels=self.model_config.get("num_channels", 14)
        )

        all_features = []
        valid_labels = []

        for eeg_data, label in zip(eeg_signals_list, labels_list):
            try:
                # Preprocess
                filtered = processor.preprocess(eeg_data)

                # Extract features
                features = processor.extract_features(filtered)

                # Flatten features for each channel
                feature_array = np.array([
                    list(features["band_powers"][band].values())
                    for band in ["delta", "theta", "alpha", "beta", "gamma"]
                ]).T  # Shape: (num_channels, 5)

                all_features.append(feature_array)
                valid_labels.append(label)

            except Exception as e:
                logger.error(f"Error processing sample: {e}")

        all_features = np.array(all_features)  # Shape: (N, num_channels, num_features)
        valid_labels = np.array(valid_labels)

        logger.info(f"Extracted features shape: {all_features.shape}")

        # Train/val/test split
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            all_features, valid_labels, test_size=test_size, random_state=42, stratify=valid_labels
        )

        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_size/(1-test_size), random_state=42, stratify=y_train_val
        )

        # Create datasets
        train_dataset = EEGDataset(X_train, y_train)
        val_dataset = EEGDataset(X_val, y_val)
        test_dataset = EEGDataset(X_test, y_test)

        # Create data loaders
        batch_size = self.model_config.get("batch_size", 32)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

        logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")

        return train_loader, val_loader, test_loader

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 50,
        learning_rate: float = 0.001,
        save_path: Optional[str] = None
    ) -> Dict:
        """
        Train the model

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            save_path: Path to save best model

        Returns:
            Training history
        """
        # Initialize model
        model = EEGClassifier(
            num_channels=self.model_config.get("num_channels", 14),
            num_features=5,  # 5 frequency bands
            num_classes=self.model_config.get("num_classes", 4),
            hidden_dim=self.model_config.get("hidden_dim", 128)
        )
        model.to(self.device)

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )

        # Training history
        history = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": []
        }

        best_val_acc = 0.0

        # Log hyperparameters
        if self.use_mlflow:
            mlflow.log_params({
                "num_epochs": num_epochs,
                "learning_rate": learning_rate,
                "batch_size": self.model_config.get("batch_size", 32),
                "num_channels": self.model_config.get("num_channels", 14),
                "hidden_dim": self.model_config.get("hidden_dim", 128)
            })

        if self.use_wandb:
            wandb.config.update({
                "num_epochs": num_epochs,
                "learning_rate": learning_rate,
                "batch_size": self.model_config.get("batch_size", 32)
            })

        # Training loop
        logger.info(f"Starting training for {num_epochs} epochs...")

        for epoch in range(num_epochs):
            # Train
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for features, labels in train_loader:
                features, labels = features.to(self.device), labels.to(self.device)

                # Forward
                optimizer.zero_grad()
                outputs = model(features)
                loss = criterion(outputs, labels)

                # Backward
                loss.backward()
                optimizer.step()

                # Metrics
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()

            train_loss /= len(train_loader)
            train_acc = 100 * train_correct / train_total

            # Validate
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for features, labels in val_loader:
                    features, labels = features.to(self.device), labels.to(self.device)

                    outputs = model(features)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()

            val_loss /= len(val_loader)
            val_acc = 100 * val_correct / val_total

            # LR scheduler
            scheduler.step(val_loss)

            # Save history
            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            # Log metrics
            if self.use_mlflow:
                mlflow.log_metrics({
                    "train_loss": train_loss,
                    "train_acc": train_acc,
                    "val_loss": val_loss,
                    "val_acc": val_acc
                }, step=epoch)

            if self.use_wandb:
                wandb.log({
                    "train_loss": train_loss,
                    "train_acc": train_acc,
                    "val_loss": val_loss,
                    "val_acc": val_acc
                }, step=epoch)

            # Print progress
            if (epoch + 1) % 5 == 0:
                logger.info(
                    f"Epoch [{epoch+1}/{num_epochs}] "
                    f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
                    f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%"
                )

            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc

                if save_path:
                    torch.save(model.state_dict(), save_path)
                    logger.info(f"Saved best model with val_acc: {val_acc:.2f}%")

                    if self.use_mlflow:
                        mlflow.pytorch.log_model(model, "model")

        logger.info(f"Training complete! Best val acc: {best_val_acc:.2f}%")

        return history

    def evaluate(
        self,
        model: nn.Module,
        test_loader: DataLoader
    ) -> Dict:
        """Evaluate model on test set"""
        model.eval()
        model.to(self.device)

        all_preds = []
        all_labels = []

        with torch.no_grad():
            for features, labels in test_loader:
                features, labels = features.to(self.device), labels.to(self.device)

                outputs = model(features)
                _, predicted = torch.max(outputs.data, 1)

                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        # Metrics
        accuracy = 100 * np.mean(np.array(all_preds) == np.array(all_labels))

        # Classification report
        class_names = ["focused", "relaxed", "stressed", "drowsy"]
        report = classification_report(
            all_labels,
            all_preds,
            target_names=class_names,
            output_dict=True
        )

        results = {
            "accuracy": accuracy,
            "classification_report": report,
            "confusion_matrix": confusion_matrix(all_labels, all_preds).tolist()
        }

        logger.info(f"Test Accuracy: {accuracy:.2f}%")

        if self.use_mlflow:
            mlflow.log_metric("test_accuracy", accuracy)

        return results


def train_eeg_model_from_dataset(
    data_dir: str,
    save_dir: str,
    config: Optional[Dict] = None
) -> Dict:
    """
    Complete training pipeline from dataset directory

    Args:
        data_dir: Directory containing EEG data files
        save_dir: Directory to save trained model
        config: Training configuration

    Returns:
        Training results
    """
    if config is None:
        config = {
            "sample_rate": 256,
            "num_channels": 14,
            "num_classes": 4,
            "hidden_dim": 128,
            "batch_size": 32,
            "num_epochs": 50,
            "learning_rate": 0.001
        }

    # Initialize trainer
    trainer = EEGTrainer(
        model_config=config,
        use_mlflow=True,
        experiment_name="eeg_mental_state_classification"
    )

    # Load dataset (implementation depends on data format)
    # For now, assume we have prepared data
    logger.info("Loading dataset...")

    # Placeholder - in production, load actual EEG dataset
    # This could be from public datasets like:
    # - DEAP (emotion recognition)
    # - SEED (emotion EEG)
    # - BCI Competition datasets

    eeg_signals = []
    labels = []

    # TODO: Implement actual data loading from data_dir

    logger.info(f"Loaded {len(labels)} samples")

    # Prepare data
    train_loader, val_loader, test_loader = trainer.prepare_data(
        eeg_signals, labels
    )

    # Train
    save_path = Path(save_dir) / "eeg_classifier_best.pth"
    history = trainer.train(
        train_loader,
        val_loader,
        num_epochs=config["num_epochs"],
        learning_rate=config["learning_rate"],
        save_path=str(save_path)
    )

    # Evaluate
    model = EEGClassifier(
        num_channels=config["num_channels"],
        num_features=5,
        num_classes=config["num_classes"],
        hidden_dim=config["hidden_dim"]
    )
    model.load_state_dict(torch.load(save_path))

    test_results = trainer.evaluate(model, test_loader)

    return {
        "history": history,
        "test_results": test_results,
        "model_path": str(save_path)
    }
