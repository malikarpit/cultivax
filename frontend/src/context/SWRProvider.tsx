'use client';

import { SWRConfig } from 'swr';
import { apiGet } from '@/lib/api';
import { useEffect, useState } from 'react';

function localStorageProvider() {
  if (typeof window === 'undefined') {
    return new Map();
  }
  
  // Try to load cache from localStorage
  const map = new Map(JSON.parse(localStorage.getItem('cultivax-swr-cache') || '[]'));

  // Save cache to localStorage before unload
  window.addEventListener('beforeunload', () => {
    const appCache = JSON.stringify(Array.from(map.entries()));
    localStorage.setItem('cultivax-swr-cache', appCache);
  });

  return map;
}

export function SWRProvider({ children }: { children: React.ReactNode }) {
  const [provider, setProvider] = useState<Map<any, any> | undefined>(undefined);

  useEffect(() => {
    setProvider(localStorageProvider());
  }, []);

  if (!provider) return null; // Avoid hydration mismatch

  return (
    <SWRConfig
      value={{
        fetcher: (url: string) => apiGet(url),
        provider: () => provider,
        // Optional: fallback behavior or error retry config
        shouldRetryOnError: false,
        revalidateOnFocus: true,
      }}
    >
      {children}
    </SWRConfig>
  );
}