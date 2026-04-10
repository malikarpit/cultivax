# CultivaX — API Reference

> **Base URL (local):** `http://localhost:8000`  
> **Base URL (production):** Your Cloud Run service URL  
> **Interactive docs:** `http://localhost:8000/docs` (Swagger UI)  
> **All endpoints are prefixed `/api/v1/`**

---

## Authentication

All protected endpoints require a JWT Bearer token:

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/v1/auth/login`.

**Roles:** `farmer` | `provider` | `admin`

---

## Table of Contents

- [Health](#health)
- [Auth](#auth)
- [Crops](#crops)
- [Actions](#actions)
- [Simulation](#simulation)
- [Yield](#yield)
- [Sync (Offline)](#sync-offline)
- [Recommendations](#recommendations)
- [Alerts](#alerts)
- [Service Providers](#service-providers)
- [Equipment](#equipment)
- [Labor](#labor)
- [Service Requests](#service-requests)
- [Reviews](#reviews)
- [Schemes](#schemes)
- [Weather](#weather)
- [Land Parcels](#land-parcels)
- [Media](#media)
- [ML Models](#ml-models)
- [Rules (Crop Templates)](#rules-crop-templates)
- [Feature Flags](#feature-flags)
- [Analytics](#analytics)
- [Reports](#reports)
- [Search](#search)
- [Disputes](#disputes)
- [Admin](#admin)
- [Account](#account)
- [Consent](#consent)
- [Config](#config)
- [Translations](#translations)

---

## Health

### `GET /api/v1/health`
> **Auth:** None

Returns service health status.

```json
{ "status": "ok", "version": "1.0" }
```

---

## Auth

### `POST /api/v1/auth/register`
> **Auth:** None

Register a new user.

**Request:**
```json
{
  "full_name": "Ramesh Kumar",
  "phone": "+919876543210",
  "password": "SecurePass@123",
  "role": "farmer",
  "region": "Punjab",
  "preferred_language": "hi"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "full_name": "Ramesh Kumar",
  "phone": "+919876543210",
  "role": "farmer",
  "region": "Punjab"
}
```

---

### `POST /api/v1/auth/login`
> **Auth:** None

```json
{ "phone": "+919876543210", "password": "SecurePass@123" }
```

**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### `POST /api/v1/auth/refresh`
> **Auth:** Bearer token

Refresh an access token before expiry.

---

## Crops

### `GET /api/v1/crops/`
> **Auth:** Farmer

List all crops for the authenticated farmer.

**Query params:** `state`, `crop_type`, `region`, `include_archived`, `page`, `limit`, `sort`

**Response `200`:**
```json
{
  "items": [ CropInstance, ... ],
  "total": 12,
  "page": 1,
  "limit": 20
}
```

---

### `POST /api/v1/crops/`
> **Auth:** Farmer

Create a new crop instance. Seasonal window (`Early/Optimal/Late`) is automatically assigned based on sowing date vs regional sowing calendar.

**Request:**
```json
{
  "crop_type": "wheat",
  "variety": "HD-2967",
  "sowing_date": "2026-11-01",
  "region": "Punjab",
  "sub_region": "Ludhiana",
  "land_area_acres": 5.0,
  "rule_template_id": "uuid-optional"
}
```

---

### `GET /api/v1/crops/{id}`
> **Auth:** Farmer (own crop) | Admin

Returns full crop detail including computed state, stress score, risk index, and day number.

---

### `PUT /api/v1/crops/{id}`
> **Auth:** Farmer (own crop)

Update crop metadata (variety, notes). Does **not** allow direct state changes (use action logging).

---

### `PUT /api/v1/crops/{id}/sowing-date`
> **Auth:** Farmer

Update the sowing date. Triggers a full replay to recompute all derived state.

---

### `DELETE /api/v1/crops/{id}`
> **Auth:** Farmer (own crop) | Admin

Soft-delete a crop (sets `is_deleted=True`).

---

### `GET /api/v1/crops/{id}/history`
> **Auth:** Farmer

Returns the full chronological action log for a crop.

---

## Actions

### `POST /api/v1/crops/{id}/actions`
> **Auth:** Farmer

Log a farmer action. Triggers an async replay via the event dispatcher.

**Request:**
```json
{
  "action_type": "irrigation",
  "effective_date": "2026-11-15",
  "category": "timeline_critical",
  "notes": "Applied 40mm irrigation",
  "idempotency_key": "uuid-client-generated"
}
```

**Action types:** `irrigation`, `fertilizer`, `pesticide`, `harvest_prep`, `soil_test`, `observation`, `weeding`, `other`

**Categories:** `timeline_critical` | `operational`

---

## Simulation

### `POST /api/v1/crops/{id}/simulate`
> **Auth:** Farmer

Run a What-If simulation. Does **not** persist any changes.

**Request:**
```json
{
  "hypothetical_action": {
    "action_type": "irrigation",
    "effective_date": "2026-11-20"
  }
}
```

**Response `200`:**
```json
{
  "current": { "stress_score": 0.45, "risk_index": 0.38, "state": "Active" },
  "simulated": { "stress_score": 0.28, "risk_index": 0.22, "state": "Active" },
  "delta": { "stress_change": -0.17, "risk_change": -0.16 }
}
```

---

## Yield

### `POST /api/v1/crops/{id}/yield`
> **Auth:** Farmer

Submit harvest yield. Finalizes the crop lifecycle (state → Harvested).

**Request:**
```json
{
  "reported_yield": 4200,
  "yield_unit": "kg_per_acre",
  "harvest_date": "2027-04-10"
}
```

**Response `200`:**
```json
{
  "reported_yield": 4200,
  "ml_yield_value": 3900,
  "bio_cap_applied": false,
  "verification_score": 0.87,
  "crop_state": "Harvested"
}
```

> `reported_yield` is always returned exactly as submitted (Farmer Truth). `ml_yield_value` may be capped at biological limit.

---

## Sync (Offline)

### `POST /api/v1/sync/`
> **Auth:** Farmer

Submit a batch of actions logged while offline. Temporal anomaly detection runs on the batch.

**Request:**
```json
{
  "actions": [
    {
      "crop_id": "uuid",
      "action_type": "irrigation",
      "effective_date": "2026-11-15",
      "idempotency_key": "uuid",
      "local_seq_no": 1
    }
  ]
}
```

**Response `200`:**
```json
{
  "accepted": 3,
  "rejected": 0,
  "anomaly_flagged": false
}
```

---

## Recommendations

### `GET /api/v1/crops/{id}/recommendations`
> **Auth:** Farmer

Returns today's top 3 prioritized recommendations for a crop.

**Response `200`:**
```json
{
  "items": [
    {
      "type": "irrigation",
      "priority_rank": 1,
      "message": "Apply 40mm irrigation within 2 days",
      "basis": "stress_score=0.7, days_until_stage_end=3",
      "valid_until": "2026-11-18"
    }
  ]
}
```

---

## Alerts

### `GET /api/v1/alerts/`
> **Auth:** Farmer

Returns active alerts for the authenticated farmer.

**Query params:** `is_acknowledged`, `alert_type`, `severity`, `page`

---

### `PUT /api/v1/alerts/{id}/acknowledge`
> **Auth:** Farmer

Mark an alert as acknowledged.

---

## Service Providers

### `GET /api/v1/providers/`
> **Auth:** Any authenticated

Browse verified service providers.

**Query params:** `region`, `service_type`, `crop_specialization`, `page`, `limit`

---

### `POST /api/v1/providers/`
> **Auth:** Provider

Register as a service provider. Status begins as `Pending` until admin verifies.

---

### `GET /api/v1/providers/{id}`
> **Auth:** Any authenticated

Provider detail including trust score breakdown.

---

## Equipment

### `GET /api/v1/equipment/`
### `POST /api/v1/equipment/`
### `PUT /api/v1/equipment/{id}`
### `DELETE /api/v1/equipment/{id}`
> **Auth:** Provider (own) | Admin

CRUD for equipment listings.

---

## Labor

### `GET /api/v1/labor/`
### `POST /api/v1/labor/`
### `PUT /api/v1/labor/{id}`
### `DELETE /api/v1/labor/{id}`
> **Auth:** Provider (own) | Admin

CRUD for labor listings.

---

## Service Requests

### `GET /api/v1/service-requests/`
> **Auth:** Farmer (own) | Provider (received) | Admin (all)

**Query params:** `status`, `provider_id`, `crop_id`, `page`

---

### `POST /api/v1/service-requests/`
> **Auth:** Farmer

Create a service request.

```json
{
  "provider_id": "uuid",
  "service_type": "equipment_rental",
  "crop_instance_id": "uuid",
  "preferred_date": "2026-12-01",
  "notes": "Need tractor for wheat harvesting"
}
```

---

### `PUT /api/v1/service-requests/{id}/accept`
> **Auth:** Provider

Accept an incoming request.

---

### `PUT /api/v1/service-requests/{id}/complete`
> **Auth:** Provider | Admin

Mark a request as completed.

---

### `PUT /api/v1/service-requests/{id}/cancel`
> **Auth:** Farmer | Admin

Cancel a request.

---

## Reviews

### `POST /api/v1/reviews/`
> **Auth:** Farmer

Submit a review for a **completed** service request. Eligibility verified server-side. Triggers trust score recalculation, fraud detection, and escalation evaluation.

```json
{
  "service_request_id": "uuid",
  "rating": 4.5,
  "comment": "Very professional and on time",
  "complaint_category": null
}
```

> Reviews are **immutable** once submitted — no soft delete, no edit.

---

## Schemes

### `GET /api/v1/schemes/`
> **Auth:** Farmer | Admin

Browse official government agricultural schemes.

**Query params:** `category`, `region`, `search`, `page`

**Categories:** `subsidy`, `insurance`, `advisory`, `loan`

---

### `POST /api/v1/schemes/{id}/redirect`
> **Auth:** Farmer

Log a scheme portal visit (creates a `SchemeRedirectLog` row).

**Response:** Returns the scheme's portal URL to redirect to.

---

## Weather

### `GET /api/v1/weather/`
> **Auth:** Farmer | Admin

**Query params:** `region` (required), `days` (1-7)

Returns current weather and forecast. Primary source: [Open-Meteo](https://open-meteo.com/) (free, no key). Fallback: OpenWeatherMap (requires `OPENWEATHER_API_KEY`).

---

## Land Parcels

### `GET /api/v1/land-parcels/`
### `POST /api/v1/land-parcels/`
### `GET /api/v1/land-parcels/{id}`
### `PUT /api/v1/land-parcels/{id}`
### `DELETE /api/v1/land-parcels/{id}`
> **Auth:** Farmer (own) | Admin

Land parcel (field) management. Parcels can be linked to crop instances.

---

## Media

### `POST /api/v1/media/upload`
> **Auth:** Farmer

Upload a photo/video associated with a crop.

**Content-Type:** `multipart/form-data`

**Form fields:** `file` (binary), `crop_instance_id` (UUID)

**Response `201`:**
```json
{
  "media_id": "uuid",
  "analysis_status": "Pending",
  "scheduled_deletion_at": "2026-08-10T00:00:00Z"
}
```

> Files are retained for 3 months (`scheduled_deletion_at`). Analysis status lifecycle: `Pending → Processing → Analyzed | Failed`.

---

## ML Models

### `GET /api/v1/ml/models`
> **Auth:** Admin

List all registered ML model versions.

---

### `POST /api/v1/ml/models`
> **Auth:** Admin

Register a new model version.

```json
{
  "name": "risk-predictor-v2",
  "version": "2.0",
  "file_path": "/models/risk_v2.pkl",
  "training_dataset_reference": "dataset-2026-q1"
}
```

---

### `PUT /api/v1/ml/models/{id}/activate`
> **Auth:** Admin

Activate a model version. Deactivates the current active model.

---

### `GET /api/v1/ml/inference-audits`
> **Auth:** Admin

Query inference audit trail.

**Query params:** `model_version`, `crop_instance_id`, `since`, `page`

---

## Rules (Crop Templates)

### `GET /api/v1/rules/`
> **Auth:** Any authenticated

List all crop rule templates.

---

### `POST /api/v1/rules/`
> **Auth:** Admin

Create a new crop rule template (stage definitions, drift limits, risk params).

---

### `PUT /api/v1/rules/{id}`
> **Auth:** Admin

Update a rule template (creates a new version).

---

### `POST /api/v1/rules/{id}/validate`
> **Auth:** Admin

Validate a draft rule against business constraints.

---

### `POST /api/v1/rules/{id}/approve`
> **Auth:** Admin

Approve and activate a rule template. New crops will use this template. **Existing crops remain pinned to their original template** (prospective-only).

---

## Feature Flags

### `GET /api/v1/features/`
> **Auth:** Admin

List all feature flags and their current state.

---

### `PUT /api/v1/features/{name}`
> **Auth:** Admin

Toggle a feature flag.

**Flags:** `ml_enabled`, `clustering_enabled`, `risk_prediction_enabled`, `behavioral_adaptation_enabled`, `soe_enabled`

---

## Analytics

### `GET /api/v1/analytics/`
> **Auth:** Admin

Platform-wide analytics: total users, active crops, service requests, alerts, average trust scores, crop distribution by state/type.

---

## Reports

### `GET /api/v1/reports/`
> **Auth:** Admin

Generate downloadable reports (crop summaries, SOE performance, alert history).

---

## Search

### `GET /api/v1/search/`
> **Auth:** Any authenticated

Unified search across crops, providers, schemes, and actions.

**Query params:** `q` (search term), `type` (optional: `crop|provider|scheme|action`)

---

## Disputes

### `GET /api/v1/disputes/`
### `POST /api/v1/disputes/`
### `GET /api/v1/disputes/{id}`
### `PUT /api/v1/disputes/{id}`
> **Auth:** Farmer (own) | Admin (all)

Dispute case management for service request complaints.

---

## Admin

### `GET /api/v1/admin/users`
> **Auth:** Admin

List all users with filtering.

**Query params:** `role`, `is_active`, `region`, `page`

---

### `PUT /api/v1/admin/users/{id}/role`
> **Auth:** Admin

Change a user's role.

---

### `DELETE /api/v1/admin/users/{id}`
> **Auth:** Admin

Soft-delete a user (sets `is_deleted=True`).

---

### `PUT /api/v1/admin/providers/{id}/verify`
### `PUT /api/v1/admin/providers/{id}/suspend`
> **Auth:** Admin

Verify or suspend a provider. Suspended providers are hidden from marketplace.

---

### `GET /api/v1/admin/audit`
> **Auth:** Admin

View admin audit log (who changed what and when).

---

### `GET /api/v1/admin/dead-letters`
> **Auth:** Admin

List events in the Dead Letter Queue.

---

### `POST /api/v1/admin/dead-letters/{id}/retry`
> **Auth:** Admin

Retry a single dead-letter event. Resets `status='Created'`, `retry_count=0`.

---

### `POST /api/v1/admin/dead-letters/bulk-retry`
> **Auth:** Admin

Retry multiple dead-letter events.

```json
{ "event_type": "ctis.action_logged", "limit": 50 }
```

---

### `DELETE /api/v1/admin/dead-letters/{id}`
> **Auth:** Admin

Permanently discard a dead-letter event.

---

### `GET /api/v1/admin/health`
> **Auth:** Admin

System health report: DB connectivity, event queue depth, avg processing latency, dead letter count.

---

## Account

### `GET /api/v1/account/me`
> **Auth:** Any authenticated

Get own profile.

---

### `PUT /api/v1/account/me`
> **Auth:** Any authenticated

Update own profile (name, region, preferred language, accessibility settings).

---

### `PUT /api/v1/account/me/password`
> **Auth:** Any authenticated

Change password.

---

## Consent

### `GET /api/v1/consent/`
### `POST /api/v1/consent/`
> **Auth:** Farmer

Manage data consent preferences (GDPR-style consent logging).

---

## Config

### `GET /api/v1/config/`
> **Auth:** Any authenticated

Fetch regional config values (default drift limits, sowing windows, etc.).

---

## Translations

### `GET /api/v1/translations/{language_code}`
> **Auth:** None

Fetch server-side translation strings for a language. (Frontend primarily uses inline i18n dictionary; this endpoint supports future dynamic translation loading.)

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Authenticated but insufficient role |
| `NOT_FOUND` | 404 | Resource does not exist |
| `INVALID_STATE_TRANSITION` | 400 | Crop state machine violation |
| `CHRONOLOGICAL_VIOLATION` | 400 | Action date precedes previous action |
| `DUPLICATE_REQUEST` | 409 | Idempotency key collision |
| `REPLAY_FAILURE` | 500 | Crop entered RecoveryRequired state |
| `RATE_LIMITED` | 429 | Too many requests |

---

## Rate Limiting

| Endpoint Group | Limit |
|----------------|-------|
| Auth endpoints | 10 req/min per IP |
| Crop mutations | 60 req/min per user |
| Offline sync | 10 req/min per user |
| Admin endpoints | 120 req/min per user |
| General reads | 200 req/min per user |
