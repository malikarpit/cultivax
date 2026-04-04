import { useState, useCallback } from 'react';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  /**
   * Provide a custom Idempotency-Key for this request.
   * If omitted on a POST/PUT/PATCH, one is generated automatically.
   * Pass `idempotencyKey: false` to explicitly suppress auto-generation.
   */
  idempotencyKey?: string | false;
}

interface UseApiReturn<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  execute: (url: string, options?: ApiOptions) => Promise<T>;
}

/**
 * Generate a UUID v4 using the Web Crypto API (available in all modern browsers
 * and Next.js server-side runtime). Falls back to Math.random if unavailable.
 */
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback — RFC4122 v4 compliant
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH']);

export function useApi<T = any>(): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async (url: string, options: ApiOptions = {}) => {
    setLoading(true);
    setError(null);

    const method = options.method || 'GET';
    const needsIdempotencyKey =
      MUTATING_METHODS.has(method.toUpperCase()) &&
      options.idempotencyKey !== false;

    // Auto-generate Idempotency-Key for all mutating requests unless suppressed.
    // If the caller provides one explicitly, use that (enables safe retry flows).
    const idempotencyKey =
      needsIdempotencyKey
        ? (typeof options.idempotencyKey === 'string'
            ? options.idempotencyKey
            : generateUUID())
        : undefined;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${url}`,
        {
          method,
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
            ...options.headers,
          },
          ...(options.body ? { body: JSON.stringify(options.body) } : {}),
        }
      );

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      // Handle the universal { success, data, meta } envelope if present
      if (result && typeof result === 'object' && 'success' in result && 'data' in result) {
        setData(result.data);
        return result.data;
      }
      setData(result);
      return result;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, error, loading, execute };
}
