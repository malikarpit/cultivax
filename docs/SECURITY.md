# Security Policy

CultivaX is built for agricultural operations handling sensitive PII, geospatial data, and commercial service contracts. Security is considered a Tier-1 requirement.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v1.0.x  | :white_check_mark: |
| < v1.0  | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within CultivaX, please report it immediately rather than opening a public issue.
**Contact Email**: security@cultivax.local

*Do not disclose vulnerabilities on GitHub discussions, Slack, or Discord prior to triage.* We attempt to acknowledge valid vulnerability reports within 24 hours.

## Architectural Security Vectors Mitigated
CultivaX intrinsically defends against several enterprise-grade attack vectors:

### 1. Replay Attacks & Idempotency
Destructive operations (like harvesting a crop) require a strict `Idempotency-Key` implementation coupled with chronologically gated `event_log` checkpoints. An attacker capturing a generic "close_crop" valid JWT token request cannot maliciously replay it repeatedly to mutate yield scores without supplying uniquely validated tokens.

### 2. Authorization Privilege Escalation (Insecure Direct Object Reference)
Every primary controller endpoint operating under `/api/v1/crops/{crop_id}` explicitly bridges the URL path ID parameter into a verified ownership query against `current_user.id`. Modifying a crop ID in an API client request will properly yield a 403 Forbidden or 404 Not Found rather than executing the destructive event.

### 3. ML Heuristic Stubs & Data Poisoning
Until proprietary PyTorch instances are integrated, CultivaX is shielded via Rule-Based bounded calculations in the `risk_predictor.py`. Bounded validation checks reject physically impossible environmental data overrides preventing data pipeline poisoning attempts.

### 4. Bounded Market Trust
The SOE limits malicious provider rating-manipulation via temporal decay algorithms and strict max-cap limiters on exposure visibility. Providers attempting review farming are automatically segmented by the Fraud Engine.
