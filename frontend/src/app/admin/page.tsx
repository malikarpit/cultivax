'use client';

import { useEffect, useState } from 'react';

interface Stats {
  total_users: number;
  total_crops: number;
  total_providers: number;
  active_requests: number;
}

export default function AdminPage() {
  const [stats, setStats] = useState<Stats>({
    total_users: 0,
    total_crops: 0,
    total_providers: 0,
    active_requests: 0,
  });

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Total Users</p>
          <p className="text-3xl font-bold text-blue-600">{stats.total_users}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Active Crops</p>
          <p className="text-3xl font-bold text-green-600">{stats.total_crops}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Providers</p>
          <p className="text-3xl font-bold text-purple-600">{stats.total_providers}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Active Requests</p>
          <p className="text-3xl font-bold text-orange-600">{stats.active_requests}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <a href="/admin/users" className="block p-6 bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
          <h3 className="text-lg font-semibold mb-2">👤 User Management</h3>
          <p className="text-gray-500">Manage users, roles, and permissions</p>
        </a>
        <a href="/admin/providers" className="block p-6 bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
          <h3 className="text-lg font-semibold mb-2">🏪 Provider Management</h3>
          <p className="text-gray-500">Verify, suspend, and manage service providers</p>
        </a>
      </div>
    </div>
  );
}
