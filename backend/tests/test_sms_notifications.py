"""
W5 — SMS Notification Tests — NFR-11

Covers:
  - StubSMSProvider sends to in-memory list, never real network
  - send_sms_with_log writes SmsDeliveryLog row on success and failure
  - AlertService.send_critical_sms_for_unacknowledged dispatches to High/Critical alerts
  - Cron _run_critical_sms_dispatch task runs and returns sms_sent count
  - TwilioSMSProvider returns error gracefully when twilio not installed
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy import text


# ---------------------------------------------------------------------------
# StubSMSProvider — in-memory, no real sends
# ---------------------------------------------------------------------------

class TestStubSMSProvider:

    def test_stub_send_records_message(self):
        """Stub records sent messages in memory."""
        from app.services.notifications.sms_provider import StubSMSProvider
        provider = StubSMSProvider()
        result = provider.send("+919876543210", "Hello test")
        assert result.success is True
        assert len(provider.sent) == 1
        assert provider.sent[0]["phone"] == "+919876543210"

    def test_stub_reset_clears_history(self):
        """Stub.reset() clears sent list."""
        from app.services.notifications.sms_provider import StubSMSProvider
        provider = StubSMSProvider()
        provider.send("+919876543210", "msg1")
        provider.reset()
        assert len(provider.sent) == 0

    def test_stub_provides_sequential_message_ids(self):
        """Stub returns incrementing provider_message_ids."""
        from app.services.notifications.sms_provider import StubSMSProvider
        provider = StubSMSProvider()
        r1 = provider.send("+91111", "a")
        r2 = provider.send("+91222", "b")
        assert r1.provider_message_id != r2.provider_message_id

    def test_twilio_provider_handles_missing_package_gracefully(self):
        """TwilioSMSProvider returns error when twilio package missing."""
        from app.services.notifications.sms_provider import TwilioSMSProvider
        provider = TwilioSMSProvider("sid", "token", "+1234")
        with patch.dict("sys.modules", {"twilio": None, "twilio.rest": None}):
            result = provider.send("+919876543210", "test")
        assert result.success is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# send_sms_with_log — DB log row written
# ---------------------------------------------------------------------------

class TestSendSmsWithLog:

    def test_successful_send_writes_sent_log(self, db):
        """send_sms_with_log writes SmsDeliveryLog with status=sent."""
        from app.models.sms_delivery_log import SmsDeliveryLog
        from app.services.notifications.sms_provider import send_sms_with_log, StubSMSProvider

        user_id = uuid4()
        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=StubSMSProvider()):
            result = send_sms_with_log(db, user_id, "+919876543210", "Test alert", "test_template")

        assert result is True
        log = db.query(SmsDeliveryLog).filter(SmsDeliveryLog.user_id == user_id).first()
        assert log is not None
        assert log.status == "sent"
        assert log.phone == "+919876543210"

    def test_failed_send_writes_failed_log(self, db):
        """send_sms_with_log writes status=failed when provider returns error."""
        from app.models.sms_delivery_log import SmsDeliveryLog
        from app.services.notifications.sms_provider import send_sms_with_log, SMSResult

        failing_provider = MagicMock()
        failing_provider.send.return_value = SMSResult(success=False, error="network_error")
        failing_provider.provider_name = "mock_fail"

        user_id = uuid4()
        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=failing_provider):
            result = send_sms_with_log(db, user_id, "+919876543210", "Test alert")

        assert result is False
        log = db.query(SmsDeliveryLog).filter(SmsDeliveryLog.user_id == user_id).first()
        assert log is not None
        assert log.status == "failed"
        assert "network_error" in (log.provider_response or "")

    def test_log_contains_provider_name(self, db):
        """Delivery log records the provider name used."""
        from app.models.sms_delivery_log import SmsDeliveryLog
        from app.services.notifications.sms_provider import send_sms_with_log, StubSMSProvider

        user_id = uuid4()
        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=StubSMSProvider()):
            send_sms_with_log(db, user_id, "+919876543210", "msg")

        log = db.query(SmsDeliveryLog).filter(SmsDeliveryLog.user_id == user_id).first()
        assert log.provider == "stub"


# ---------------------------------------------------------------------------
# AlertService.send_critical_sms_for_unacknowledged
# ---------------------------------------------------------------------------

class TestAlertServiceSMSDispatch:

    def _create_user_with_phone(self, db):
        from app.models.user import User
        u = User(
            id=uuid4(), full_name="SMS Test User",
            phone=f"+91{uuid4().int % 10**10:010d}",
            email=f"sms-{uuid4().hex[:6]}@test.in",
            password_hash="hash", role="farmer",
            region="Punjab", is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    def _create_stale_alert(self, db, user_id, urgency: str, minutes_old: int = 60):
        """Insert an alert and backdate its created_at via raw SQL."""
        from app.models.alert import Alert
        alert_id = uuid4()
        crop_id = uuid4()
        a = Alert(
            id=alert_id,
            user_id=user_id,
            crop_instance_id=crop_id,
            alert_type="stress_alert",
            severity="High",
            message=f"Test {urgency} alert",
            urgency_level=urgency,
            is_acknowledged=False,
            is_deleted=False,
        )
        db.add(a)
        db.commit()
        # Backdate via parameterised raw SQL (uses text() for SQLAlchemy 1.4+)
        db.execute(
            text("UPDATE alerts SET created_at = NOW() - INTERVAL ':mins minutes' WHERE id = :alert_id".replace(
                "':mins minutes'", f"'{minutes_old} minutes'"
            )),
            {"alert_id": str(alert_id)},
        )
        db.commit()
        db.refresh(a)
        return a

    def test_dispatches_sms_for_critical_unacknowledged_alert(self, db):
        """AlertService dispatches SMS for unacknowledged Critical alerts older than 30 min."""
        from app.services.notifications import AlertService
        from app.services.notifications.sms_provider import StubSMSProvider

        user = self._create_user_with_phone(db)
        self._create_stale_alert(db, user.id, "Critical", minutes_old=45)

        stub = StubSMSProvider()
        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=stub):
            sent = AlertService(db).send_critical_sms_for_unacknowledged(min_urgency="High", stale_minutes=30)

        assert sent >= 1
        assert any(m["phone"] == user.phone for m in stub.sent)

    def test_does_not_dispatch_for_acknowledged_alerts(self, db):
        """Acknowledged alerts should not trigger SMS."""
        from app.services.notifications import AlertService
        from app.services.notifications.sms_provider import StubSMSProvider

        user = self._create_user_with_phone(db)
        alert = self._create_stale_alert(db, user.id, "Critical", minutes_old=60)
        alert.is_acknowledged = True
        db.commit()

        stub = StubSMSProvider()
        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=stub):
            AlertService(db).send_critical_sms_for_unacknowledged(min_urgency="High", stale_minutes=30)

        user_sent = [m for m in stub.sent if m["phone"] == user.phone]
        assert len(user_sent) == 0

    def test_does_not_dispatch_for_low_urgency_alerts(self, db):
        """Low/Medium urgency alerts should not trigger SMS when min_urgency=High."""
        from app.services.notifications import AlertService
        from app.services.notifications.sms_provider import StubSMSProvider

        user = self._create_user_with_phone(db)
        self._create_stale_alert(db, user.id, "Low", minutes_old=60)
        self._create_stale_alert(db, user.id, "Medium", minutes_old=60)

        stub = StubSMSProvider()
        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=stub):
            AlertService(db).send_critical_sms_for_unacknowledged(min_urgency="High", stale_minutes=30)

        user_sent = [m for m in stub.sent if m["phone"] == user.phone]
        assert len(user_sent) == 0


# ---------------------------------------------------------------------------
# Cron task integration
# ---------------------------------------------------------------------------

class TestCronSMSDispatchTask:

    def test_cron_sms_dispatch_returns_ok_status(self, db):
        """_run_critical_sms_dispatch cron task returns status=ok."""
        import asyncio
        from app.services.notifications.sms_provider import StubSMSProvider

        with patch("app.services.notifications.sms_provider.get_sms_provider", return_value=StubSMSProvider()), \
             patch("app.services.cron._should_run", return_value=(True, None)):
            from app.services.cron import _run_critical_sms_dispatch
            result = asyncio.run(_run_critical_sms_dispatch(db, force=True))

        assert result["status"] == "ok"
        assert "sms_sent" in result

    def test_cron_sms_dispatch_skipped_when_cadence_not_met(self, db):
        """_run_critical_sms_dispatch returns skipped when not enough time elapsed."""
        import asyncio

        with patch("app.services.cron._should_run", return_value=(False, "cadence_not_met")):
            from app.services.cron import _run_critical_sms_dispatch
            result = asyncio.run(_run_critical_sms_dispatch(db, force=False))

        assert result["status"] == "skipped"
