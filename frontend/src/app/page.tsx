'use client';

/**
 * Home Page — redirects to dashboard
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-pulse text-cultivax-primary text-xl">Loading...</div>
    </div>
  );
}
