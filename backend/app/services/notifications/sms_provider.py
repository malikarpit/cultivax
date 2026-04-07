"""
SMS Provider Abstraction — NFR-11

Provides a provider-agnostic SMS sending interface with:
- Twilio production provider
- Stub provider for tests (no real sends)
- SmsDeliveryLog written on every attempt
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SMSResult:
    success: bool
    provider_message_id: Optional[str] = None
    error: Optional[str] = None


class SMSProvider(ABC):
    """Abstract base — all providers must implement send()."""

    @abstractmethod
    def send(self, phone: str, message: str) -> SMSResult:
        """Send a plain-text SMS. Returns SMSResult."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...


class StubSMSProvider(SMSProvider):
    """
    In-memory stub provider used in tests and development.
    Records all sent messages; never makes real network calls.
    """

    provider_name = "stub"

    def __init__(self):
        self.sent: list[dict] = []

    def send(self, phone: str, message: str) -> SMSResult:
        self.sent.append({"phone": phone, "message": message})
        logger.info(f"[StubSMS] Would send to {phone}: {message[:60]}")
        return SMSResult(success=True, provider_message_id=f"stub-{len(self.sent)}")

    def reset(self):
        self.sent.clear()


class TwilioSMSProvider(SMSProvider):
    """Twilio-backed production SMS provider."""

    provider_name = "twilio"

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self._sid = account_sid
        self._token = auth_token
        self._from = from_number

    def send(self, phone: str, message: str) -> SMSResult:
        try:
            from twilio.rest import Client  # type: ignore

            client = Client(self._sid, self._token)
            msg = client.messages.create(body=message, from_=self._from, to=phone)
            return SMSResult(success=True, provider_message_id=msg.sid)
        except ImportError:
            logger.error("twilio package not installed — cannot send SMS")
            return SMSResult(success=False, error="twilio_not_installed")
        except Exception as exc:
            logger.error(f"Twilio send failed: {exc}")
            return SMSResult(success=False, error=str(exc))


def get_sms_provider() -> SMSProvider:
    """
    Factory: returns the configured SMS provider from environment.
    Falls back to StubSMSProvider if no config is present.
    """
    try:
        from app.config import settings

        provider_name = getattr(settings, "SMS_PROVIDER", "stub")
        if provider_name == "twilio":
            return TwilioSMSProvider(
                account_sid=settings.TWILIO_ACCOUNT_SID,
                auth_token=settings.TWILIO_AUTH_TOKEN,
                from_number=settings.TWILIO_FROM_NUMBER,
            )
    except Exception as exc:
        logger.warning(f"SMS provider config error — using stub: {exc}")
    return StubSMSProvider()


def send_sms_with_log(
    db, user_id, phone: str, message: str, template: str = ""
) -> bool:
    """
    Send an SMS and write an SmsDeliveryLog row with result.
    Returns True on success, False on failure.
    """
    from app.models.sms_delivery_log import SmsDeliveryLog

    provider = get_sms_provider()
    result = provider.send(phone, message)

    err_msg = result.provider_message_id or result.error or ""
    log = SmsDeliveryLog(
        user_id=user_id,
        phone=phone,
        message_template=template,
        message_body=message[:500],
        attempt_count=1,
        status="sent" if result.success else "failed",
        provider=provider.provider_name,
        provider_response=str(err_msg)[:250], # Truncate to avoid DB DataError
    )
    try:
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"SmsDeliveryLog commit failed: {e}")

    return result.success
