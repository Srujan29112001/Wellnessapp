"""
Training script for EEG mental state classifier

Trains on labeled EEG datasets (DEAP, SEED, etc.)
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
import mlflow
import mlflow.pytorch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml.eeg_analysis.classifier import EEGClassifier
from ml.eeg_analysis.processor import EEGProcessor


class EEGDataset(Dataset):
    """PyTorch Dataset for EEG data"""

    def __init__(self, eeg_data: np.ndarray, labels: np.ndarray):
        """
        Args:
            eeg_data: Array of shape (n_samples, n_channels, n_features)
            labels: Array of shape (n_samples, n_classes)
        """
        self.data = torch.FloatTensor(eeg_data)
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]


def load_eeg_dataset(data_path: str = "data/eeg/deap_dataset.npz"):
    """
    Load EEG dataset

    For production, download DEAP or SEED dataset:
    - DEAP: https://www.eecs.qmul.ac.uk/mmv/datasets/deap/
    - SEED: https://bcmi.sjtu.edu.cn/home/seed/

    For now, generate synthetic data for demonstration
    """
    path = Path(data_path)

    if path.exists():
        # Load real dataset
        data = np.load(path)
        return data['eeg'], data['labels']
    else:
        # Generate synthetic data for demo
        print("Real dataset not found. Generating synthetic data...")

        n_samples = 1000
        n_channels = 14
        n_features = 29  # From EEG processor

        # Synthetic EEG features
        eeg_data = np.random.randn(n_samples, n_channels, n_features).astype(np.float32)

        # Synthetic labels (4 classes: stress, focus, relaxation, drowsy)
        labels = np.zeros((n_samples, 4), dtype=np.float32)
        for i in range(n_samples):
            class_idx = np.random.randint(0, 4)
            labels[i, class_idx] = 1.0

        return eeg_data, labels


def train_eeg_model(
    data_path: str = "data/eeg/deap_dataset.npz",
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    model_save_path: str = "data/models/eeg_classifier.pth"
):
    """
    Train EEG classifier

    Args:
        data_path: Path to EEG dataset
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        model_save_path: Where to save trained model
    """
    # Start MLflow run
    mlflow.set_experiment("eeg_classification")

    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("learning_rate", learning_rate)

        # Load data
        print("Loading EEG dataset...")
        eeg_data, labels = load_eeg_dataset(data_path)

        # Split train/val
        X_train, X_val, y_train, y_val = train_test_split(
            eeg_data, labels, test_size=0.2, random_state=42
        )

        # Create datasets
        train_dataset = EEGDataset(X_train, y_train)
        val_dataset = EEGDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        # Initialize model
        n_channels = eeg_data.shape[1]
        n_features = eeg_data.shape[2]
        n_classes = labels.shape[1]

        model = EEGClassifier(n_channels=n_channels, n_features=n_features, n_classes=n_classes)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)

        # Loss and optimizer
        criterion = nn.BCELoss()  # Binary cross-entropy for multi-label
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

        # Training loop
        best_val_loss = float('inf')

        for epoch in range(epochs):
            # Train
            model.train()
            train_loss = 0
            for batch_data, batch_labels in train_loader:
                batch_data = batch_data.to(device)
                batch_labels = batch_labels.to(device)

                # Forward
                outputs = model(batch_data)
                loss = criterion(outputs, batch_labels)

                # Backward
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation
            model.eval()
            val_loss = 0
            all_preds = []
            all_labels = []

            with torch.no_grad():
                for batch_data, batch_labels in val_loader:
                    batch_data = batch_data.to(device)
                    batch_labels = batch_labels.to(device)

                    outputs = model(batch_data)
                    loss = criterion(outputs, batch_labels)

                    val_loss += loss.item()

                    # Convert to class predictions
                    preds = (outputs.cpu().numpy() > 0.5).astype(int)
                    all_preds.extend(preds)
                    all_labels.extend(batch_labels.cpu().numpy())

            val_loss /= len(val_loader)

            # Calculate metrics
            all_preds = np.array(all_preds)
            all_labels = np.array(all_labels)
            accuracy = accuracy_score(all_labels.argmax(axis=1), all_preds.argmax(axis=1))

            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Accuracy: {accuracy:.4f}")

            # Log metrics to MLflow
            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("accuracy", accuracy, step=epoch)

            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), model_save_path)
                print(f"Saved best model with val_loss: {val_loss:.4f}")

        # Log model
        mlflow.pytorch.log_model(model, "model")

        print(f"\nTraining complete! Best model saved to {model_save_path}")
        print(f"Best validation loss: {best_val_loss:.4f}")


if __name__ == "__main__":
    train_eeg_model(
        epochs=50,
        batch_size=32,
        learning_rate=0.001
    )
