# ASVS Level 2 Compliance Checklist — CultivaX Backend

**Standard**: OWASP Application Security Verification Standard (ASVS) v4.0 Level 2  
**Wave**: 2 — Security Hardening  
**Date**: 2026-04-04  
**Status**: ✅ PASS | ⚠️ PARTIAL | ❌ FAIL | 🔲 N/A

---

## V1 Architecture, Design and Threat Modeling

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V1.1.1 | SSDLC established | ✅ | MSDD/TDD contracts govern all changes |
| V1.2.1 | No hardcoded credentials in source | ✅ | All secrets via env vars; `.env` in `.gitignore` |
| V1.6.1 | Shared secrets stored in secrets vault | ⚠️ | `.env` file locally; Cloud Run uses Secret Manager |
| V1.9.1 | All communications encrypted (TLS) | ✅ | Cloud Run enforces HTTPS; HSTS in production |

---

## V2 Authentication

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V2.1.1 | Password min length 8 chars | ✅ | `AuthService` enforces 8+ |
| V2.1.2 | No truncation of passwords | ✅ | bcrypt/argon2 handles full strings |
| V2.2.1 | Anti-brute-force controls | ✅ | Wave 2: auth endpoints limited to 10 req/min per IP |
| V2.3.1 | Credential reset uses secure OTP | ✅ | OTP flow via `AuthService.request_otp` |
| V2.5.1 | Credentials not sent in GET params | ✅ | All auth via POST body / httpOnly cookie |
| V2.8.3 | Time-based OTP expiry enforced | ✅ | OTP TTL = 10 minutes |

---

## V3 Session Management

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V3.1.1 | Session IDs not exposed in URLs | ✅ | JWT in httpOnly cookie |
| V3.2.2 | New session ID generated after authentication | ✅ | New refresh token on each login |
| V3.3.1 | Sessions expire after inactivity | ✅ | Access token: 15 min; refresh: 7 days |
| V3.4.1 | Cookie uses Secure flag | ⚠️ | Set in production config; dev uses http |
| V3.4.2 | Cookie uses HttpOnly flag | ✅ | `httponly=True` in `auth.py` |
| V3.4.3 | Cookie uses SameSite | ✅ | `samesite="lax"` |
| V3.5.1 | OAuth refresh tokens rotated | ✅ | Refresh token blacklisted after use |

---

## V4 Access Control

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V4.1.1 | Deny by default | ✅ | `get_current_user` required on all private endpoints |
| V4.1.3 | Principle of least privilege enforced | ✅ | `require_role(["admin"])` on admin endpoints |
| V4.2.1 | Trusted API layer for data access | ✅ | No direct DB access from routes; uses service layer |
| V4.3.1 | Admin UI requires additional auth | ✅ | `require_admin_api_key` dependency on admin routes |

---

## V5 Validation, Sanitization and Encoding

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V5.1.1 | HTTP parameter pollution not possible | ✅ | FastAPI/Pydantic parses all inputs |
| V5.1.3 | All inputs validated via schema | ✅ | Pydantic models on every endpoint |
| V5.2.1 | HTML entity encoding for untrusted data | ✅ | API returns JSON; no HTML rendering |
| V5.4.4 | Path traversal prevented | ✅ | File uploads go to GCS; no local path exposure |

---

## V7 Error Handling and Logging

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V7.1.1 | No PII in log messages | ✅ | Phones redacted in security events |
| V7.1.2 | Sufficient context logged for forensics | ✅ | `request_id`, `user_id`, `path` in all events |
| V7.2.1 | No stack traces in production responses | ✅ | `ErrorHandlerMiddleware` masks in production |
| V7.4.1 | Generic error messages to client | ✅ | Errors sanitized; detail in server logs only |

---

## V8 Data Protection

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V8.1.1 | Sensitive data not cached | ✅ | No cache headers on auth endpoints |
| V8.2.1 | PII minimized in logs | ✅ | No passwords, tokens, or full phones in logs |
| V8.3.1 | Sensitive data not exposed in URL | ✅ | All sensitive params in request body |
| V8.3.7 | Soft-delete pattern (data retained) | ✅ | `is_deleted` flag on all models |

---

## V9 Communication

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V9.1.1 | TLS required for all connections | ✅ | HTTPS enforced by Cloud Run; HSTS header set |
| V9.1.3 | TLS 1.2+ only | ✅ | Cloud Run default (TLS 1.2/1.3) |
| V9.2.2 | Internal communications encrypted | ✅ | Cloud SQL via unix socket inside VPC |

---

## V11 Business Logic

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V11.1.4 | Business logic limits enforced | ✅ | Role-based rate limits (farmer/provider/admin) |
| V11.1.7 | Idempotency for high-value operations | ✅ | Wave 2: mandatory Idempotency-Key on service-requests/reviews/sync |

---

## V13 API and Web Service

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V13.1.1 | All API inputs validated | ✅ | Pydantic schemas on all routes |
| V13.2.1 | Sensitive list operations protected | ✅ | Owner/role filters on all list endpoints |
| V13.4.1 | Webhook signature validation | ✅ | WhatsApp: HMAC-SHA256 `X-Hub-Signature-256` |

---

## V14 Configuration

| ID | Control | Status | Notes |
|----|---------|--------|-------|
| V14.1.1 | Build warnings treated as errors | ⚠️ | Pydantic deprecation warnings present (Pydantic v1 class Config) |
| V14.2.1 | All components up to date | ⚠️ | `passlib` uses deprecated `crypt` module — deferred |
| V14.4.1 | HTTP response headers include security headers | ✅ | CSP, HSTS, X-Frame, X-Content-Type, Referrer-Policy |
| V14.4.3 | CSP enforced on all responses | ✅ | Wave 2: per-request nonce, no `unsafe-inline` on API paths |
| V14.4.4 | Frame-ancestors none | ✅ | `frame-ancestors 'none'` in CSP |
| V14.4.5 | HSTS enabled in production | ✅ | `max-age=31536000; includeSubDomains; preload` |
| V14.4.6 | Referrer-Policy set | ✅ | `strict-origin-when-cross-origin` |
| V14.4.7 | Permissions-Policy | ✅ | Blocks camera, mic, USB, payment, geolocation |
| V14.5.1 | X-Frame-Options set | ✅ | `DENY` |
| V14.5.3 | Rate limiting implemented | ✅ | Sliding window Redis (in-memory fallback); per-role limits |

---

## Open Items (to close in Wave 5)

| ID | Item | Priority |
|----|------|----------|
| V1.6.1 | Migrate local `.env` secrets to Cloud Secret Manager | P2 |
| V2.1.5 | Password length maximum (ASVS recommends no max) — review `MAX_PASSWORD_LENGTH` | P3 |
| V14.1.1 | Resolve Pydantic `class Config` deprecation warnings | P3 |
| V14.2.1 | Upgrade `passlib` to remove `crypt` dependency | P3 |
