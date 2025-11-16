"""
Train EEG Mental State Classifiers.

Trains both:
1. CNN + Bidirectional LSTM (standard deep learning)
2. Spiking Neural Network (brain-inspired)

Compares performance and saves best model.
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
from pathlib import Path
from typing import Tuple, Dict
import json
from tqdm import tqdm
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import mlflow
import mlflow.pytorch

# Import our models
from eeg_classifier import EEGMentalStateClassifier
from snn_classifier import SpikingEEGClassifier


class EEGDataset(Dataset):
    """PyTorch Dataset for EEG data."""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        """
        Args:
            X: EEG data (n_samples, n_channels, n_timepoints)
            y: Labels (n_samples,)
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class EEGTrainer:
    """Trainer for EEG mental state classifiers."""

    def __init__(
        self,
        model_type: str = "cnn_lstm",  # or "snn"
        n_channels: int = 14,
        n_classes: int = 4,
        device: str = None
    ):
        """
        Initialize trainer.

        Args:
            model_type: 'cnn_lstm' or 'snn'
            n_channels: Number of EEG channels
            n_classes: Number of mental states
            device: 'cuda' or 'cpu'
        """
        self.model_type = model_type
        self.n_channels = n_channels
        self.n_classes = n_classes

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        print(f"🔧 Using device: {self.device}")

        # Initialize model
        self.model = self._create_model()
        self.model.to(self.device)

        # Print model info
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"📊 Model: {model_type}")
        print(f"📊 Total parameters: {total_params:,}")
        print(f"📊 Trainable parameters: {trainable_params:,}")

    def _create_model(self):
        """Create model based on type."""
        if self.model_type == "cnn_lstm":
            return EEGMentalStateClassifier(
                n_channels=self.n_channels,
                n_classes=self.n_classes
            )
        elif self.model_type == "snn":
            return SpikingEEGClassifier(
                n_channels=self.n_channels,
                n_classes=self.n_classes
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 50,
        lr: float = 0.001,
        weight_decay: float = 1e-4,
        patience: int = 10
    ) -> Dict:
        """
        Train the model.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Number of training epochs
            lr: Learning rate
            weight_decay: L2 regularization
            patience: Early stopping patience

        Returns:
            Training history
        """
        print(f"\n🚀 Starting training for {epochs} epochs...")

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(
            self.model.parameters(),
            lr=lr,
            weight_decay=weight_decay
        )

        # Learning rate scheduler
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )

        # Training history
        history = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "lr": []
        }

        best_val_acc = 0
        patience_counter = 0
        best_model_state = None

        # Training loop
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0

            for batch_X, batch_y in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                # Forward pass
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)

                # Backward pass
                loss.backward()
                optimizer.step()

                # Statistics
                train_loss += loss.item()
                _, predicted = outputs.max(1)
                train_total += batch_y.size(0)
                train_correct += predicted.eq(batch_y).sum().item()

            # Validation phase
            val_loss, val_acc, _, _ = self.evaluate(val_loader, criterion)

            # Update history
            train_loss /= len(train_loader)
            train_acc = 100. * train_correct / train_total

            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)
            history["lr"].append(optimizer.param_groups[0]['lr'])

            # Print progress
            print(f"\nEpoch {epoch+1}/{epochs}:")
            print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            print(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

            # MLflow logging
            mlflow.log_metrics({
                "train_loss": train_loss,
                "train_acc": train_acc,
                "val_loss": val_loss,
                "val_acc": val_acc,
                "learning_rate": optimizer.param_groups[0]['lr']
            }, step=epoch)

            # Learning rate scheduling
            scheduler.step(val_loss)

            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                best_model_state = self.model.state_dict().copy()
                print(f"  ✅ New best model! Val Acc: {val_acc:.2f}%")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"\n⏹️  Early stopping triggered after {epoch+1} epochs")
                    break

        # Restore best model
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)
            print(f"\n✅ Restored best model with Val Acc: {best_val_acc:.2f}%")

        return history

    def evaluate(
        self,
        data_loader: DataLoader,
        criterion=None
    ) -> Tuple[float, float, np.ndarray, np.ndarray]:
        """
        Evaluate model on dataset.

        Args:
            data_loader: Data loader
            criterion: Loss function (optional)

        Returns:
            loss, accuracy, predictions, true_labels
        """
        self.model.eval()

        all_preds = []
        all_labels = []
        total_loss = 0

        with torch.no_grad():
            for batch_X, batch_y in data_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                outputs = self.model(batch_X)

                if criterion:
                    loss = criterion(outputs, batch_y)
                    total_loss += loss.item()

                _, predicted = outputs.max(1)
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(batch_y.cpu().numpy())

        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)

        accuracy = accuracy_score(all_labels, all_preds) * 100

        if criterion:
            avg_loss = total_loss / len(data_loader)
        else:
            avg_loss = 0

        return avg_loss, accuracy, all_preds, all_labels

    def save_model(self, save_path: str):
        """Save trained model."""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'n_channels': self.n_channels,
            'n_classes': self.n_classes,
        }, save_path)

        print(f"💾 Model saved to {save_path}")

    def load_model(self, load_path: str):
        """Load trained model."""
        checkpoint = torch.load(load_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        print(f"📥 Model loaded from {load_path}")


def plot_training_history(history: Dict, save_path: str = None):
    """Plot training history."""

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Loss plot
    axes[0].plot(history['train_loss'], label='Train Loss', marker='o')
    axes[0].plot(history['val_loss'], label='Val Loss', marker='s')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)

    # Accuracy plot
    axes[1].plot(history['train_acc'], label='Train Acc', marker='o')
    axes[1].plot(history['val_acc'], label='Val Acc', marker='s')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy (%)')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Training plots saved to {save_path}")

    plt.show()


def plot_confusion_matrix(y_true, y_pred, class_names, save_path=None):
    """Plot confusion matrix."""

    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names
    )
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Confusion matrix saved to {save_path}")

    plt.show()


def main():
    """Main training pipeline."""

    print("=== EEG Mental State Classifier Training ===\n")

    # Configuration
    DATASET_DIR = "data/eeg_datasets/synthetic"
    MODEL_TYPE = "cnn_lstm"  # or "snn"
    BATCH_SIZE = 32
    EPOCHS = 50
    LEARNING_RATE = 0.001
    PATIENCE = 10

    # Load dataset
    print("📚 Loading dataset...")
    X_train = np.load(Path(DATASET_DIR) / "X_train.npy")
    y_train = np.load(Path(DATASET_DIR) / "y_train.npy")
    X_test = np.load(Path(DATASET_DIR) / "X_test.npy")
    y_test = np.load(Path(DATASET_DIR) / "y_test.npy")

    print(f"✅ Dataset loaded:")
    print(f"   Train: {X_train.shape}, {y_train.shape}")
    print(f"   Test: {X_test.shape}, {y_test.shape}")

    # Create data loaders
    train_dataset = EEGDataset(X_train, y_train)
    test_dataset = EEGDataset(X_test, y_test)

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4
    )

    # Initialize MLflow
    mlflow.set_experiment("eeg-mental-state-classification")

    with mlflow.start_run(run_name=f"{MODEL_TYPE}_training"):
        # Log parameters
        mlflow.log_params({
            "model_type": MODEL_TYPE,
            "batch_size": BATCH_SIZE,
            "epochs": EPOCHS,
            "learning_rate": LEARNING_RATE,
            "patience": PATIENCE,
            "n_channels": X_train.shape[1],
            "n_classes": len(np.unique(y_train)),
        })

        # Initialize trainer
        trainer = EEGTrainer(
            model_type=MODEL_TYPE,
            n_channels=X_train.shape[1],
            n_classes=len(np.unique(y_train))
        )

        # Train
        history = trainer.train(
            train_loader=train_loader,
            val_loader=test_loader,
            epochs=EPOCHS,
            lr=LEARNING_RATE,
            patience=PATIENCE
        )

        # Final evaluation
        print("\n📊 Final Evaluation on Test Set:")
        test_loss, test_acc, y_pred, y_true = trainer.evaluate(
            test_loader,
            criterion=nn.CrossEntropyLoss()
        )

        print(f"Test Loss: {test_loss:.4f}")
        print(f"Test Accuracy: {test_acc:.2f}%")

        # Classification report
        class_names = ["Stressed", "Relaxed", "Focused", "Drowsy"]
        print("\n" + classification_report(y_true, y_pred, target_names=class_names))

        # F1 scores
        f1_macro = f1_score(y_true, y_pred, average='macro')
        f1_weighted = f1_score(y_true, y_pred, average='weighted')

        print(f"F1 Score (Macro): {f1_macro:.4f}")
        print(f"F1 Score (Weighted): {f1_weighted:.4f}")

        # Log final metrics
        mlflow.log_metrics({
            "test_loss": test_loss,
            "test_accuracy": test_acc,
            "f1_macro": f1_macro,
            "f1_weighted": f1_weighted
        })

        # Save model
        model_save_path = f"models/eeg_{MODEL_TYPE}_best.pth"
        trainer.save_model(model_save_path)
        mlflow.log_artifact(model_save_path)

        # Plot and save results
        plot_training_history(history, save_path=f"results/eeg_{MODEL_TYPE}_training_history.png")
        plot_confusion_matrix(y_true, y_pred, class_names, save_path=f"results/eeg_{MODEL_TYPE}_confusion_matrix.png")

    print("\n🎉 Training completed successfully!")


if __name__ == "__main__":
    main()
