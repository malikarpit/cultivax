import hashlib
import json
import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import settings
from app.security.admin_api_key import AdminAPIKey, require_admin_api_key


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _build_request(
    method: str = "POST",
    path: str = "/admin/health-check",
    body: bytes = b"",
) -> Request:
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [(b"host", b"testserver")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope, receive=receive)


@pytest.mark.asyncio
async def test_admin_api_key_fail_closed_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")
    monkeypatch.setattr(settings, "ADMIN_API_KEYS_JSON", "")
    monkeypatch.setattr(settings, "APP_ENV", "development")

    with pytest.raises(HTTPException) as exc:
        await require_admin_api_key(
            request=_build_request(),
            x_api_key="cultivax_admin_test_key",
            x_signature=None,
            x_timestamp=None,
        )
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_admin_api_key_accepts_single_sha256_key(monkeypatch):
    api_key = "cultivax_admin_wave2_single"
    monkeypatch.setattr(settings, "ADMIN_API_KEY", f"sha256:{_sha256(api_key)}")
    monkeypatch.setattr(settings, "ADMIN_API_KEYS_JSON", "")
    monkeypatch.setattr(settings, "ADMIN_REQUIRE_API_SIGNATURE", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    result = await require_admin_api_key(
        request=_build_request(),
        x_api_key=api_key,
        x_signature=None,
        x_timestamp=None,
    )
    assert result is True


@pytest.mark.asyncio
async def test_admin_api_key_rejects_invalid_key(monkeypatch):
    monkeypatch.setattr(
        settings,
        "ADMIN_API_KEY",
        f"sha256:{_sha256('cultivax_admin_valid_key')}",
    )
    monkeypatch.setattr(settings, "ADMIN_API_KEYS_JSON", "")
    monkeypatch.setattr(settings, "APP_ENV", "development")

    with pytest.raises(HTTPException) as exc:
        await require_admin_api_key(
            request=_build_request(),
            x_api_key="cultivax_admin_wrong_key",
            x_signature=None,
            x_timestamp=None,
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_api_key_keyring_with_key_id(monkeypatch):
    key_primary = "cultivax_admin_primary"
    key_secondary = "cultivax_admin_secondary"
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")
    monkeypatch.setattr(
        settings,
        "ADMIN_API_KEYS_JSON",
        json.dumps(
            {
                "keys": [
                    {"key_id": "primary", "sha256": _sha256(key_primary), "active": True},
                    {"key_id": "secondary", "sha256": _sha256(key_secondary), "active": False},
                ]
            }
        ),
    )
    monkeypatch.setattr(settings, "APP_ENV", "development")

    ok = await require_admin_api_key(
        request=_build_request(),
        x_api_key=key_primary,
        x_api_key_id="primary",
        x_signature=None,
        x_timestamp=None,
    )
    assert ok is True

    with pytest.raises(HTTPException) as exc:
        await require_admin_api_key(
            request=_build_request(),
            x_api_key=key_primary,
            x_api_key_id="missing",
            x_signature=None,
            x_timestamp=None,
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_api_key_rejects_plaintext_in_production(monkeypatch):
    api_key = "cultivax_admin_plaintext_prod"
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", api_key)
    monkeypatch.setattr(settings, "ADMIN_API_KEYS_JSON", "")

    with pytest.raises(HTTPException) as exc:
        await require_admin_api_key(
            request=_build_request(),
            x_api_key=api_key,
            x_signature=None,
            x_timestamp=None,
        )
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_admin_api_key_optional_signature_enforcement(monkeypatch):
    api_key = "cultivax_admin_sign_required"
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", f"sha256:{_sha256(api_key)}")
    monkeypatch.setattr(settings, "ADMIN_API_KEYS_JSON", "")
    monkeypatch.setattr(settings, "ADMIN_REQUIRE_API_SIGNATURE", True)

    with pytest.raises(HTTPException) as exc:
        await require_admin_api_key(
            request=_build_request(),
            x_api_key=api_key,
            x_signature=None,
            x_timestamp=None,
        )
    assert exc.value.status_code == 400

    timestamp = int(time.time())
    signature = AdminAPIKey.sign_request(
        method="POST",
        path="/admin/health-check",
        body="",
        timestamp=timestamp,
        api_secret=settings.SECRET_KEY,
    )
    ok = await require_admin_api_key(
        request=_build_request(),
        x_api_key=api_key,
        x_signature=signature,
        x_timestamp=timestamp,
    )
    assert ok is True
