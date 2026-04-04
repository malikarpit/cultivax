# Secrets Rotation & Management Runbook

## Overview
CultivaX uses Google Cloud Secret Manager to store production secrets, which are securely injected into Cloud Run environments at runtime rather than living in code.

## 1. Secret Manifest
The production environment requires the following core keys:
*   `JWT_SECRET_KEY`
*   `DB_PASSWORD` 

## 2. Zero-Downtime Secret Rotation Process
To rotate passwords without disrupting live farmer endpoints, follow this blue-green rollout:

### Step 1: Add New Secret Version in Secret Manager
1. Navigate to **Google Cloud Console > Secret Manager**.
2. Select the targeted secret (e.g., `cultivax-jwt-secret`).
3. Click **Add New Version** and input the newly generated cryptographically secure string.

### Step 2: Establish Backend Transition Overlay
If you are rotating `JWT_SECRET_KEY`:
You must modify `backend/app/core/config.py` temporarily to validate against BOTH the old key and the new key, otherwise users with active tokens will experience instant 401 Unauthorized crashes.
*Add a `FALLBACK_JWT_SECRET` parsing logic. Deploy this code version before deleting old keys.*

### Step 3: Shift Production Variables
Update Cloud Run to point strictly to the `latest` version of your Secret mapping via `gcloud`:
```bash
gcloud run services update cultivax-backend \
  --set-secrets=SECRET_KEY=cultivax-jwt-secret:latest \
  --region=asia-south1
```
*Wait 20-40 seconds for traffic to re-route to the new Cloud Run execution container instance.*

### Step 4: Verify System Integrity
Check logs and monitor `/api/v1/health`. If errors spike, issue an immediate rollback via:
```bash
gcloud run revisions list --service cultivax-backend
gcloud run services update-traffic cultivax-backend --to-revisions=<PREV_ID>=100
```

### Step 5: Deprecate Key
Once existing JWTs expire (default 60 minutes), remove `FALLBACK_JWT` from codebase and return to Secret Manager to **Disable** or **Destroy** the older Key version permanently.
