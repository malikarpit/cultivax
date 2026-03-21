'use client';

import { useEffect, useState } from 'react';
import DataTable from '@/components/DataTable';

export default function AdminProvidersPage() {
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/providers`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      const data = await res.json();
      setProviders(data?.items || data || []);
    } catch (err) {
      console.error('Failed to fetch providers:', err);
    } finally {
      setLoading(false);
    }
  };

  const columns = ['business_name', 'region', 'is_verified', 'trust_score', 'created_at'];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Provider Management</h1>
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading providers...</div>
      ) : (
        <DataTable data={providers} columns={columns} />
      )}
    </div>
  );
}
