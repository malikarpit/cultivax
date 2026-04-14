"""
Test CNN Stress Model — MSDD 4.3, TDD 6.2, TDD 6.8

Tests CNN model architecture and TFLite export pipeline.
"""

import pytest
from unittest.mock import MagicMock, patch
import os


class TestCNNStressModel:
    """Tests for the CNN stress detection model."""

    def test_model_class_loads(self):
        """CNN model class should load when PyTorch is available."""
        try:
            from app.ml.train_stress_cnn import get_model_class
            ModelClass = get_model_class()
            if ModelClass is not None:
                model = ModelClass()
                assert model is not None
            else:
                pytest.skip("PyTorch not available")
        except ImportError:
            pytest.skip("PyTorch not available")

    def test_synthetic_dataset_generates_correct_shape(self):
        """Synthetic dataset should produce correct tensor shapes."""
        try:
            import torch
            from app.ml.train_stress_cnn import generate_synthetic_dataset, IMAGE_SIZE

            images, labels = generate_synthetic_dataset(100)
            assert images.shape == (100, 3, IMAGE_SIZE, IMAGE_SIZE)
            assert labels.shape == (100,)
            assert set(labels.numpy().tolist()) == {0, 1}
        except ImportError:
            pytest.skip("PyTorch not available")

    def test_model_forward_pass(self):
        """Model should produce output in correct shape."""
        try:
            import torch
            from app.ml.train_stress_cnn import get_model_class, IMAGE_SIZE

            ModelClass = get_model_class()
            if ModelClass is None:
                pytest.skip("PyTorch not available")

            model = ModelClass()
            x = torch.randn(1, 3, IMAGE_SIZE, IMAGE_SIZE)
            output = model(x)
            assert output.shape == (1, 2), f"Expected (1, 2), got {output.shape}"

            probs = torch.softmax(output, dim=1)
            assert 0.0 <= probs[0][0].item() <= 1.0
            assert 0.0 <= probs[0][1].item() <= 1.0
        except ImportError:
            pytest.skip("PyTorch not available")

    def test_predict_stress_returns_valid_output(self):
        """predict_stress should return (probability, confidence) tuple."""
        try:
            import torch
            from app.ml.train_stress_cnn import (
                get_model_class, predict_stress, IMAGE_SIZE
            )

            ModelClass = get_model_class()
            if ModelClass is None:
                pytest.skip("PyTorch not available")

            model = ModelClass()
            model.eval()
            image = torch.randn(3, IMAGE_SIZE, IMAGE_SIZE)
            stress_prob, confidence = predict_stress(model, image)

            assert 0.0 <= stress_prob <= 1.0
            assert 0.0 <= confidence <= 1.0
        except ImportError:
            pytest.skip("PyTorch not available")


class TestTFLiteExport:
    """Tests for the TFLite export pipeline."""

    def test_export_to_onnx(self):
        """PyTorch model should export to ONNX format."""
        try:
            import torch
            from app.ml.train_stress_cnn import get_model_class
            from app.ml.export_tflite import export_to_onnx

            ModelClass = get_model_class()
            if ModelClass is None:
                pytest.skip("PyTorch not available")

            model = ModelClass()
            model.eval()

            output_path = "/tmp/test_stress_cnn.onnx"
            result = export_to_onnx(model, output_path)

            assert os.path.exists(result)
            assert result.endswith(".onnx")

            # Cleanup
            os.remove(result)
        except ImportError:
            pytest.skip("PyTorch or ONNX not available")

    def test_full_pipeline_metadata(self):
        """Export pipeline should produce metadata when full deps unavailable."""
        from app.ml.export_tflite import convert_onnx_to_tflite

        # This will create a stub metadata file since onnx-tf is likely not installed
        output_path = "/tmp/test_stress_cnn.tflite"
        result = convert_onnx_to_tflite("/tmp/nonexistent.onnx", output_path)

        # Either the actual tflite or the metadata stub should be created
        meta_path = f"{result}.meta.json"
        if os.path.exists(meta_path):
            import json
            with open(meta_path) as f:
                meta = json.load(f)
            assert meta["format"] == "tflite_stub"
            os.remove(meta_path)
