"""
ML Inference Runtime — FR-10, FR-29

Provides a production-grade inference layer that loads serialized model
artifacts (joblib/pickle) from the MLModel registry and executes predictions
with LRU in-memory caching to avoid repeated disk reads.

Falls back gracefully to the rule-based predictor when no artifact is present.
"""

import logging
import os
from functools import lru_cache
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# --- Optional heavy dependencies (not available during unit tests) ---
try:
    import joblib

    _JOBLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    joblib = None  # type: ignore
    _JOBLIB_AVAILABLE = False

try:
    import numpy as np

    _NUMPY_AVAILABLE = True
except ImportError:  # pragma: no cover
    np = None  # type: ignore
    _NUMPY_AVAILABLE = False


class InferenceRuntime:
    """
    Loads and executes ML model artifacts.

    Usage:
        runtime = InferenceRuntime()
        model = runtime.load(file_path)
        risk_probability, confidence = runtime.predict_risk(model, features)

    Thread safety: `load()` is backed by a module-level LRU cache on the
    file_path string, so concurrent reads of the same path serve from cache.
    """

    def load(self, file_path: str):
        """
        Load a serialized sklearn/joblib model from disk.
        Uses an LRU cache keyed on file_path to avoid repeated I/O.

        Returns:
            Loaded model object, or None if joblib is unavailable or file missing.
        """
        return _load_model_cached(file_path)

    def predict_risk(self, model, features: dict) -> Tuple[float, float]:
        """
        Run inference with the given model and feature dict.

        Returns:
            (risk_probability, confidence) — both in [0.0, 1.0]

        Falls back to heuristic estimate if model does not support `predict_proba`.
        """
        if model is None:
            return self._heuristic_fallback(features)

        try:
            feature_vector = self._build_feature_vector(features)
            if _NUMPY_AVAILABLE and hasattr(model, "predict_proba"):
                proba = model.predict_proba(np.array([feature_vector]))[0]
                # Binary classification: index 1 = risk=True probability
                risk_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
                # Confidence: max probability (certainty the model is deciding firmly)
                confidence = float(max(proba))
                return (
                    round(min(max(risk_prob, 0.0), 1.0), 4),
                    round(min(max(confidence, 0.0), 1.0), 3),
                )
            elif hasattr(model, "predict"):
                result = model.predict(
                    np.array([feature_vector]) if _NUMPY_AVAILABLE else [feature_vector]
                )
                risk_prob = float(result[0])
                return (
                    round(min(max(risk_prob, 0.0), 1.0), 4),
                    0.6,
                )  # lower confidence for point estimates
        except Exception as exc:
            logger.warning(
                f"InferenceRuntime.predict_risk failed: {exc} — using heuristic fallback"
            )

        return self._heuristic_fallback(features)

    def _build_feature_vector(self, features: dict) -> list:
        """
        Convert a feature dict to an ordered list matching training schema.
        Order: [stress_score_norm, risk_index, stage_offset_days_norm, action_count_norm, day_norm]
        """
        return [
            features.get("stress_score_norm", 0.0),
            features.get("risk_index", 0.0),
            features.get("stage_offset_days_norm", 0.0),
            features.get("action_count_norm", 0.0),
            features.get("day_norm", 0.0),
        ]

    def _heuristic_fallback(self, features: dict) -> Tuple[float, float]:
        """Simple weighted heuristic used when no model artifact is available."""
        stress = features.get("stress_score_norm", 0.0)
        risk = features.get("risk_index", 0.0)
        drift = features.get("stage_offset_days_norm", 0.0)
        prob = round(min(0.4 * stress + 0.35 * risk + 0.25 * drift, 1.0), 4)
        confidence = 0.5  # rule-based ceiling
        return prob, confidence


@lru_cache(maxsize=8)
def _load_model_cached(file_path: str):
    """Module-level LRU-cached model loader."""
    if not _JOBLIB_AVAILABLE:
        logger.warning("joblib not installed — InferenceRuntime.load() returns None")
        return None
    if not os.path.isfile(file_path):
        logger.warning(f"Model artifact not found at: {file_path}")
        return None
    try:
        model = joblib.load(file_path)
        logger.info(f"Loaded ML model artifact from {file_path}")
        return model
    except Exception as exc:
        logger.error(f"Failed to load ML artifact {file_path}: {exc}")
        return None


def clear_model_cache() -> None:
    """Clears the LRU model cache (call during tests or after model swap)."""
    _load_model_cached.cache_clear()
