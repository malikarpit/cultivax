"""
Phase 3 — Data Governance Tests (NFR-13, NFR-16, NFR-17, NFR-18, NFR-19, NFR-34)

Covers:
  W6 — Consent Management (NFR-13)
  W6 — Personal Data Export (NFR-16)
  W6 — Account Anonymisation/Deletion (NFR-17)
  W6 — PII Anonymisation Service (NFR-18, NFR-19)
  W13 — Audit Retention Cron Task (NFR-34)
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from tests.conftest import unwrap


# ===========================================================================
# W6.A — Consent Management (NFR-13)
# ===========================================================================

class TestConsentPurposeListing:

    def test_list_purposes_returns_all_five(self, client):
        """GET /consent/purposes must return all defined purposes."""
        resp = client.get("/api/v1/consent/purposes")
        assert resp.status_code == 200
        data = unwrap(resp)
        assert len(data["purposes"]) == 5
        ids = [p["id"] for p in data["purposes"]]
        assert "analytics" in ids
        assert "ml_training" in ids


class TestConsentGrantAndRevoke:

    def test_user_starts_with_no_consents(self, client, auth_headers):
        """Fresh user has no granted consents."""
        resp = client.get("/api/v1/consent/me", headers=auth_headers)
        assert resp.status_code == 200
        data = unwrap(resp)
        assert all(c["granted"] is False for c in data["consents"])

    def test_grant_consent_sets_status(self, client, auth_headers):
        """POST /consent/me/{purpose} → granted=True with timestamp."""
        resp = client.post("/api/v1/consent/me/analytics", headers=auth_headers)
        assert resp.status_code == 200
        data = unwrap(resp)
        assert data["granted"] is True
        assert "granted_at" in data

    def test_grant_and_read_back(self, client, auth_headers):
        """Granted consent is visible in GET /consent/me."""
        client.post("/api/v1/consent/me/ml_training", headers=auth_headers)
        resp = client.get("/api/v1/consent/me", headers=auth_headers)
        assert resp.status_code == 200
        consents = {c["purpose"]: c for c in unwrap(resp)["consents"]}
        assert consents["ml_training"]["granted"] is True

    def test_revoke_consent_clears_status(self, client, auth_headers):
        """DELETE /consent/me/{purpose} → granted=False."""
        client.post("/api/v1/consent/me/sms_alerts", headers=auth_headers)
        resp = client.delete("/api/v1/consent/me/sms_alerts", headers=auth_headers)
        assert resp.status_code == 200
        assert unwrap(resp)["granted"] is False

    def test_revoke_then_grant_is_idempotent(self, client, auth_headers):
        """Revoking then re-granting updates back to granted."""
        client.post("/api/v1/consent/me/analytics", headers=auth_headers)
        client.delete("/api/v1/consent/me/analytics", headers=auth_headers)
        resp = client.post("/api/v1/consent/me/analytics", headers=auth_headers)
        assert resp.status_code == 200
        assert unwrap(resp)["granted"] is True

    def test_unknown_purpose_rejected(self, client, auth_headers):
        """Invalid purpose name returns 422."""
        resp = client.post("/api/v1/consent/me/hacking", headers=auth_headers)
        assert resp.status_code == 422

    def test_unauthenticated_consent_rejected(self, client):
        """No token → 401 on consent endpoints."""
        resp = client.post("/api/v1/consent/me/analytics")
        assert resp.status_code in (401, 403)


# ===========================================================================
# W6.B — Personal Data Export (NFR-16)
# ===========================================================================

class TestPersonalDataExport:

    def test_export_returns_profile_and_consents(self, client, auth_headers, farmer_user):
        """GET /account/me/export returns profile + consent fields."""
        resp = client.get("/api/v1/account/me/export", headers=auth_headers)
        assert resp.status_code == 200
        data = unwrap(resp)
        assert "profile" in data
        assert "consents" in data
        assert str(farmer_user.id) == data["profile"]["id"]

    def test_export_contains_schema_version(self, client, auth_headers):
        """Export bundle includes schema_version for forward compatibility."""
        resp = client.get("/api/v1/account/me/export", headers=auth_headers)
        data = unwrap(resp)
        assert data.get("schema_version") == "1.0"

    def test_export_includes_exported_at_timestamp(self, client, auth_headers):
        """Export bundle includes exported_at ISO timestamp."""
        resp = client.get("/api/v1/account/me/export", headers=auth_headers)
        data = unwrap(resp)
        assert "exported_at" in data
        # Must be parseable ISO format
        datetime.fromisoformat(data["exported_at"].replace("Z", "+00:00"))

    def test_unauthenticated_export_rejected(self, client):
        """No token → 401 on export."""
        resp = client.get("/api/v1/account/me/export")
        assert resp.status_code in (401, 403)


# ===========================================================================
# W6.C — Account Anonymisation / Deletion (NFR-17)
# ===========================================================================

class TestAccountDeletion:

    def test_correct_confirmation_deletes_account(self, client, db):
        """POST /account/me/delete with correct phrase soft-deletes and anonymises."""
        from app.models.user import User
        from app.security.auth import create_access_token

        user = User(
            id=uuid4(), full_name="Doomed User",
            phone=f"+91{uuid4().int % 10**10:010d}",
            email=f"doomed-{uuid4().hex[:6]}@test.in",
            password_hash="hash", role="farmer",
            region="Punjab", is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        headers = {"Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'role': 'farmer'})}"}

        resp = client.post("/api/v1/account/me/delete",
                           json={"confirmation": "DELETE MY ACCOUNT"},
                           headers=headers)
        assert resp.status_code == 200
        db.refresh(user)
        assert user.is_deleted is True
        assert user.is_active is False
        # PII overwritten
        assert user.email.endswith(".invalid")

    def test_wrong_confirmation_rejected(self, client, auth_headers):
        """Wrong confirmation phrase returns 422."""
        resp = client.post("/api/v1/account/me/delete",
                           json={"confirmation": "please delete"},
                           headers=auth_headers)
        assert resp.status_code == 422

    def test_unauthenticated_delete_rejected(self, client):
        """No token → 401."""
        resp = client.post("/api/v1/account/me/delete",
                           json={"confirmation": "DELETE MY ACCOUNT"})
        assert resp.status_code in (401, 403)


# ===========================================================================
# W6.D — Anonymisation Service (NFR-18, NFR-19)
# ===========================================================================

class TestAnonymisationService:

    def test_mask_phone_hides_all_but_last_4(self):
        from app.services.anonymization import mask_phone
        result = mask_phone("+919876543210")
        assert result.endswith("3210")
        assert "987654" not in result

    def test_mask_email_preserves_domain(self):
        from app.services.anonymization import mask_email
        result = mask_email("farmer@example.com")
        assert "@example.com" in result
        assert "farmer" not in result

    def test_redact_payload_removes_pii_keys(self):
        from app.services.anonymization import redact_payload
        payload = {"full_name": "Arpit", "soil_ph": 6.5, "phone": "+91111"}
        result = redact_payload(payload)
        assert result["full_name"] == "[REDACTED]"
        assert result["phone"] == "[REDACTED]"
        assert result["soil_ph"] == 6.5   # non-PII preserved

    def test_redact_payload_nested_dict(self):
        from app.services.anonymization import redact_payload
        payload = {"user": {"email": "x@y.com", "crop_type": "wheat"}}
        result = redact_payload(payload)
        assert result["user"]["email"] == "[REDACTED]"
        assert result["user"]["crop_type"] == "wheat"

    def test_anonymize_ml_dataset_scrubs_personal_fields(self):
        from app.services.anonymization import anonymize_ml_dataset
        records = [
            {"phone": "+91111", "email": "a@b.com", "soil_ph": 6.2, "full_name": "X"},
            {"phone": "+92222", "soil_ph": 7.0},
        ]
        result = anonymize_ml_dataset(records)
        for record in result:
            assert record.get("phone") != "+91111"
            assert record.get("email", "[REDACTED]") != "a@b.com"
        # agronomic data preserved
        assert result[0]["soil_ph"] == 6.2


# ===========================================================================
# W13 — Audit Retention Cron (NFR-34)
# ===========================================================================

class TestAuditRetentionCron:

    def test_retention_task_returns_ok(self, db):
        """_run_audit_retention returns status=ok when forced."""
        import asyncio
        with patch("app.services.cron._should_run", return_value=(True, None)):
            from app.services.cron import _run_audit_retention
            result = asyncio.run(_run_audit_retention(db, force=True))
        assert result["status"] == "ok"
        assert "sms_logs_deleted" in result

    def test_retention_task_purges_old_sms_logs(self, db):
        """Old SMS logs (beyond retention window) are deleted by cron task."""
        import asyncio
        from sqlalchemy import text
        from app.models.sms_delivery_log import SmsDeliveryLog

        # Insert a log and backdate it beyond retention window
        log = SmsDeliveryLog(
            id=uuid4(), user_id=uuid4(), phone="+91test",
            message_body="old msg", status="sent",
            message_template="test", provider="stub",
        )
        db.add(log)
        db.commit()
        db.execute(
            text("UPDATE sms_delivery_logs SET created_at = NOW() - INTERVAL '100 days' WHERE id = :lid"),
            {"lid": str(log.id)},
        )
        db.commit()

        log_id = log.id  # capture ID before deletion clears object
        db.expire(log)   # detach the in-session instance

        with patch("app.services.cron._should_run", return_value=(True, None)):
            from app.services.cron import _run_audit_retention
            result = asyncio.run(_run_audit_retention(db, force=True))

        assert result["sms_logs_deleted"] >= 1
        still_exists = db.query(SmsDeliveryLog).filter(SmsDeliveryLog.id == log_id).first()
        assert still_exists is None

    def test_retention_task_skipped_when_cadence_not_met(self, db):
        """audit_retention returns skipped when not due."""
        import asyncio
        with patch("app.services.cron._should_run", return_value=(False, "cadence_not_met")):
            from app.services.cron import _run_audit_retention
            result = asyncio.run(_run_audit_retention(db, force=False))
        assert result["status"] == "skipped"
