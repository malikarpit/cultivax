import { useState, useCallback } from 'react';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

interface UseApiReturn<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  execute: (url: string, options?: ApiOptions) => Promise<T>;
}

export function useApi<T = any>(): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async (url: string, options: ApiOptions = {}) => {
    setLoading(true);
    setError(null);

    try {
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('token')
        : null;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${url}`,
        {
          method: options.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
          },
          ...(options.body ? { body: JSON.stringify(options.body) } : {}),
        }
      );

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
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
