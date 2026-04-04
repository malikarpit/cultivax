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

export async function api<T = any>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
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

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: options.method || 'GET',
    headers,
    credentials: 'include',
    body: isFormData ? options.body : (options.body ? JSON.stringify(options.body) : undefined),
  });

  // Handle 401 — attempt silent token refresh
  if (response.status === 401 && !endpoint.includes('/auth/refresh')) {
    const refreshed = await attemptTokenRefresh();
    if (refreshed) {
      // Retry the original request
      const retryResponse = await fetch(`${API_URL}${endpoint}`, {
        method: options.method || 'GET',
        headers,
        credentials: 'include',
        body: options.body ? JSON.stringify(options.body) : undefined,
      });

      if (!retryResponse.ok) {
        const error = await retryResponse.json().catch(() => ({ detail: 'Request failed after refresh' }));
        throw new Error(error.detail || `API error: ${retryResponse.status}`);
      }

      const retryJson = await retryResponse.json();
      if (retryJson && typeof retryJson === 'object' && 'success' in retryJson && 'data' in retryJson) {
        return retryJson.data;
      }
      return retryJson;
    }
    // Refresh failed — redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
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
