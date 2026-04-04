'use client';

import { useState } from 'react';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import { Users, Search, MoreVertical, Edit3, Trash2, ShieldAlert, Loader2, RefreshCw } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';
import clsx from 'clsx';

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [deletedFilter, setDeletedFilter] = useState('false');
  
  const [actionUserId, setActionUserId] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'role' | 'delete' | 'restore' | null>(null);
  const [selectedRole, setSelectedRole] = useState('farmer');

  const api = useApi();
  
  const queryParams = new URLSearchParams({
    page: page.toString(),
    per_page: '20',
  });
  if (search) queryParams.set('search', search);
  if (roleFilter) queryParams.set('role', roleFilter);
  if (deletedFilter !== 'all') queryParams.set('is_deleted', deletedFilter);

  const { data, loading, error, refetch } = useFetch(`/api/v1/admin/users?${queryParams.toString()}`);
  const users = data?.items || [];
  const totalPages = data?.total ? Math.ceil(data.total / 20) : 1;

  const handleAction = async () => {
    if (!actionUserId || !actionType) return;
    try {
      if (actionType === 'delete') {
        await api.execute(`/api/v1/admin/users/${actionUserId}`, { method: 'DELETE' });
      } else if (actionType === 'restore') {
        await api.execute(`/api/v1/admin/users/${actionUserId}/restore`, { method: 'POST' });
      } else if (actionType === 'role') {
        await api.execute(`/api/v1/admin/users/${actionUserId}/role?new_role=${selectedRole}`, { method: 'PUT' });
      }
      refetch();
      setActionType(null);
      setActionUserId(null);
    } catch (err) {
      console.error('Failed mutative action', err);
    }
  };

  const openAction = (id: string, type: 'role' | 'delete' | 'restore', currentRole?: string) => {
    setActionUserId(id);
    setActionType(type);
    if (currentRole) setSelectedRole(currentRole);
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface">User Management</h1>
            <p className="text-m3-on-surface-variant mt-2">Manage all system users, execute soft deletes, or alter access boundaries.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6 bg-m3-surface-container-high/50 p-4 rounded-xl border border-m3-outline-variant/20">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-m3-on-surface-variant" />
            <input 
              type="text" 
              placeholder="Search by name, email, phone..." 
              className="w-full bg-m3-surface border border-m3-outline-variant/30 rounded-lg pl-10 pr-4 py-2 text-sm text-m3-on-surface focus:ring-2 focus:ring-m3-primary/50"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            value={roleFilter} 
            onChange={e => setRoleFilter(e.target.value)}
            className="bg-m3-surface border border-m3-outline-variant/30 rounded-lg px-4 py-2 text-sm text-m3-on-surface appearance-none"
          >
            <option value="">All Roles</option>
            <option value="farmer">Farmer</option>
            <option value="provider">Provider</option>
            <option value="admin">Admin</option>
          </select>
          <select 
            value={deletedFilter} 
            onChange={e => setDeletedFilter(e.target.value)}
            className="bg-m3-surface border border-m3-outline-variant/30 rounded-lg px-4 py-2 text-sm text-m3-on-surface appearance-none"
          >
            <option value="false">Active Only</option>
            <option value="true">Deleted Only</option>
            <option value="all">Everyone</option>
          </select>
        </div>

        {/* Table */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-m3-surface-container-high/40 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                  <th className="p-4 font-semibold">User</th>
                  <th className="p-4 font-semibold">Contact</th>
                  <th className="p-4 font-semibold">Role</th>
                  <th className="p-4 font-semibold">Status</th>
                  <th className="p-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                {loading ? (
                   <tr>
                     <td colSpan={5} className="p-8 text-center text-m3-on-surface-variant">
                       <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                     </td>
                   </tr>
                ) : users.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="p-8 text-center text-m3-on-surface-variant">
                       <Users className="w-8 h-8 opacity-40 mx-auto mb-2" />
                       No users found matching criteria.
                     </td>
                   </tr>
                ) : (
                  users.map((user: any) => (
                    <tr key={user.id} className="hover:bg-m3-surface-container-high/30 transition-colors">
                      <td className="p-4">
                        <div className="font-semibold text-m3-on-surface">{user.full_name}</div>
                        <div className="text-xs text-m3-on-surface-variant font-mono">{user.id}</div>
                      </td>
                      <td className="p-4 text-m3-on-surface-variant">
                        <div>{user.phone}</div>
                        {user.email && <div className="text-xs">{user.email}</div>}
                      </td>
                      <td className="p-4">
                        <Badge variant={user.role === 'admin' ? 'blue' : (user.role === 'provider' ? 'amber' : 'green')}>
                          {user.role}
                        </Badge>
                      </td>
                      <td className="p-4">
                        {user.is_deleted ? (
                          <Badge variant="red">Deleted</Badge>
                        ) : (
                          <Badge variant="blue">Active</Badge>
                        )}
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                           <button onClick={() => openAction(user.id, 'role', user.role)} className="p-2 text-m3-on-surface-variant hover:bg-m3-surface-container-highest rounded-full transition-colors" title="Change Role">
                             <Edit3 className="w-4 h-4" />
                           </button>
                           {user.is_deleted ? (
                             <button onClick={() => openAction(user.id, 'restore')} className="p-2 text-green-500 hover:bg-green-500/10 rounded-full transition-colors" title="Restore User">
                               <RefreshCw className="w-4 h-4" />
                             </button>
                           ) : (
                             <button onClick={() => openAction(user.id, 'delete')} className="p-2 text-red-500 hover:bg-red-500/10 rounded-full transition-colors" title="Soft Delete">
                               <Trash2 className="w-4 h-4" />
                             </button>
                           )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="p-4 border-t border-m3-outline-variant/10 flex items-center justify-between">
            <span className="text-sm text-m3-on-surface-variant">Page {page} of {totalPages} ({data?.total || 0} total)</span>
            <div className="flex gap-2">
              <button 
                disabled={page === 1} 
                onClick={() => setPage(page - 1)}
                className="px-3 py-1 text-sm border border-m3-outline-variant/30 rounded-lg disabled:opacity-50 hover:bg-m3-surface-container-highest transition-colors"
              >
                Previous
              </button>
              <button 
                disabled={page >= totalPages} 
                onClick={() => setPage(page + 1)}
                className="px-3 py-1 text-sm border border-m3-outline-variant/30 rounded-lg disabled:opacity-50 hover:bg-m3-surface-container-highest transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Action Modal */}
      {actionType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card max-w-sm w-full p-6 rounded-2xl shadow-2xl relative border border-m3-outline-variant/20">
            <h2 className="text-xl font-bold text-m3-on-surface mb-2">
              {actionType === 'delete' ? 'Delete User?' : actionType === 'restore' ? 'Restore User?' : 'Change User Role'}
            </h2>
            <p className="text-sm text-m3-on-surface-variant mb-6">
              {actionType === 'delete' && 'This action soft-deletes the user and revokes their active sessions globally.'}
              {actionType === 'restore' && 'This restores the user to active capacity securely.'}
              {actionType === 'role' && 'Select the new boundary context. Note downgrading from admin revokes running tokens directly.'}
            </p>

            {actionType === 'role' && (
              <select 
                value={selectedRole}
                onChange={e => setSelectedRole(e.target.value)}
                className="w-full mb-6 bg-m3-surface-container-highest border border-m3-outline-variant/30 rounded-xl px-4 py-3 text-sm text-m3-on-surface appearance-none"
              >
                <option value="farmer">Farmer</option>
                <option value="provider">Provider</option>
                <option value="admin">Admin</option>
              </select>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setActionType(null)}
                className="px-4 py-2 rounded-lg font-medium text-sm text-m3-on-surface hover:bg-m3-surface-container-highest transition-colors border border-m3-outline-variant/20"
              >
                Cancel
              </button>
              <button
                onClick={handleAction}
                disabled={api.loading}
                className={clsx(
                  "px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 text-white shadow-lg",
                  actionType === 'delete' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20' : 'bg-m3-primary hover:bg-m3-primary/90 shadow-m3-primary/20'
                )}
              >
                {api.loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Confirm Execution
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
