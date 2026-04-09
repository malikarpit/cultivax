import useSWR from 'swr';
import { apiGet } from '@/lib/api';

/**
 * useFetch — Auto-fetching hook for GET requests using SWR
 * 
 * Includes offline caching from SWRProvider.
 */

interface UseFetchReturn<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refetch: () => void;
}

export function useFetch<T = any>(url: string | null): UseFetchReturn<T> {
  const { data, error, isLoading, mutate } = useSWR<T>(url, url ? () => apiGet<T>(url) : null);

  return { 
    data: data ?? null, 
    error: error?.message || null, 
    loading: isLoading, 
    refetch: () => mutate() 
  };
}