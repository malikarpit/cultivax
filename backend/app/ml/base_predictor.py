"""
Base Predictor Abstract Base Class — Extensibility

Provides a plugin architecture for adding new ML models over time.
All ML models in CultivaX must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePredictor(ABC):
    """Abstract base class for all machine learning models."""

    @abstractmethod
    def load_model(self, path: str) -> None:
        """Load model weights/metadata from disk."""
        pass

    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference on the given features.
        Must return a dict containing at minimum the prediction and confidence score.
        """
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return the semantic version of the loaded model."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Return the expected input feature schema."""
        pass
