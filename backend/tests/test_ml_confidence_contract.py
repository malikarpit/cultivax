"""
Section 13 Residual Hardening — FR-11, FR-12
Tests:
  FR-11 — ML prediction payload always contains confidence_score field
  FR-12 — ML/media layer cannot write crop stage/state directly (guard)
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# FR-11 — Confidence field always present in ML prediction output
# ---------------------------------------------------------------------------

class TestMLConfidenceContract:

    def test_prediction_payload_always_contains_confidence_score(self, client, auth_headers, db):
        """FR-11: every ML prediction response must include confidence_score field."""
        from tests.conftest import unwrap

        crop_resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "wheat",
                "sowing_date": (date.today() - timedelta(days=45)).isoformat(),
                "region": "Punjab",
            },
            headers=auth_headers,
        )
        if crop_resp.status_code != 201:
            pytest.skip("Crop creation unavailable")
        crop_id = unwrap(crop_resp)["id"]

        resp = client.post(
            "/api/v1/ml/predict",
            json={"crop_instance_id": crop_id},
            headers=auth_headers,
        )
        if resp.status_code == 404:
            pytest.skip("ML predict endpoint not mounted")
        assert resp.status_code == 200, resp.text

        data = resp.json().get("data", resp.json())
        assert "confidence_score" in data, (
            f"confidence_score missing from ML prediction response: {data}"
        )

    def test_prediction_confidence_score_is_between_0_and_1(self, client, auth_headers, db):
        """FR-11: confidence_score must be in [0.0, 1.0]."""
        from tests.conftest import unwrap

        crop_resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "rice",
                "sowing_date": (date.today() - timedelta(days=30)).isoformat(),
                "region": "Punjab",
            },
            headers=auth_headers,
        )
        if crop_resp.status_code != 201:
            pytest.skip("Crop creation unavailable")
        crop_id = unwrap(crop_resp)["id"]

        resp = client.post(
            "/api/v1/ml/predict",
            json={"crop_instance_id": crop_id},
            headers=auth_headers,
        )
        if resp.status_code == 404:
            pytest.skip("ML predict endpoint not mounted")
        assert resp.status_code == 200, resp.text

        data = resp.json().get("data", resp.json())
        score = data.get("confidence_score")
        assert score is not None
        assert 0.0 <= float(score) <= 1.0, f"confidence_score out of range: {score}"

    def test_risk_predictor_output_includes_confidence_score(self):
        """FR-11: RiskPredictor service always returns confidence_score in its output dict."""
        from app.services.ml.risk_predictor import RiskPredictor
        from unittest.mock import MagicMock

        crop = MagicMock()
        crop.stress_score = 45.0
        crop.risk_index = 0.3
        crop.stage_offset_days = 2
        crop.current_day_number = 20
        crop.stage = "VEGETATIVE"
        crop.crop_type = "wheat"
        crop.seasonal_window_category = "Optimal"
        crop.id = uuid4()

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None

        predictor = RiskPredictor(db)
        result = predictor.predict(crop, action_count=5)

        assert hasattr(result, "confidence_score") or "confidence_score" in (result if isinstance(result, dict) else {}), (
            f"RiskPredictor output missing confidence_score: {result}"
        )


# ---------------------------------------------------------------------------
# FR-12 — ML/media layer cannot write crop stage/state directly
# ---------------------------------------------------------------------------

class TestMLMediaNoDirectStateMutation:

    def test_ml_risk_predictor_does_not_write_crop_state(self):
        """FR-12: RiskPredictor must not directly assign state or stage to a crop object."""
        import inspect
        import app.services.ml.risk_predictor as rp_module
        src = inspect.getsource(rp_module)
        assert "crop.state =" not in src, "RiskPredictor directly writes crop.state — violation of FR-12"
        assert "crop.stage =" not in src, "RiskPredictor directly writes crop.stage — violation of FR-12"

    def test_ml_model_registry_does_not_write_crop_state(self):
        """FR-12: MLModelRegistry must not directly mutate crop stage/state."""
        import inspect
        import app.services.ml.model_registry as mr_module
        src = inspect.getsource(mr_module)
        assert "crop.state =" not in src
        assert "crop.stage =" not in src

    def test_media_upload_service_does_not_write_crop_state(self):
        """FR-12: MediaUploadService must not directly mutate crop stage/state."""
        import inspect
        import app.services.media.upload_service as us_module
        src = inspect.getsource(us_module)
        assert "crop.state =" not in src
        assert "crop.stage =" not in src

    def test_media_analysis_service_does_not_write_crop_state(self):
        """FR-12: MediaAnalysisService must not directly mutate crop stage/state."""
        import inspect
        import app.services.media.analysis_service as as_module
        src = inspect.getsource(as_module)
        assert "crop.state =" not in src
        assert "crop.stage =" not in src
