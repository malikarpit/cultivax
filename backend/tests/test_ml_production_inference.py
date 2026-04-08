"""
FR-10 + FR-29 — ML Production Inference & Inference Audit Tests

Covers:
  FR-10 — InferenceRuntime is used when an active model with file_path exists
  FR-10 — Falls back to rule-based path when no artifact is present
  FR-29 — MLInferenceAudit row is written after every prediction
  FR-29 — /ml/inference-audits filters by model_version, crop_instance_id
"""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from tests.conftest import unwrap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_crop_mock(stress: float = 45.0, risk: float = 0.3):
    crop = MagicMock()
    crop.id = uuid4()
    crop.stress_score = stress
    crop.risk_index = risk
    crop.current_day_number = 30
    crop.stage = "VEGETATIVE"
    crop.crop_type = "wheat"
    crop.seasonal_window_category = "Optimal"
    crop.stage_offset_days = 2
    crop.metadata_extra = {}
    return crop


# ---------------------------------------------------------------------------
# FR-10 — InferenceRuntime integration
# ---------------------------------------------------------------------------

class TestInferenceRuntimeWiring:

    def test_inference_runtime_used_when_active_model_has_file_path(self):
        """FR-10: when ModelRegistry returns an active model with file_path, InferenceRuntime is called."""
        from app.services.ml.risk_predictor import RiskPredictor

        predictor = RiskPredictor()
        mock_db = MagicMock()

        # Mock registry returning active model with file_path
        fake_model = MagicMock()
        fake_model.version = 2
        fake_model.file_path = "/tmp/fake_model.joblib"

        with patch("app.services.ml.risk_predictor.RiskPredictor.is_ml_safe", return_value=True), \
             patch("app.services.ml.model_registry.ModelRegistry.get_active_model", return_value=fake_model), \
             patch("app.services.ml.inference_runtime.InferenceRuntime.load", return_value=MagicMock()), \
             patch("app.services.ml.inference_runtime.InferenceRuntime.predict_risk", return_value=(0.72, 0.88)) as mock_predict:

            result = predictor.predict_risk(
                stress_score=60.0,
                risk_index=0.5,
                db=mock_db,
            )

        assert result.prediction_value == pytest.approx(0.72)
        assert result.confidence_score == pytest.approx(0.88)
        assert result.model_version == "v2"

    def test_falls_back_to_rule_based_when_no_file_path(self):
        """FR-10: when active model has no file_path, rule-based path runs and inference_source is not registry."""
        from app.services.ml.risk_predictor import RiskPredictor

        predictor = RiskPredictor()
        mock_db = MagicMock()

        fake_model = MagicMock()
        fake_model.version = 1
        fake_model.file_path = None  # no artifact

        with patch("app.services.ml.risk_predictor.RiskPredictor.is_ml_safe", return_value=True), \
             patch("app.services.ml.model_registry.ModelRegistry.get_active_model", return_value=fake_model):

            result = predictor.predict_risk(stress_score=50.0, risk_index=0.4, db=mock_db)

        assert 0.0 <= result.prediction_value <= 1.0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.model_version == "v1"

    def test_falls_back_gracefully_when_no_active_model(self):
        """FR-10: when no active model in registry, rule-based values returned."""
        from app.services.ml.risk_predictor import RiskPredictor

        predictor = RiskPredictor()
        mock_db = MagicMock()

        with patch("app.services.ml.risk_predictor.RiskPredictor.is_ml_safe", return_value=True), \
             patch("app.services.ml.model_registry.ModelRegistry.get_active_model", return_value=None):

            result = predictor.predict_risk(stress_score=40.0, risk_index=0.3, db=mock_db)

        assert 0.0 <= result.prediction_value <= 1.0

    def test_kill_switch_off_uses_rule_based_only(self):
        """FR-10: when is_ml_safe returns False, InferenceRuntime is never called."""
        from app.services.ml.risk_predictor import RiskPredictor
        from app.services.ml.inference_runtime import InferenceRuntime

        predictor = RiskPredictor()

        with patch.object(predictor, "is_ml_safe", return_value=False), \
             patch.object(InferenceRuntime, "load") as mock_load, \
             patch.object(InferenceRuntime, "predict_risk") as mock_pred:

            result = predictor.predict_risk(stress_score=70.0, risk_index=0.6, db=MagicMock())

        mock_load.assert_not_called()
        mock_pred.assert_not_called()
        assert 0.0 <= result.prediction_value <= 1.0


# ---------------------------------------------------------------------------
# FR-29 — MLInferenceAudit written per prediction
# ---------------------------------------------------------------------------

class TestMLInferenceAuditWritten:

    def test_inference_audit_row_written_after_prediction(self, db):
        """FR-29: predict_risk with db= must write one MLInferenceAudit row."""
        from app.models.ml_inference_audit import MLInferenceAudit
        from app.services.ml.risk_predictor import RiskPredictor

        predictor = RiskPredictor()

        with patch("app.services.ml.risk_predictor.RiskPredictor.is_ml_safe", return_value=False):
            predictor.predict_risk(stress_score=55.0, risk_index=0.4, db=db)

        audit = db.query(MLInferenceAudit)\
            .filter(MLInferenceAudit.model_version.isnot(None))\
            .order_by(MLInferenceAudit.created_at.desc())\
            .first()

        assert audit is not None
        assert audit.prediction_value is not None
        assert 0.0 <= audit.prediction_value <= 1.0
        assert audit.confidence_score is not None
        assert audit.inference_source is not None

    def test_inference_audit_contains_feature_snapshot(self, db):
        """FR-29: audit row features dict must contain the input values used for prediction."""
        from app.models.ml_inference_audit import MLInferenceAudit
        from app.services.ml.risk_predictor import RiskPredictor

        predictor = RiskPredictor()

        with patch("app.services.ml.risk_predictor.RiskPredictor.is_ml_safe", return_value=False):
            predictor.predict_risk(stress_score=62.5, risk_index=0.45, action_count=7, db=db)

        audit = db.query(MLInferenceAudit)\
            .order_by(MLInferenceAudit.created_at.desc())\
            .first()

        assert audit is not None
        assert "stress_score" in audit.features
        assert audit.features["stress_score"] == pytest.approx(62.5)


# ---------------------------------------------------------------------------
# FR-29 — /ml/inference-audits API filters
# ---------------------------------------------------------------------------

class TestInferenceAuditAPI:

    def test_inference_audit_endpoint_requires_admin(self, client, auth_headers):
        """FR-29: GET /ml/inference-audits must reject non-admin users."""
        resp = client.get("/api/v1/ml/inference-audits", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_inference_audit_filter_by_model_version(self, client, db):
        """FR-29: ?model_version=X returns only rows with that model version."""
        from app.models.ml_inference_audit import MLInferenceAudit
        from app.security.auth import create_access_token
        from app.models.user import User

        admin = User(
            id=uuid4(), full_name="ML Admin", role="admin",
            phone=f"+91{uuid4().int % 10**10:010d}",
            email=f"ml-admin-{uuid4().hex[:6]}@test.in",
            password_hash="hash", region="Punjab", is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.id), 'role': 'admin'})}"}

        target_version = f"test-v{uuid4().hex[:4]}"
        other_version = f"other-v{uuid4().hex[:4]}"

        for v in [target_version, target_version, other_version]:
            db.add(MLInferenceAudit(
                model_version=v,
                inference_source="rule_based",
                features={"stress_score": 40.0},
                prediction_value=0.3, confidence_score=0.6, risk_label="low",
            ))
        db.commit()

        resp = client.get(f"/api/v1/ml/inference-audits?model_version={target_version}", headers=admin_headers)
        assert resp.status_code == 200
        items = unwrap(resp)["items"]
        assert all(i["model_version"] == target_version for i in items)
        assert len(items) >= 2
