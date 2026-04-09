/**
 * API Client — Secure Cookie-Based Authentication
 *
 * Fetch wrapper that uses `credentials: 'include'` to let the browser
 * automatically attach HttpOnly cookies. No manual token injection needed.
 *
 * Security:
 * - Tokens are NEVER stored in JavaScript-accessible storage
 * - HttpOnly cookies are immune to XSS token theft
 * - Automatic 401 handling triggers token refresh
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import type { SimulationRequest, SimulationResponse, YieldRecord } from '@/lib/types';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

type ApiErrorCode = 'network' | 'http' | 'auth' | 'session';

export class ApiError extends Error {
  status?: number;
  code: ApiErrorCode;

  constructor(message: string, code: ApiErrorCode, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

function makeApiError(input: unknown, code: ApiErrorCode, status?: number): ApiError {
  const fallbackMessage = code === 'network'
    ? 'Unable to reach backend. Verify http://localhost:8000 is running and CORS allows http://localhost:3000.'
    : 'Request failed';

  const message = input instanceof Error
    ? input.message
    : (typeof input === 'string' && input.trim().length > 0 ? input : fallbackMessage);

  if (code === 'network') {
    const normalized = message.toLowerCase();
    if (
      normalized.includes('failed to fetch') ||
      normalized.includes('network request failed') ||
      normalized.includes('load failed')
    ) {
      return new ApiError(fallbackMessage, code, status);
    }
  }

  return new ApiError(message, code, status);
}

export async function api<T = any>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const method = options.method || 'GET';
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(!isFormData && { 'Content-Type': 'application/json' }),
    ...options.headers,
  };

  // Remove Content-Type if it was set explicitly to multipart/form-data
  // so the browser can attach the boundary
  if (headers['Content-Type'] === 'multipart/form-data') {
    delete headers['Content-Type'];
  }

  // Auto-generate Idempotency-Key for all mutating requests (POST/PUT/PATCH)
  // This satisfies the backend middleware requirement and prevents double-submissions
  if (['POST', 'PUT', 'PATCH'].includes(method) && !headers['Idempotency-Key']) {
    headers['Idempotency-Key'] = crypto.randomUUID();
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      method,
      headers,
      credentials: 'include',
      body: isFormData ? options.body : (options.body ? JSON.stringify(options.body) : undefined),
    });
  } catch (error) {
    throw makeApiError(error, 'network');
  }

  // Handle 401 — attempt silent token refresh
  if (response.status === 401 && !endpoint.includes('/auth/refresh')) {
    const refreshed = await attemptTokenRefresh();
    if (refreshed) {
      // Retry the original request with a fresh idempotency key
      const retryHeaders = { ...headers, 'Idempotency-Key': crypto.randomUUID() };
      let retryResponse: Response;
      try {
        retryResponse = await fetch(`${API_URL}${endpoint}`, {
          method,
          headers: retryHeaders,
          credentials: 'include',
          body: options.body ? JSON.stringify(options.body) : undefined,
        });
      } catch (error) {
        throw makeApiError(error, 'network');
      }

      if (!retryResponse.ok) {
        const error = await retryResponse.json().catch(() => ({ detail: 'Request failed after refresh' }));
        throw makeApiError(
          error.detail || `API error: ${retryResponse.status}`,
          retryResponse.status === 401 ? 'auth' : 'http',
          retryResponse.status,
        );
      }

      const retryJson = await retryResponse.json();
      if (retryJson && typeof retryJson === 'object' && 'success' in retryJson && 'data' in retryJson) {
        return retryJson.data;
      }
      return retryJson;
    }
    // Refresh failed
    if (typeof window !== 'undefined' && !endpoint.includes('/auth/me')) {
      window.location.href = '/login';
    }
    throw makeApiError('Session expired. Please log in again.', 'session', 401);
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Network error' }));
    // Surface the first detail message for 422 validation errors
    const detail = error.detail
      || (Array.isArray(error.details) && error.details[0]?.message)
      || error.error
      || `API error: ${response.status}`;
    throw makeApiError(
      detail,
      response.status === 401 ? 'auth' : 'http',
      response.status,
    );
  }

  const json = await response.json();
  if (json && typeof json === 'object' && 'success' in json && 'data' in json) {
    return json.data;
  }
  return json;
}

/**
 * Attempt to refresh the access token using the refresh cookie.
 * Returns true if successful, false otherwise.
 */
let refreshPromise: Promise<boolean> | null = null;

async function attemptTokenRefresh(): Promise<boolean> {
  // Deduplicate concurrent refresh attempts
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      return response.ok;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

// Convenience methods
export const apiGet = <T>(url: string) => api<T>(url);
export const apiPost = <T>(url: string, body: any) => api<T>(url, { method: 'POST', body });
export const apiPut = <T>(url: string, body: any) => api<T>(url, { method: 'PUT', body });
export const apiPatch = <T>(url: string, body: any) => api<T>(url, { method: 'PATCH', body });
export const apiDelete = <T>(url: string) => api<T>(url, { method: 'DELETE' });

export const simulateCrop = (cropId: string, payload: SimulationRequest) =>
  apiPost<SimulationResponse>(`/api/v1/crops/${cropId}/simulate`, payload);

export const getLatestYield = (cropId: string) =>
  apiGet<YieldRecord>(`/api/v1/crops/${cropId}/yield`);

export const getYieldHistory = (cropId: string) =>
  apiGet<YieldRecord[]>(`/api/v1/crops/${cropId}/yield/history`);
