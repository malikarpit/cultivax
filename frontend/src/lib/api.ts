/**
 * API Client
 * Fetch wrapper with automatic JWT header injection.
 */

import { getToken } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

export async function api<T = any>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// Convenience methods
export const apiGet = <T>(url: string) => api<T>(url);
export const apiPost = <T>(url: string, body: any) => api<T>(url, { method: 'POST', body });
export const apiPut = <T>(url: string, body: any) => api<T>(url, { method: 'PUT', body });
export const apiDelete = <T>(url: string) => api<T>(url, { method: 'DELETE' });
