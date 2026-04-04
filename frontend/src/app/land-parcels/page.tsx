'use client';

import { useEffect, useMemo, useState } from 'react';
import { Plus, Search } from 'lucide-react';

import ProtectedRoute from '@/components/ProtectedRoute';
import ConfirmModal from '@/components/ConfirmModal';
import ParcelForm from '@/components/ParcelForm';
import ParcelList from '@/components/ParcelList';
import { deleteLandParcel, listLandParcels, restoreLandParcel } from '@/lib/land-parcels';
import type { LandParcel } from '@/lib/types';

export default function LandParcelsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<LandParcel[]>([]);
  const [search, setSearch] = useState('');
  const [showDeleted, setShowDeleted] = useState(false);

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<LandParcel | null>(null);

  const [deleting, setDeleting] = useState<LandParcel | null>(null);
  const [deletingBusy, setDeletingBusy] = useState(false);
  const [restoring, setRestoring] = useState<LandParcel | null>(null);
  const [restoringBusy, setRestoringBusy] = useState(false);

  const load = async (includeDeleted = showDeleted) => {
    setLoading(true);
    setError(null);
    try {
      const parcels = await listLandParcels(includeDeleted);
      setItems(parcels);
    } catch (err: any) {
      setError(err.message || 'Failed to load fields');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((parcel) => {
      return (
        parcel.parcel_name.toLowerCase().includes(q) ||
        parcel.region.toLowerCase().includes(q) ||
        (parcel.sub_region || '').toLowerCase().includes(q)
      );
    });
  }, [items, search]);

  const handleDelete = async () => {
    if (!deleting || deletingBusy) return;
    setDeletingBusy(true);
    try {
      await deleteLandParcel(deleting.id);
      setDeleting(null);
      await load();
    } catch (err: any) {
      setError(err.message || 'Failed to delete field');
    } finally {
      setDeletingBusy(false);
    }
  };

  const handleRestore = async () => {
    if (!restoring || restoringBusy) return;
    setRestoringBusy(true);
    try {
      await restoreLandParcel(restoring.id);
      setRestoring(null);
      await load(true);
    } catch (err: any) {
      setError(err.message || 'Failed to restore field');
    } finally {
      setRestoringBusy(false);
    }
  };

  const activeCount = useMemo(() => items.filter((item) => !item.is_deleted).length, [items]);
  const deletedCount = useMemo(() => items.filter((item) => item.is_deleted).length, [items]);

  return (
    <ProtectedRoute requiredRole={["farmer", "admin"]}>
      <div className="animate-fade-in space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-cultivax-text-primary">My Fields</h1>
            <p className="text-sm text-cultivax-text-muted mt-0.5">
              Manage field boundaries, soil profile, and irrigation metadata
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={() => {
              setEditing(null);
              setShowForm(true);
            }}
            type="button"
          >
            <Plus className="w-4 h-4" /> New Field
          </button>
        </div>

        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
          <input
            className="input !pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by field name or region"
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-cultivax-text-muted">
            {activeCount} active fields{showDeleted ? `, ${deletedCount} deleted` : ''}
          </p>
          <label className="inline-flex items-center gap-2 text-sm text-cultivax-text-secondary">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={async (e) => {
                const next = e.target.checked;
                setShowDeleted(next);
                await load(next);
              }}
            />
            Show deleted fields
          </label>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton h-40 rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <div className="card text-red-400">{error}</div>
        ) : (
          <ParcelList
            parcels={filtered}
            onEdit={(parcel) => {
              setEditing(parcel);
              setShowForm(true);
            }}
            onDelete={(parcel) => setDeleting(parcel)}
            onRestore={(parcel) => setRestoring(parcel)}
          />
        )}
      </div>

      {showForm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowForm(false)} />
          <div className="relative bg-cultivax-surface border border-cultivax-border rounded-2xl p-5 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-cultivax-text-primary mb-4">
              {editing ? 'Edit Field' : 'Create Field'}
            </h2>
            <ParcelForm
              initialData={editing}
              onCancel={() => setShowForm(false)}
              onSuccess={async () => {
                setShowForm(false);
                setEditing(null);
                await load();
              }}
            />
          </div>
        </div>
      ) : null}

      <ConfirmModal
        isOpen={!!deleting}
        title="Delete field"
        message={
          deleting
            ? `Delete \"${deleting.parcel_name}\"? You can restore this field from the deleted list.`
            : 'Delete this field?'
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onCancel={() => setDeleting(null)}
        onConfirm={handleDelete}
        loading={deletingBusy}
      />

      <ConfirmModal
        isOpen={!!restoring}
        title="Restore field"
        message={
          restoring
            ? `Restore \"${restoring.parcel_name}\" to active fields?`
            : 'Restore this field?'
        }
        confirmLabel="Restore"
        cancelLabel="Cancel"
        onCancel={() => setRestoring(null)}
        onConfirm={handleRestore}
        loading={restoringBusy}
      />
    </ProtectedRoute>
  );
}
