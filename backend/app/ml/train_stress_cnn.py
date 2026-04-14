"""
CNN Stress Detection Model — MSDD 4.3, TDD 6.2

Simple convolutional neural network for crop stress detection.
Trained on synthetic or augmented dataset for prototype demonstration.

Architecture:
  - 3 Conv2d layers with ReLU + MaxPool
  - Fully connected classifier (binary: stressed/healthy)
  - Output: stress_probability, confidence

Usage:
    python -m app.ml.train_stress_cnn
"""

import logging
import os

logger = logging.getLogger(__name__)

# Model hyperparameters
IMAGE_SIZE = 64
NUM_CLASSES = 2  # stressed, healthy
BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 0.001

# Output paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml_models")
MODEL_FILENAME = "stress_cnn_v1.pt"


def get_model_class():
    """
    Lazy-load PyTorch model class to avoid import failure when torch
    is not installed (it's an optional dependency).
    """
    try:
        import torch
        import torch.nn as nn

        class StressCNN(nn.Module):
            """
            3-layer CNN for binary crop stress classification.
            Input: 3-channel RGB image (64×64)
            Output: [healthy_prob, stressed_prob]
            """

            def __init__(self):
                super().__init__()
                self.features = nn.Sequential(
                    nn.Conv2d(3, 16, kernel_size=3, padding=1),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                    nn.Conv2d(16, 32, kernel_size=3, padding=1),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                    nn.Conv2d(32, 64, kernel_size=3, padding=1),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                )
                self.classifier = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(64 * (IMAGE_SIZE // 8) ** 2, 128),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.3),
                    nn.Linear(128, NUM_CLASSES),
                )

            def forward(self, x):
                x = self.features(x)
                x = self.classifier(x)
                return x

        return StressCNN

    except ImportError:
        logger.warning("PyTorch not available — CNN model cannot be loaded")
        return None


def generate_synthetic_dataset(num_samples: int = 500):
    """
    Generate a synthetic training dataset for demonstration.
    Creates random tensors labeled as stressed (high-variance) or
    healthy (low-variance) with noise.
    """
    import torch

    images = []
    labels = []

    for i in range(num_samples):
        if i < num_samples // 2:
            # "Healthy" — low-variance greenish image
            img = torch.randn(3, IMAGE_SIZE, IMAGE_SIZE) * 0.3 + 0.6
            img[1] *= 1.3  # boost green channel
            labels.append(0)
        else:
            # "Stressed" — high-variance brownish/yellow image
            img = torch.randn(3, IMAGE_SIZE, IMAGE_SIZE) * 0.6 + 0.4
            img[1] *= 0.5  # reduce green channel
            img[0] *= 1.2  # boost red channel
            labels.append(1)
        images.append(img.clamp(0, 1))

    return torch.stack(images), torch.tensor(labels)


def train_model():
    """
    Train the CNN model on synthetic data and save the artifact.
    """
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset

    ModelClass = get_model_class()
    if ModelClass is None:
        logger.error("Cannot train — PyTorch not available")
        return None

    model = ModelClass()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Generate synthetic dataset
    images, labels = generate_synthetic_dataset(500)
    dataset = TensorDataset(images, labels)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Training loop
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        correct = 0
        total = 0
        for batch_images, batch_labels in loader:
            optimizer.zero_grad()
            outputs = model(batch_images)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += batch_labels.size(0)
            correct += predicted.eq(batch_labels).sum().item()

        accuracy = 100.0 * correct / total
        logger.info(
            f"Epoch {epoch+1}/{EPOCHS}: loss={total_loss:.4f}, accuracy={accuracy:.1f}%"
        )

    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    torch.save(model.state_dict(), model_path)
    logger.info(f"Model saved to {model_path}")

    return model_path


def load_model(model_path: str = None):
    """Load a trained model from disk."""
    import torch

    ModelClass = get_model_class()
    if ModelClass is None:
        return None

    if model_path is None:
        model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)

    if not os.path.exists(model_path):
        logger.warning(f"Model file not found: {model_path}")
        return None

    model = ModelClass()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    return model


def predict_stress(model, image_tensor):
    """
    Run inference on a single image tensor.
    Returns: (stress_probability, confidence)
    """
    import torch

    with torch.no_grad():
        output = model(image_tensor.unsqueeze(0))
        probabilities = torch.softmax(output, dim=1)
        stress_prob = probabilities[0][1].item()
        confidence = probabilities.max(dim=1).values.item()

    return stress_prob, confidence


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_model()
