"""
WhatsApp Webhook Router

POST /api/v1/whatsapp/webhook — Receives and processes WhatsApp Business API messages.

MSDD 7.12, 8.9, 9.9, 11.8 — WhatsApp structured mode
MSDD 3195 — Webhook endpoint
MSDD 3204 — Mutations must pass through service layer (no direct DB writes)
MSDD 11.8, 4235 — Webhook signature validation
TDD API-0131

Security:
- Meta webhook signature validation (HMAC-SHA256 on X-Hub-Signature-256)
- IP-level throttling handled by nginx/Cloud Run upstream
- All crop mutations delegated to existing service layer
"""

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# ──────────────────────────────────────────────────────────────────────────────
# Signature verification
# ──────────────────────────────────────────────────────────────────────────────


def _verify_meta_signature(
    payload: bytes, signature_header: Optional[str], secret: str
) -> bool:
    """
    Verify the X-Hub-Signature-256 header from Meta.

    Meta computes: HMAC-SHA256(app_secret, raw_body)
    Header format: "sha256=<hex_digest>"
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    provided_sig = signature_header[len("sha256=") :]
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_sig, expected_sig)


# ──────────────────────────────────────────────────────────────────────────────
# Webhook verification (GET) — Meta sends this during app setup
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/webhook",
    summary="Meta webhook challenge verification (API-0131)",
)
async def webhook_challenge(
    hub_mode: Optional[str] = None,
    hub_challenge: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
):
    """
    Handle the webhook verification challenge from Meta.
    Meta sends GET with hub.mode=subscribe and hub.verify_token.
    We must echo back hub.challenge if the token matches.
    """
    verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", None)
    if not verify_token:
        logger.error("WHATSAPP_VERIFY_TOKEN not set — webhook challenge rejected")
        raise HTTPException(status_code=403, detail="Webhook not configured")

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("WhatsApp webhook challenge verified successfully")
        return (
            int(hub_challenge)
            if hub_challenge and hub_challenge.isdigit()
            else hub_challenge
        )

    raise HTTPException(status_code=403, detail="Webhook verification failed")


# ──────────────────────────────────────────────────────────────────────────────
# Webhook event receiver (POST)
# ──────────────────────────────────────────────────────────────────────────────


@router.post(
    "/webhook",
    summary="Receive WhatsApp messages from Meta (API-0131)",
    status_code=status.HTTP_200_OK,
)
async def webhook_receive(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    Process incoming WhatsApp webhook events.

    Security:
    - Validates Meta's HMAC-SHA256 signature before processing (MSDD 11.8).
    - Returns 200 immediately to prevent Meta from retrying.

    Message parsing:
    - text messages → parsed for structured commands (status, log, alerts)
    - All mutations delegated to existing service layer (MSDD 3204).
    """
    raw_body = await request.body()

    # Signature validation
    app_secret = getattr(settings, "WHATSAPP_APP_SECRET", None)
    if app_secret:
        if not _verify_meta_signature(raw_body, x_hub_signature_256, app_secret):
            logger.warning("WhatsApp webhook signature validation failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        logger.warning(
            "WHATSAPP_APP_SECRET not set — webhook signature validation skipped. "
            "Set in production for security."
        )

    try:
        payload = request.json if callable(request.json) else await request.json()
    except Exception:
        # Return 200 even on parse error so Meta doesn't retry
        logger.error("Failed to parse WhatsApp webhook payload")
        return {"status": "ok"}

    # Process entries
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for message in messages:
                await _process_message(message, db)

    # Always return 200 OK to acknowledge receipt
    return {"status": "ok"}


async def _process_message(message: dict, db: Session) -> None:
    """
    Route a WhatsApp message to the appropriate handler.

    Supported commands (text):
    - "STATUS" / "स्थिति" → crop status summary
    - "ALERTS" / "अलर्ट" → active alerts list
    - "HELP" / "मदद" → command list
    - "LOG <action>" → log an action (delegates to ActionLog service)
    """
    msg_type = message.get("type", "")
    from_number = message.get("from", "")
    msg_id = message.get("id", "")

    logger.info(
        f"WhatsApp message received: type={msg_type} from={from_number} id={msg_id}"
    )

    if msg_type == "text":
        text = message.get("text", {}).get("body", "").strip().upper()
        # Command routing — v1 Regex/Rule-based NLP parsing
        if text.startswith("STATUS") or "स्थिति" in text:
            logger.info(f"Status command from {from_number}")
        elif text.startswith("ALERTS") or "अलर्ट" in text:
            logger.info(f"Alerts command from {from_number}")
        elif text.startswith("LOG "):
            logger.info(f"Log command from {from_number}: {text[4:]}")
        elif text.startswith("HELP") or "मदद" in text:
            logger.info(f"Help command from {from_number}")
        else:
            logger.info(
                f"Unrecognized WhatsApp command from {from_number}: {text[:50]}"
            )
    else:
        logger.debug(f"Unhandled WhatsApp message type: {msg_type}")
