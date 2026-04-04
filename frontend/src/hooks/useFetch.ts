import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '@/lib/api';

/**
 * useFetch — Auto-fetching hook for GET requests
 * 
 * Fetches data on mount and when URL changes.
 * Returns mock data gracefully when API is unreachable.
 */

interface UseFetchReturn<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refetch: () => void;
}

export function useFetch<T = any>(url: string | null): UseFetchReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!!url);

  const fetchData = useCallback(async () => {
    if (!url) return;
    
    setLoading(true);
    setError(null);

    try {
      const result = await apiGet<T>(url);
      setData(result);
    } catch (err: any) {
      setError(err.message);
      // Don't crash — pages handle null data gracefully
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, error, loading, refetch: fetchData };
}
