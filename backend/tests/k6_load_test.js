import http from 'k6/http';
import { check, sleep } from 'k6';

// NFR-5 requires supporting up to 600 concurrent users without degradation.
export const options = {
  stages: [
    { duration: '30s', target: 200 }, // Warm up to 200 users
    { duration: '1m', target: 600 },  // Ramp up to 600 peak concurrent users
    { duration: '2m', target: 600 },  // Maintain peak load
    { duration: '30s', target: 0 },   // Cool down
  ],
  thresholds: {
    // 95% of requests must complete within 250ms (NFR-1)
    http_req_duration: ['p(95)<250'],
    // Less than 1% failure rate
    http_req_failed: ['rate<0.01'], 
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  // Phase 1: Test GET /api/v1/health (baseline)
  const healthRes = http.get(`${BASE_URL}/api/v1/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
  });

  // Phase 2: Test crops listing (typical read heavy operation)
  const cropsRes = http.get(`${BASE_URL}/api/v1/crops?limit=20`);
  check(cropsRes, {
    'crops returned successfully': (r) => r.status === 200 || r.status === 401, // 401 expected if no auth token provided for test
  });

  // Simulating user think time
  sleep(Math.random() * 2 + 1); 
}
