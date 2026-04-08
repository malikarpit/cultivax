# CultivaX — Production Capacity Target

**NFR-2 / NFR-24 alignment | Baseline: 2026-04-09**

## Target Load

| Metric | Target | Evidence |
|--------|--------|----------|
| Concurrent users | 600 | SRS NFR-2 |
| p95 API response time | < 300 ms | SRS NFR-2 |
| Replay throughput | O(n), ≤ 3× per-action scaling | `tests/perf/test_replay_performance.py` |
| Media analysis non-blocking | < 2 s status check | NFR-3 |

## Cloud Run Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `--min-instances` | 2 | Warm pool for burst; no cold-start on sustained load |
| `--max-instances` | 12 | Auto-scales to handle 600-user burst |
| `--concurrency` | 120 | Per instance; 12 × 120 = 1440 max concurrent requests |
| `--cpu` | 2 | Adequate for async FastAPI under gunicorn/uvicorn |
| `--memory` | 1Gi | ML inference + DB pool headroom |

## Database Pool

| Parameter | Target |
|-----------|--------|
| `SQLALCHEMY_POOL_SIZE` | 10 |
| `SQLALCHEMY_MAX_OVERFLOW` | 20 |
| `SQLALCHEMY_POOL_TIMEOUT` | 30s |
| Cloud SQL connections | 30 (pool × 2 min instances) |

## Evidence Artifacts

| Test | Result | File |
|------|--------|------|
| Replay perf SLO (O(n)) | 1 passed | `tests/perf/test_replay_performance.py` |
| ACID isolation + rollback | 2 passed | `tests/test_db_transaction_isolation.py` |
| k6 600-user load | Pending staging run | `perf/k6_600_users.js` |

## k6 Load Test Command

```bash
k6 run backend/perf/k6_600_users.js \
  -e BASE_URL=https://<service>.a.run.app \
  --out json=docs/k6_load_report_$(date +%Y%m%d).json
```
Run against staging before each major release.
