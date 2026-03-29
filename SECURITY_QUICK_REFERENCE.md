# Security Quick Reference Guide

## For Developers

### 1. Using Secure Authentication

**Backend:**
```python
from app.security.secure_auth import set_auth_cookies, clear_auth_cookies

# On login - set HTTPOnly cookies
@router.post("/login")
async def login(response: Response):
    access_token = create_access_token({"sub": user_id, "role": role})
    refresh_token = create_refresh_token({"sub": user_id})

    # Set secure cookies
    set_auth_cookies(response, access_token, refresh_token)

    return {"success": True}

# On logout - clear cookies
@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"success": True}
```

**Frontend (Future Migration):**
```typescript
// No need to manually handle tokens - cookies are automatic!

// Login
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include', // Important: send cookies
  body: JSON.stringify({ phone, password })
});

// Authenticated requests
const data = await fetch('/api/v1/crops/', {
  credentials: 'include' // Cookies sent automatically
});

// Logout
await fetch('/api/v1/auth/logout', {
  method: 'POST',
  credentials: 'include'
});
```

### 2. Admin Endpoints - API Key Required

**Adding Admin Protection:**
```python
from app.security.admin_api_key import require_admin_api_key

@app.post("/admin/my-endpoint")
async def admin_operation(
    authenticated: bool = Depends(require_admin_api_key),
):
    # Only executes if valid API key provided
    return {"status": "success"}
```

**Calling Admin Endpoints:**
```bash
# Simple API key
curl -X POST http://localhost:8000/admin/cron/run \
  -H "X-API-Key: cultivax_admin_xxxxx"

# With signature (critical operations)
curl -X POST http://localhost:8000/admin/cron/run \
  -H "X-API-Key: cultivax_admin_xxxxx" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Signature: <computed-hmac>"
```

### 3. Logging to Blockchain

**Usage:**
```python
from app.security.blockchain_audit import log_to_blockchain

# Log any critical action
log_to_blockchain(
    action="user_role_changed",
    user_id=user_id,
    details={
        "old_role": "farmer",
        "new_role": "admin",
        "changed_by": admin_id,
    }
)
```

**Querying Audit Trail:**
```python
from app.security.blockchain_audit import get_audit_blockchain

blockchain = get_audit_blockchain()

# Get all entries for a user
entries = blockchain.get_audit_trail(user_id="123")

# Verify blockchain integrity
is_valid, errors = blockchain.verify_chain()
```

### 4. Anomaly Detection

**Manual Check:**
```python
from app.security.anomaly_detector import get_anomaly_detector

detector = get_anomaly_detector()

is_anomalous, score, reasons = detector.analyze_request(
    user_id=current_user.id,
    endpoint=request.url.path,
    method=request.method,
    ip_address=request.client.host,
)

if is_anomalous:
    logger.warning(f"Anomaly detected: {reasons}")
    # Optionally create abuse flag
    await detector.create_abuse_flag(db, user_id, score, reasons)
```

**Automatic Integration (Middleware):**
```python
# Add to main.py middleware stack
from app.security.anomaly_detector import AnomalyDetectionMiddleware
app.add_middleware(AnomalyDetectionMiddleware)
```

### 5. Quantum-Safe Audit Logging

**Sign Important Data:**
```python
from app.security.quantum_crypto import get_quantum_audit_logger

logger = get_quantum_audit_logger()

# Sign log entry
signed_entry = logger.sign_log_entry({
    "action": "data_export",
    "user_id": "123",
    "records": 1000,
})

# Store signed_entry in database
db.add(AuditLog(**signed_entry))

# Verify later
is_valid = logger.verify_log_entry(signed_entry)
```

### 6. Input Sanitization

**Automatic (Middleware):**
```python
# Already active via InputSanitizationMiddleware
# Automatically logs suspicious inputs
```

**Manual Sanitization:**
```python
from app.middleware.input_sanitization import InputSanitizationMiddleware

# HTML encoding for display
safe_text = InputSanitizationMiddleware.sanitize_for_html(user_input)

# SQL escaping (prefer parameterized queries!)
safe_sql = InputSanitizationMiddleware.sanitize_for_sql(user_input)
```

### 7. Rate Limiting

**Current Limits:**
- Farmer: 60 requests/minute
- Provider: 100 requests/minute
- Admin: 200 requests/minute
- Unauthenticated: 30 requests/minute

**Checking Rate Limit Headers:**
```bash
curl -I http://localhost:8000/api/v1/crops/

# Response headers:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 45
```

**Custom Rate Limiting:**
```python
from app.middleware.distributed_rate_limiter import get_rate_limiter

limiter = get_rate_limiter()

allowed, count, remaining = await limiter.check_rate_limit(
    key=f"custom:{user_id}:{action}",
    limit=10,
    window_seconds=60,
)
```

## For DevOps

### Environment Setup

```bash
# 1. Generate secure keys
python -c "from app.security.production_validator import generate_secure_secret_key; print(generate_secure_secret_key())"

python -c "import secrets; print(f'cultivax_admin_{secrets.token_urlsafe(32)}')"

# 2. Create .env file
cat > .env <<EOF
SECRET_KEY=<generated-secret-key>
ADMIN_API_KEY=<generated-admin-key>
REDIS_URL=redis://localhost:6379/0
APP_ENV=production
DEBUG=false
CORS_ORIGINS=https://cultivax.com,https://app.cultivax.com
PROD_DB_HOST_ALLOWLIST=sql.cloud.google.com
EOF

# 3. Install optional dependencies
pip install redis==5.0.1 numpy==1.26.3
```

### Production Checklist

```bash
# 1. Verify security validation passes
python -c "from app.config import settings; settings.APP_ENV='production'; from app.security.production_validator import ProductionSecurityValidator; ProductionSecurityValidator.enforce_production_security()"

# 2. Test admin API key
curl -X POST https://api.cultivax.com/admin/health-check \
  -H "X-API-Key: $ADMIN_API_KEY"

# 3. Verify security headers
curl -I https://api.cultivax.com/ | grep -E "(Content-Security-Policy|Strict-Transport-Security|X-Frame-Options)"

# 4. Test rate limiting
for i in {1..100}; do curl -w "%{http_code}\n" https://api.cultivax.com/health; done | grep 429

# 5. Check blockchain integrity
python -c "from app.security.blockchain_audit import get_audit_blockchain; bc = get_audit_blockchain(); print(bc.verify_chain())"
```

### Monitoring Commands

```bash
# Watch for security events
tail -f /var/log/cultivax/app.log | grep -E "(anomaly|abuse|violation|invalid)"

# Check abuse flags
psql $DATABASE_URL -c "SELECT * FROM abuse_flags WHERE reviewed = false ORDER BY created_at DESC LIMIT 10;"

# Verify blockchain
python -c "from app.security.blockchain_audit import get_audit_blockchain; bc = get_audit_blockchain(); print(f'Chain length: {len(bc.chain)}'); valid, errors = bc.verify_chain(); print(f'Valid: {valid}'); print(f'Errors: {errors}')"

# Rate limit statistics
redis-cli keys "rate_limit:*" | wc -l
```

## Common Issues & Solutions

### Issue: "Production security validation failed"

**Solution:**
```bash
# Check which validation failed
python -c "from app.security.production_validator import ProductionSecurityValidator; errors = ProductionSecurityValidator.validate_all(); print('\n'.join(errors))"

# Common fixes:
# 1. Weak secret key
export SECRET_KEY=$(python -c "from app.security.production_validator import generate_secure_secret_key; print(generate_secure_secret_key())")

# 2. CORS wildcard
export CORS_ORIGINS="https://cultivax.com,https://app.cultivax.com"

# 3. Debug mode enabled
export DEBUG=false
```

### Issue: "Rate limit exceeded"

**Solution:**
```bash
# Check current rate limit
curl -I http://localhost:8000/api/v1/crops/

# Increase limit in .env
export RATE_LIMIT_FARMER=120

# Or clear Redis
redis-cli FLUSHDB
```

### Issue: "Admin API key not working"

**Solution:**
```bash
# Verify API key is set
echo $ADMIN_API_KEY

# Test with curl
curl -v -X POST http://localhost:8000/admin/health-check \
  -H "X-API-Key: $ADMIN_API_KEY"

# Check logs for authentication errors
tail -f /var/log/cultivax/app.log | grep "API key"
```

## Testing Security Features

### Unit Tests

```python
# Test HTTPOnly cookies
def test_secure_auth_cookies(client):
    response = client.post("/api/v1/auth/login", json={...})
    assert "cultivax_access_token" in response.cookies
    assert response.cookies["cultivax_access_token"]["httponly"]

# Test admin API key
def test_admin_endpoint_requires_key(client):
    response = client.post("/admin/cron/run")
    assert response.status_code == 401

    response = client.post("/admin/cron/run", headers={"X-API-Key": "valid-key"})
    assert response.status_code == 200

# Test rate limiting
def test_rate_limiting(client):
    for i in range(100):
        response = client.get("/api/v1/crops/")
    assert response.status_code == 429
```

### Integration Tests

```bash
# Security headers
pytest tests/test_security_headers.py -v

# Input sanitization
pytest tests/test_input_sanitization.py -v

# Anomaly detection
pytest tests/test_anomaly_detection.py -v

# Blockchain audit
pytest tests/test_blockchain_audit.py -v
```

## Best Practices

1. **Always use HTTPOnly cookies for authentication** (not localStorage)
2. **Generate strong keys** (use provided generators)
3. **Enable Redis in production** (for distributed rate limiting)
4. **Monitor abuse flags regularly** (daily review)
5. **Verify blockchain integrity** (automated daily check)
6. **Review security logs** (anomalies, violations)
7. **Test security features** (before deployment)
8. **Rotate keys regularly** (SECRET_KEY: 90 days, ADMIN_API_KEY: 180 days)

## Resources

- Full Documentation: `SECURITY.md`
- Implementation Summary: `SECURITY_IMPLEMENTATION_SUMMARY.md`
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Security Issues: security@cultivax.com
