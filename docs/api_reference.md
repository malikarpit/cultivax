# CultivaX API Reference

> **Version**: 1.0.0  
> **Base URL**: `https://<host>/api/v1`  
> **Authentication**: JWT Bearer Token  
> **Content-Type**: `application/json`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Crop Instances](#2-crop-instances)
3. [Actions](#3-actions)
4. [Simulation](#4-simulation)
5. [Yield](#5-yield)
6. [Recommendations](#6-recommendations)
7. [Alerts](#7-alerts)
8. [Service Providers](#8-service-providers)
9. [Equipment](#9-equipment)
10. [Labor](#10-labor)
11. [Service Requests](#11-service-requests)
12. [Reviews](#12-reviews)
13. [Media](#13-media)
14. [Offline Sync](#14-offline-sync)
15. [ML Models](#15-ml-models)
16. [Crop Rule Templates](#16-crop-rule-templates)
17. [Feature Flags](#17-feature-flags)
18. [Admin](#18-admin)
19. [System](#19-system-endpoints)
20. [Error Handling](#20-error-handling)

---

## Authentication Overview

All endpoints except `/auth/register`, `/auth/login`, `/health`, and `/` require a valid JWT Bearer token.

Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after the configured `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes). Use the `/auth/refresh` endpoint to obtain a new token pair.

### Roles

| Role | Description |
|------|-------------|
| `farmer` | Standard user — can manage crops, log actions, submit yields |
| `provider` | Service provider — can manage equipment, respond to service requests |
| `admin` | Administrator — full access to user management, feature flags, system health |

---

## 1. Authentication

### `POST /auth/register`

Register a new user account and receive a JWT token pair.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | ✅ | User's full name |
| `phone` | string | ✅ | Phone number (unique) |
| `email` | string | ❌ | Email address (unique if provided) |
| `password` | string | ✅ | Password (min 8 characters) |
| `role` | string | ✅ | One of: `farmer`, `provider`, `admin` |
| `region` | string | ❌ | User's region |
| `preferred_language` | string | ❌ | Language preference (e.g., `en`, `hi`) |

**Response** `201 Created`:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "full_name": "Arpit Malik",
    "phone": "+919876543210",
    "email": "arpit@example.com",
    "role": "farmer",
    "region": "haryana",
    "is_active": true,
    "created_at": "2026-03-30T10:00:00Z"
  }
}
```

**Errors:**

| Code | Detail |
|------|--------|
| `409` | Phone number or email already registered |
| `422` | Invalid role or validation error |

---

### `POST /auth/login`

Authenticate with phone number and password.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | string | ✅ | Registered phone number |
| `password` | string | ✅ | Account password |

**Response** `200 OK`: Same structure as register response.

**Errors:**

| Code | Detail |
|------|--------|
| `401` | Invalid phone number or password |
| `403` | Account is deactivated |

---

### `POST /auth/refresh`

Exchange a valid refresh token for a new access + refresh token pair.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | ✅ | Valid refresh token |

**Response** `200 OK`: Same structure as register response.

**Errors:**

| Code | Detail |
|------|--------|
| `401` | Invalid or expired refresh token, or user not found |

---

## 2. Crop Instances

### `POST /crops/`

Create a new crop instance with automatic seasonal window assignment.

**Auth Required**: ✅ (farmer)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crop_type` | string | ✅ | Crop type (e.g., `wheat`, `rice`, `cotton`) |
| `variety` | string | ❌ | Specific variety |
| `sowing_date` | date | ✅ | Actual sowing date |
| `field_area_acres` | float | ❌ | Field area in acres |
| `region` | string | ✅ | Growing region |
| `notes` | string | ❌ | Farmer notes |

**Response** `201 Created`: CropInstance object with computed `seasonal_window_category`.

---

### `GET /crops/`

List crop instances with pagination and filtering.

**Auth Required**: ✅

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | `1` | Page number (≥ 1) |
| `per_page` | int | `20` | Items per page (1–100) |
| `state` | string | — | Filter by state (`created`, `active`, `harvested`, `closed`) |
| `crop_type` | string | — | Filter by crop type |
| `region` | string | — | Filter by region |
| `include_archived` | bool | `false` | Include archived crop instances |

**Response** `200 OK`:

```json
{
  "items": [ /* CropInstance objects */ ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### `GET /crops/{crop_id}`

Get a single crop instance with computed state from replay.

**Auth Required**: ✅

**Response** `200 OK`: Full CropInstance object.

---

### `PUT /crops/{crop_id}`

Update non-state fields of a crop instance.

**Auth Required**: ✅ (owner)

**Request Body**: Partial update — only fields provided will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `variety` | string | Crop variety |
| `field_area_acres` | float | Field area |
| `notes` | string | Notes |

---

### `PUT /crops/{crop_id}/sowing-date`

Modify the sowing date of a crop instance. **Triggers full replay from scratch.**

**Auth Required**: ✅ (owner)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_sowing_date` | date | ✅ | New sowing date |

> ⚠️ **Note**: `seasonal_window_category` is immutable and will NOT be recalculated.

---

## 3. Actions

### `POST /crops/{crop_id}/actions`

Log a farmer action on a crop instance with chronological validation.

**Auth Required**: ✅

**Validation Rules:**
- `effective_date` must be ≥ sowing date
- `effective_date` must be ≥ last action's effective date (within same crop)
- Rejects if `idempotency_key` already exists

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | string | ✅ | Action type (e.g., `irrigation`, `fertilizer`, `pesticide`, `observation`) |
| `effective_date` | datetime | ✅ | When the action occurred |
| `quantity` | float | ❌ | Quantity applied |
| `unit` | string | ❌ | Unit of measurement |
| `notes` | string | ❌ | Additional notes |
| `idempotency_key` | string | ❌ | Unique key for deduplication |

**Response** `201 Created`: ActionLog object.

**Errors:**

| Code | Detail |
|------|--------|
| `403` | Not the owner of this crop instance |
| `422` | Chronological invariant violated or duplicate idempotency key |

---

## 4. Simulation

### `POST /crops/{crop_id}/simulate`

Run a what-if simulation with hypothetical actions in an isolated memory context.

**Auth Required**: ✅

The simulation engine deep-copies the crop state and applies hypothetical actions without mutating the real timeline.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hypothetical_actions` | array | ✅ | List of hypothetical ActionLog entries |
| `include_stress_projection` | bool | ❌ | Include stress score projections (default: `true`) |

**Response** `200 OK`:

```json
{
  "simulated_state": { /* projected crop state */ },
  "stress_delta": -0.15,
  "risk_index_delta": -0.08,
  "projected_growth_stage": "grain_filling",
  "day_number_projected": 75,
  "warnings": []
}
```

---

## 5. Yield

### `POST /crops/{crop_id}/yield`

Submit harvest yield for a crop instance.

**Auth Required**: ✅ (owner)

Implements the MSDD 1.12 dual-truth model:
- **Farmer Truth**: Self-reported actual yield
- **ML Truth**: Model-predicted yield (computed internally)
- **Biological Limit Cap**: Enforces maximum plausible yield per crop type

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actual_yield_kg` | float | ✅ | Farmer-reported yield in kg |
| `harvest_date` | date | ✅ | Date of harvest |
| `quality_grade` | string | ❌ | Harvest quality (A/B/C) |
| `notes` | string | ❌ | Additional comments |

---

## 6. Recommendations

### `GET /crops/{crop_id}/recommendations`

Get prioritized action recommendations for a crop instance.

**Auth Required**: ✅

Recommendations are generated daily based on:
- Current stress scores
- Risk index
- Growth stage
- Deviation profile
- Weather forecast data

**Response** `200 OK`:

```json
[
  {
    "id": "uuid",
    "crop_instance_id": "uuid",
    "recommendation_type": "irrigation",
    "priority_score": 0.85,
    "title": "Increase Irrigation",
    "description": "Soil moisture is below optimal for current growth stage",
    "basis": "stress_score_high",
    "created_at": "2026-03-30T10:00:00Z"
  }
]
```

---

## 7. Alerts

### `GET /alerts/`

Get alerts for the authenticated user.

**Auth Required**: ✅

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `is_read` | bool | — | Filter by read/unread status |
| `severity` | string | — | Filter by severity |

### `PUT /alerts/{alert_id}/read`

Mark an alert as read.

**Auth Required**: ✅

> **Throttling**: Maximum 3 alerts per crop per 24 hours (configurable).

---

## 8. Service Providers

### `POST /providers/`

Register as a service provider.

**Auth Required**: ✅ (provider role)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `business_name` | string | ✅ | Provider business name |
| `service_type` | string | ✅ | Type of service offered |
| `description` | string | ❌ | Business description |
| `service_area` | string | ✅ | Geographic service area |
| `hourly_rate` | float | ❌ | Base hourly rate |

### `GET /providers/`

List service providers with trust scores and exposure-fair ranking.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `service_type` | string | — | Filter by service type |
| `region` | string | — | Filter by region |
| `min_trust_score` | float | — | Minimum trust score threshold |

### `GET /providers/{provider_id}`

Get a single provider with full trust breakdown.

---

## 9. Equipment

### `POST /equipment/`

Register equipment for a service provider.

**Auth Required**: ✅ (provider)

### `GET /equipment/`

List equipment. Filterable by `provider_id` and `equipment_type`.

---

## 10. Labor

### `POST /labor/`

Register labor availability.

**Auth Required**: ✅ (provider)

### `GET /labor/`

List available labor. Supports filtering by `region`, `skill_type`, and `availability_date`.

### `PUT /labor/{labor_id}`

Update labor details or availability.

---

## 11. Service Requests

### `POST /service-requests/`

Create a new service request.

**Auth Required**: ✅ (farmer)

**State Machine**: `created` → `accepted` → `in_progress` → `completed` / `cancelled`

Each transition emits a system event.

### `PUT /service-requests/{request_id}/accept`

Provider accepts a service request.

### `PUT /service-requests/{request_id}/complete`

Mark a service request as completed.

### `PUT /service-requests/{request_id}/cancel`

Cancel a service request (with reason).

---

## 12. Reviews

### `POST /reviews/`

Submit a review for a completed service.

**Auth Required**: ✅ (farmer who created the request)

**Eligibility**: Can only review after service request is `completed`.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service_request_id` | UUID | ✅ | The completed service request |
| `rating` | int | ✅ | 1–5 star rating |
| `comment` | string | ❌ | Review text |
| `complaint_category` | string | ❌ | Category if complaint |

---

## 13. Media

### `POST /media/upload`

Upload a media file (image/video).

**Auth Required**: ✅

**Content-Type**: `multipart/form-data`

Supports two storage backends:
- **Google Cloud Storage** (production): Returns GCS signed URL
- **Local filesystem** (development): Stores in `uploads/` directory

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | Image or video file |
| `crop_instance_id` | UUID | ❌ | Associated crop instance |
| `media_type` | string | ❌ | `image` or `video` |

---

## 14. Offline Sync

### `POST /offline-sync/`

Bulk sync actions captured offline with temporal anomaly detection.

**Auth Required**: ✅

Validates:
- Timestamp ordering consistency
- Detects backdated actions beyond tolerance (MSDD 1.7.1)
- Detects future-dated actions
- Applies server-side timestamp clamping

**Request Body:**

```json
{
  "crop_instance_id": "uuid",
  "actions": [
    {
      "action_type": "irrigation",
      "effective_date": "2026-03-28T10:00:00Z",
      "quantity": 50,
      "unit": "liters",
      "client_timestamp": "2026-03-28T10:05:00Z"
    }
  ]
}
```

---

## 15. ML Models

### `POST /ml/models`

Register a new ML model version.

**Auth Required**: ✅ (admin)

### `GET /ml/models`

List registered ML models with version and status.

### `PUT /ml/models/{model_id}/activate`

Activate a model version (deactivates previous active version of same type).

### `PUT /ml/models/{model_id}/deactivate`

Deactivate a model version.

---

## 16. Crop Rule Templates

### `POST /rules/`

Create a new crop rule template.

**Auth Required**: ✅ (admin)

Templates define the expected behavior for a crop type — growth stages, durations, expected actions, and thresholds.

### `GET /rules/`

List all crop rule templates.

### `GET /rules/{rule_id}`

Get a specific rule template with full stage definitions.

### `PUT /rules/{rule_id}`

Update a rule template. **Creates a new version** (immutable versioning).

### `GET /rules/{rule_id}/versions`

List all versions of a rule template.

---

## 17. Feature Flags

### `GET /features/`

List all feature flags.

**Auth Required**: ✅ (admin)

### `PUT /features/{flag_name}`

Toggle a feature flag.

**Key Flags:**

| Flag | Description |
|------|-------------|
| `ml_enabled` | Global ML kill switch |
| `offline_sync_enabled` | Enable/disable offline sync |
| `media_analysis_enabled` | Enable/disable media analysis |

---

## 18. Admin

### `GET /admin/users`

List all users with pagination. Admin only.

### `PUT /admin/users/{user_id}/deactivate`

Deactivate a user account.

### `PUT /admin/users/{user_id}/activate`

Reactivate a user account.

### `PUT /admin/users/{user_id}/role`

Change a user's role.

### `GET /admin/providers`

List all providers with trust scores and fraud flags.

### `PUT /admin/providers/{provider_id}/flag`

Flag a provider for review.

### `GET /admin/dead-letters`

List events that failed processing (dead letter queue).

### `POST /admin/dead-letters/{event_id}/retry`

Retry a failed event.

---

## 19. System Endpoints

### `GET /health`

Health check endpoint. Returns subsystem-level status.

**No Auth Required**

```json
{
  "status": "healthy",
  "service": "CultivaX",
  "environment": "production",
  "version": "1.0.0",
  "subsystems": {
    "database": "healthy",
    "event_processor": "healthy",
    "ml_service": "healthy"
  },
  "checked_at": "2026-03-30T10:00:00Z"
}
```

### `GET /`

Root endpoint with API info and navigation links.

### `POST /admin/cron/run`

Manually trigger scheduled maintenance tasks (trust decay, health checks, log compression).

### `POST /admin/health-check`

Trigger a full system health check.

### `GET /docs`

Interactive API documentation (Swagger UI).

### `GET /redoc`

Alternative API documentation (ReDoc).

---

## 20. Error Handling

All errors follow a standard format:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request — malformed input |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — insufficient permissions |
| `404` | Not Found — resource doesn't exist |
| `409` | Conflict — duplicate resource |
| `422` | Unprocessable Entity — validation error |
| `429` | Too Many Requests — rate limit exceeded |
| `500` | Internal Server Error |

### Rate Limiting

The API enforces per-IP rate limiting via middleware. Default limits:
- **Standard endpoints**: 100 requests/minute
- **Auth endpoints**: 10 requests/minute
- **Upload endpoints**: 20 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1711800000
```

### Idempotency

For POST requests, include an `Idempotency-Key` header to prevent duplicate processing:

```
Idempotency-Key: <unique-uuid>
```

The middleware caches responses for 24 hours keyed by the idempotency key.

---

## Appendix A: Data Types

| Type | Format | Example |
|------|--------|---------|
| UUID | v4 UUID string | `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` |
| DateTime | ISO 8601 | `"2026-03-30T10:00:00Z"` |
| Date | ISO 8601 date | `"2026-03-30"` |
| Enum (state) | string | `"created"`, `"active"`, `"harvested"`, `"closed"` |
| Enum (role) | string | `"farmer"`, `"provider"`, `"admin"` |

## Appendix B: Event Types

Events emitted by the system for internal processing:

| Event Type | Source | Description |
|------------|--------|-------------|
| `CropCreated` | CTIS | New crop instance registered |
| `ActionLogged` | CTIS | Farmer action recorded |
| `StressComputed` | CTIS | Stress score recalculated |
| `StateTransition` | CTIS | Crop state machine transition |
| `YieldSubmitted` | CTIS | Harvest yield submitted |
| `ServiceRequested` | SOE | New service request |
| `ServiceAccepted` | SOE | Provider accepted request |
| `ServiceCompleted` | SOE | Service completed |
| `ReviewSubmitted` | SOE | Review posted |
| `TrustUpdated` | SOE | Trust score recalculated |
| `MediaUploaded` | Media | File uploaded |
| `AlertCreated` | Notifications | New alert generated |
| `ModelActivated` | ML | ML model version activated |
