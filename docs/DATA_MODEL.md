# CultivaX — Data Model Reference

> Complete schema reference for all 35+ database tables.

---

## Common Fields (All Tables)

All major tables inherit from the base mixin and include:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` PK | Auto-generated UUID v4 |
| `created_at` | `DateTime` | Row creation timestamp (UTC) |
| `updated_at` | `DateTime` | Last update timestamp (UTC, auto-updated) |
| `is_deleted` | `Boolean` | Soft delete flag (default: `False`) |
| `deleted_at` | `DateTime` nullable | When soft-deleted |
| `deleted_by` | `UUID` nullable | Who soft-deleted it (references `users.id`) |

> **Soft Delete Policy (MSDD 5.10):** No hard deletes on any major table. Admin "delete" operations set `is_deleted=True`. Queries always include `WHERE is_deleted = FALSE`.

---

## Users & Auth

### `users`
> Authentication, roles, and farmer profiles.

| Column | Type | Notes |
|--------|------|-------|
| `phone` | VARCHAR(20) UNIQUE | Primary identifier |
| `full_name` | VARCHAR(255) | |
| `email` | VARCHAR(255) nullable | Optional |
| `role` | ENUM(`farmer`, `provider`, `admin`) | |
| `password_hash` | TEXT | bcrypt hash |
| `region` | VARCHAR(100) | Indian state |
| `preferred_language` | VARCHAR(10) | `en`, `hi`, `ta`, `te`, `mr` |
| `accessibility_settings` | JSONB | `{largeText, highContrast, theme, pinnedSidebar}` |
| `is_active` | Boolean | Account active flag |
| `is_onboarded` | Boolean | Has completed onboarding tour |

### `otp_codes`
> Phone OTP verification codes.

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | UUID FK → users | |
| `code` | VARCHAR(10) | Hashed OTP |
| `expires_at` | DateTime | |
| `is_used` | Boolean | |

### `active_sessions`
> Tracks active JWT sessions for invalidation.

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | UUID FK → users | |
| `token_hash` | TEXT | SHA256 of JWT |
| `expires_at` | DateTime | |
| `device_info` | JSONB | User-Agent, IP |

---

## CTIS — Crop Timeline Intelligence System

### `crop_instances`
> Central CTIS table. One row per planted crop.

| Column | Type | Notes |
|--------|------|-------|
| `farmer_id` | UUID FK → users | |
| `crop_type` | VARCHAR(100) | `wheat`, `rice`, `cotton`, etc. |
| `variety` | VARCHAR(255) nullable | |
| `sowing_date` | DATE | Immutable after first replay |
| `region` | VARCHAR(100) | |
| `sub_region` | VARCHAR(255) nullable | |
| `land_area_acres` | DECIMAL nullable | |
| `state` | VARCHAR(50) | `Created/Active/Delayed/AtRisk/ReadyToHarvest/Harvested/Closed/Archived/RecoveryRequired` |
| `stage` | VARCHAR(100) | Current growth stage (e.g., `Germination`) |
| `stress_score` | DECIMAL(5,4) | 0.0–1.0 |
| `risk_index` | DECIMAL(5,4) | 0.0–1.0 |
| `current_day_number` | INTEGER | Days since sowing |
| `stage_offset_days` | DECIMAL(5,2) | Drift from ideal timeline |
| `max_allowed_drift` | INTEGER | Per-stage drift cap (from rule template) |
| `seasonal_window_category` | VARCHAR(20) | `Early/Optimal/Late` — frozen at creation |
| `rule_template_id` | UUID FK → crop_rule_templates nullable | Pinned at creation |
| `rule_version_applied` | VARCHAR(50) | Version string of pinned template |

### `action_logs`
> Immutable record of every farmer action on a crop.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `farmer_id` | UUID FK → users | |
| `action_type` | VARCHAR(100) | `irrigation`, `fertilizer`, `pesticide`, `harvest_prep`, `soil_test`, `observation`, `weeding`, `other` |
| `effective_date` | DATE | Must be ≥ sowing_date, chronologically after previous action |
| `category` | VARCHAR(50) | `timeline_critical` / `operational` |
| `notes` | TEXT nullable | |
| `idempotency_key` | VARCHAR(255) UNIQUE nullable | Client-supplied dedup key |
| `is_offline_sync` | Boolean | Whether synced from offline queue |
| `local_seq_no` | INTEGER nullable | Sequence number from offline device |

> **Immutability:** Action logs are append-only. The replay engine processes them in chronological order.

### `crop_instance_snapshots`
> Periodic checkpoints for fast replay recovery.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `snapshot_state` | JSONB | Full serialized CropInstance state |
| `action_log_count_at_snapshot` | INTEGER | How many actions were processed to produce this snapshot |
| `stress_score` | DECIMAL | At snapshot time |
| `stage` | VARCHAR | At snapshot time |

### `deviation_profiles`
> Per-crop deviation tracking across lifecycle.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances UNIQUE | One profile per crop |
| `consecutive_deviation_count` | INTEGER | |
| `deviation_trend_slope` | DECIMAL | Positive = worsening |
| `recurring_pattern_flag` | Boolean | True if farmer has consistent timing pattern |
| `last_deviation_date` | DATE | |

### `yield_records`
> Harvest yield submissions.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `farmer_id` | UUID FK → users | |
| `reported_yield` | DECIMAL | **Farmer Truth** — immutable as submitted |
| `yield_unit` | VARCHAR | `kg_per_acre`, `quintal_per_acre`, `ton_per_hectare` |
| `ml_yield_value` | DECIMAL | **ML Truth** — capped at biological limit |
| `bio_cap_applied` | Boolean | Whether biological limit was enforced |
| `verification_score` | DECIMAL(5,4) | `YieldVerificationScore` 0-1 |
| `harvest_date` | DATE | |

### `crop_rule_templates`
> Admin-managed crop lifecycle rule templates.

| Column | Type | Notes |
|--------|------|-------|
| `name` | VARCHAR(255) | |
| `crop_type` | VARCHAR(100) | |
| `version_id` | VARCHAR(50) | e.g., `v1.2` |
| `status` | VARCHAR(50) | `draft/validated/active/deprecated` |
| `effective_from_date` | DATE | |
| `stage_definitions` | JSONB | Stages, durations, expected actions |
| `drift_limits` | JSONB | Max offset per stage |
| `risk_parameters` | JSONB | Risk weights per signal |
| `irrigation_windows` | JSONB | |
| `fertilizer_windows` | JSONB | |
| `harvest_windows` | JSONB | |

### `regional_sowing_calendars`
> Optimal sowing dates by crop type and region.

| Column | Type | Notes |
|--------|------|-------|
| `crop_type` | VARCHAR(100) | |
| `region` | VARCHAR(100) | |
| `optimal_start` | DATE | |
| `optimal_end` | DATE | |
| `version_id` | VARCHAR(50) | |

### `regional_clusters`
> Aggregated yield and delay statistics by region/crop/season.

| Column | Type | Notes |
|--------|------|-------|
| `crop_type` | VARCHAR(100) | |
| `region` | VARCHAR(100) | |
| `season` | VARCHAR(50) | `kharif/rabi/zaid` |
| `avg_delay` | DECIMAL | Running average delay days |
| `avg_yield` | DECIMAL | Running average yield |
| `sample_size` | INTEGER | Number of yield records contributing |
| `std_dev_yield` | DECIMAL | Standard deviation |
| `confidence_interval` | DECIMAL | 95% CI |
| `last_updated_from_count` | INTEGER | `sample_size` at last update |

> **Prospective-only updates.** Regional cluster data is updated forward from new yield submissions only. Historical values are never rewritten.

### `stress_history`
> Time-series stress score records per crop.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `stress_score` | DECIMAL | |
| `stage` | VARCHAR | At time of record |
| `computed_at` | DateTime | |

---

## SOE — Service Orchestration Ecosystem

### `service_providers`
> Registered service providers (farmers who also offer services).

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | UUID FK → users | |
| `business_name` | VARCHAR(255) | |
| `service_types` | JSONB | `["equipment_rental", "labor", "spraying"]` |
| `crop_specializations` | JSONB | Which crop types they specialize in |
| `region` | VARCHAR(100) | |
| `verification_status` | VARCHAR(50) | `Pending/Verified/Suspended/Rejected` |
| `trust_score` | DECIMAL(5,4) | Computed by TrustEngine |
| `total_requests` | INTEGER | |
| `completed_requests` | INTEGER | |
| `complaint_count` | INTEGER | |
| `avg_rating` | DECIMAL(3,2) | |
| `last_active_at` | DateTime | Used for temporal trust decay |
| `is_flagged` | Boolean | Fraud detection flag |

### `equipment`
> Equipment listings by providers.

| Column | Type | Notes |
|--------|------|-------|
| `provider_id` | UUID FK → service_providers | |
| `equipment_type` | VARCHAR(100) | |
| `description` | TEXT | |
| `hourly_rate` | DECIMAL | |
| `availability` | VARCHAR(50) | `available/unavailable/rented` |
| `region` | VARCHAR(100) | |
| `is_flagged` | Boolean | |

### `labor`
> Labor listings by providers.

| Column | Type | Notes |
|--------|------|-------|
| `provider_id` | UUID FK → service_providers | |
| `labor_type` | VARCHAR(100) | |
| `available_units` | INTEGER | Number of workers |
| `daily_rate` | DECIMAL | |
| `region` | VARCHAR(100) | |
| `is_flagged` | Boolean | |

### `service_requests`
> Service requests from farmers to providers.

| Column | Type | Notes |
|--------|------|-------|
| `farmer_id` | UUID FK → users | |
| `provider_id` | UUID FK → service_providers | |
| `crop_instance_id` | UUID FK → crop_instances nullable | |
| `service_type` | VARCHAR(100) | |
| `status` | VARCHAR(50) | `Created/Accepted/InProgress/Completed/Rejected/Cancelled` |
| `preferred_date` | DATE | |
| `completed_at` | DateTime nullable | |
| `notes` | TEXT nullable | |
| `provider_acknowledged_at` | DateTime nullable | |

### `service_request_events`
> Immutable audit trail of every service request state transition.

| Column | Type | Notes |
|--------|------|-------|
| `request_id` | UUID FK → service_requests | |
| `event_type` | VARCHAR(100) | `created/accepted/completed/cancelled/review_submitted` |
| `previous_state` | VARCHAR(50) | |
| `new_state` | VARCHAR(50) | |
| `actor_id` | UUID FK → users | |
| `actor_role` | VARCHAR(50) | `farmer/provider/system/admin` |
| `notes` | TEXT nullable | |

### `service_reviews`
> Reviews of completed service requests. Immutable.

| Column | Type | Notes |
|--------|------|-------|
| `service_request_id` | UUID FK → service_requests UNIQUE | One review per request |
| `reviewer_id` | UUID FK → users | |
| `provider_id` | UUID FK → service_providers | |
| `rating` | DECIMAL(3,2) | 0.0–5.0 |
| `comment` | TEXT nullable | |
| `complaint_category` | VARCHAR(100) nullable | `late_delivery/poor_quality/no_show/other` |

> **Immutability:** Reviews have `is_deleted` field but are never soft-deleted through normal flows. Reviews are factored into trust scores permanently.

### `provider_availability`
> Provider availability calendar.

| Column | Type | Notes |
|--------|------|-------|
| `provider_id` | UUID FK → service_providers | |
| `available_date` | DATE | |
| `is_available` | Boolean | |
| `reason` | TEXT nullable | |

---

## ML & Analytics

### `ml_models`
> ML model version registry.

| Column | Type | Notes |
|--------|------|-------|
| `name` | VARCHAR(255) | |
| `version` | VARCHAR(50) | e.g., `2.0` |
| `status` | VARCHAR(50) | `pending/active/deactivated` |
| `file_path` | TEXT nullable | Path to model artifact (`.pkl` etc.) |
| `evaluation_metrics` | JSONB | `{accuracy, f1, auc_roc}` |
| `training_dataset_reference` | VARCHAR(255) | Dataset identifier |

### `ml_training_audit`
> Audit trail of model training runs.

| Column | Type | Notes |
|--------|------|-------|
| `model_id` | UUID FK → ml_models | |
| `dataset_source` | TEXT | |
| `date_range` | JSONB | `{from, to}` |
| `feature_schema` | JSONB | Feature column definitions |
| `preprocessing_version` | VARCHAR(50) | Feature lineage tracking |
| `training_metrics` | JSONB | |

### `ml_inference_audit`
> Every ML prediction call is logged here.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID | |
| `model_id` | UUID FK → ml_models nullable | Null if rule-based fallback |
| `model_version` | VARCHAR(50) | |
| `inference_source` | VARCHAR(50) | `registry_ml_inference` / `rule_based_fallback` |
| `features` | JSONB | Input features snapshot |
| `output` | JSONB | `{risk_probability, confidence_score, data_sufficiency_index}` |

### `media_files`
> Uploaded photos/videos associated with crops.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `uploader_id` | UUID FK → users | |
| `file_path` | TEXT | GCS path or local path |
| `file_type` | VARCHAR(50) | `image/jpeg`, `video/mp4` |
| `file_size_bytes` | BIGINT | |
| `analysis_status` | VARCHAR(50) | `Pending/Processing/Analyzed/Failed` |
| `analysis_result` | JSONB nullable | CNN/YOLO output |
| `scheduled_deletion_at` | DateTime | 3 months after upload (MSDD 4.6) |

### `pest_alert_history`
> Pest detection events from media analysis.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `pest_type` | VARCHAR(100) | |
| `alert_level` | VARCHAR(50) | `low/medium/high/critical` |
| `detected_by` | VARCHAR(50) | `cnn_inference/manual` |
| `confidence` | DECIMAL(5,4) | Model confidence |

---

## Notifications

### `alerts`
> System-generated alerts for farmers.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `farmer_id` | UUID FK → users | |
| `alert_type` | VARCHAR(50) | `weather_alert/stress_alert/pest_alert/action_reminder/market_alert/harvest_approaching` |
| `severity` | VARCHAR(20) | `low/medium/high/critical` |
| `message` | TEXT | Localized message |
| `message_key` | VARCHAR(255) | i18n lookup key |
| `is_acknowledged` | Boolean | |
| `acknowledged_at` | DateTime nullable | |

> **Throttling:** Max 3 alerts per crop per 24 hours, enforced in `AlertService`.

### `recommendations`
> Daily prioritized action suggestions per crop.

| Column | Type | Notes |
|--------|------|-------|
| `crop_instance_id` | UUID FK → crop_instances | |
| `farmer_id` | UUID FK → users | |
| `type` | VARCHAR(100) | `irrigation/fertilizer/harvest_prep/general` |
| `priority_rank` | INTEGER | 1 = highest priority |
| `message_key` | VARCHAR(255) | i18n key |
| `message_parameters` | JSONB | Dynamic values for the message |
| `basis` | TEXT | Why this was recommended |
| `valid_from` | DateTime | |
| `valid_until` | DateTime | |
| `status` | VARCHAR(50) | `active/dismissed/acted_upon` |

---

## Event System

### `event_log`
> DB-backed event bus. The backbone of all async processing.

| Column | Type | Notes |
|--------|------|-------|
| `event_type` | VARCHAR(255) | e.g., `ctis.action_logged` |
| `entity_type` | VARCHAR(100) | e.g., `CropInstance` |
| `entity_id` | UUID | Primary key of the entity |
| `payload` | JSONB | Event-specific data |
| `status` | VARCHAR(50) | `Created/Processing/Processed/DeadLetter` |
| `retry_count` | INTEGER | Number of processing attempts |
| `max_retries` | INTEGER | Default: 3 |
| `next_retry_at` | DateTime nullable | Exponential backoff |
| `error_message` | TEXT nullable | Last failure message |
| `partition_key` | VARCHAR(255) | For FIFO ordering (typically `crop_instance_id`) |
| `event_hash` | VARCHAR(64) UNIQUE | SHA256 for idempotency |
| `processed_at` | DateTime nullable | |

---

## Admin & Governance

### `admin_audit_log`
> Immutable record of all admin actions.

| Column | Type | Notes |
|--------|------|-------|
| `admin_id` | UUID FK → users | |
| `action` | VARCHAR(255) | e.g., `user.role_changed` |
| `target_id` | UUID nullable | Entity affected |
| `target_type` | VARCHAR(100) | |
| `old_value` | JSONB | |
| `new_value` | JSONB | |
| `ip_address` | VARCHAR(45) | |

### `feature_flags`
> Admin-controlled feature toggles.

| Column | Type | Notes |
|--------|------|-------|
| `name` | VARCHAR(255) UNIQUE | e.g., `ml_enabled` |
| `is_enabled` | Boolean | |
| `updated_by` | UUID FK → users | |
| `notes` | TEXT | |

### `abuse_flags`
> Flagged suspicious activity from offline sync temporal anomaly detection.

| Column | Type | Notes |
|--------|------|-------|
| `farmer_id` | UUID FK → users | |
| `anomaly_type` | VARCHAR(100) | `excessive_backdate/future_action/batch_anomaly/seq_reset` |
| `anomaly_score` | DECIMAL(5,4) | |
| `payload_summary` | JSONB | Offending action details |
| `reviewed_by` | UUID nullable | Admin who reviewed |
| `resolution` | VARCHAR(100) nullable | `dismissed/warned/suspended` |

---

## Government Schemes

### `official_schemes`
> Government agricultural scheme listings.

| Column | Type | Notes |
|--------|------|-------|
| `name` | VARCHAR(500) | |
| `description` | TEXT | |
| `category` | VARCHAR(100) | `subsidy/insurance/advisory/loan` |
| `region` | VARCHAR(100) | State or `national` |
| `portal_url` | TEXT | Government portal link |
| `is_active` | Boolean | |
| `valid_until` | DATE nullable | Scheme expiry |
| `benefit_amount` | TEXT nullable | Textual description of benefit |

### `scheme_redirect_logs`
> Audit trail of scheme portal visits.

| Column | Type | Notes |
|--------|------|-------|
| `scheme_id` | UUID FK → official_schemes | |
| `farmer_id` | UUID FK → users | |
| `redirected_at` | DateTime | |

---

## Communications

### `sms_delivery_log`
> Record of all SMS messages sent.

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | UUID FK → users | |
| `phone` | VARCHAR(20) | |
| `message_type` | VARCHAR(50) | `otp/alert/notification` |
| `provider` | VARCHAR(50) | `twilio/stub` |
| `status` | VARCHAR(50) | `sent/failed/delivered` |
| `provider_message_id` | VARCHAR(255) nullable | Twilio SID |
| `error_message` | TEXT nullable | |

### `whatsapp_sessions`
> WhatsApp bot conversation sessions (future feature).

---

## Disputes & Governance

### `dispute_cases`
> Formal dispute cases between farmers and providers.

| Column | Type | Notes |
|--------|------|-------|
| `complainant_id` | UUID FK → users | |
| `respondent_id` | UUID FK → users | |
| `service_request_id` | UUID FK nullable | Related request |
| `status` | VARCHAR(50) | `open/under_review/resolved/closed` |
| `description` | TEXT | |
| `resolution` | TEXT nullable | Admin resolution notes |
| `resolved_by` | UUID FK nullable | |
| `resolved_at` | DateTime nullable | |

### `user_consents`
> GDPR-style data consent records.

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | UUID FK → users | |
| `consent_type` | VARCHAR(100) | `data_processing/marketing/analytics` |
| `is_granted` | Boolean | |
| `granted_at` | DateTime nullable | |
| `withdrawn_at` | DateTime nullable | |
| `version` | VARCHAR(50) | Consent form version |

### `user_reports`
> Reports filed by users about other users or providers.

| Column | Type | Notes |
|--------|------|-------|
| `reporter_id` | UUID FK → users | |
| `reported_user_id` | UUID FK → users | |
| `report_type` | VARCHAR(100) | |
| `description` | TEXT | |
| `status` | VARCHAR(50) | `pending/reviewed/dismissed/actioned` |

---

## Configuration

### `region_configs`
> Per-region configuration overrides.

| Column | Type | Notes |
|--------|------|-------|
| `region` | VARCHAR(100) UNIQUE | |
| `default_drift_limit_days` | INTEGER | |
| `weather_provider` | VARCHAR(50) | `openmeteo/openweathermap` |
| `sms_enabled` | Boolean | |
| `config_overrides` | JSONB | Any other per-region settings |

---

## Entity Relationship Overview

```
users ──────────────────────────────────────────────┐
  │                                                  │
  ├─► crop_instances ──► action_logs                 │
  │         │                                        │
  │         ├─► crop_instance_snapshots              │
  │         ├─► deviation_profiles                   │
  │         ├─► yield_records                        │
  │         ├─► stress_history                       │
  │         ├─► alerts                               │
  │         ├─► recommendations                      │
  │         ├─► media_files ──► pest_alert_history   │
  │         └─► ml_inference_audit                   │
  │                                                  │
  ├─► service_providers ─────────────────────────────┤
  │         │                                        │
  │         ├─► equipment                            │
  │         ├─► labor                                │
  │         └─► provider_availability                │
  │                                                  │
  ├─► service_requests ──────────────────────────────┤
  │         │                                        │
  │         ├─► service_request_events               │
  │         └─► service_reviews                      │
  │                                                  │
  ├─► dispute_cases                                  │
  ├─► user_consents                                  │
  ├─► user_reports                                   │
  ├─► abuse_flags                                    │
  └─► sms_delivery_log                               │
                                                     │
event_log (all modules publish here) ◄───────────────┘
admin_audit_log
feature_flags
official_schemes ──► scheme_redirect_logs
regional_clusters
regional_sowing_calendars
crop_rule_templates
ml_models ──► ml_training_audit
region_configs
```
