"""
CSP Violation Report Endpoint

Receives Content-Security-Policy violation reports from browsers (report-to directive).
MSDD §7.14 — Security event logging for frontend violations.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security"])


class CSPReport(BaseModel):
    """Schema for browser CSP violation reports (report-to format)."""

    type: Optional[str] = None
    url: Optional[str] = None
    body: Optional[Dict[str, Any]] = None


@router.post(
    "/csp-report",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Receive CSP violation reports",
    description=(
        "Browser-reported Content-Security-Policy violations. "
        "This endpoint is referenced by the Report-To header and requires no authentication. "
        "Reports are logged at WARNING level and never stored as PII."
    ),
    include_in_schema=False,  # Hide from dev docs — not a user-facing API
)
async def receive_csp_report(request: Request):
    """
    Ingest CSP violation reports from browsers.

    Browsers may POST either:
    - report-to format: {"type": "csp-violation", "body": {...}}
    - report-uri format: {"csp-report": {...}}

    We log both and return 204 immediately (browsers ignore the response body).
    """
    try:
        body = await request.json()
    except Exception:
        # Invalid JSON from browser — ignore silently
        return JSONResponse(status_code=204, content=None)

    # Normalise across report-to vs report-uri formats
    if isinstance(body, dict):
        report_body = body.get("body") or body.get("csp-report") or body
        blocked_uri = report_body.get("blocked-uri") or report_body.get(
            "blockedURL", "unknown"
        )
        violated_directive = report_body.get("violated-directive") or report_body.get(
            "effectiveDirective", "unknown"
        )
        document_uri = report_body.get("document-uri") or report_body.get(
            "documentURL", "unknown"
        )

        logger.warning(
            "CSP violation reported",
            extra={
                "event": "csp_violation",
                "blocked_uri": blocked_uri,
                "violated_directive": violated_directive,
                "document_uri": document_uri,
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )
    else:
        logger.warning(f"CSP violation (unparseable body): {str(body)[:200]}")

    return JSONResponse(status_code=204, content=None)
