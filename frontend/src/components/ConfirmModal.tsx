'use client';

/**
 * ConfirmModal — Confirmation dialog for destructive actions
 */

import { X } from 'lucide-react';
import clsx from 'clsx';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'primary';
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export default function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'primary',
  onConfirm,
  onCancel,
  loading = false,
}: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative bg-cultivax-surface border border-cultivax-border rounded-2xl p-6 max-w-md w-full shadow-elevated animate-slide-up">
        {/* Close button */}
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 btn-icon"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Content */}
        <h3 className="text-lg font-semibold text-cultivax-text-primary mb-2">
          {title}
        </h3>
        <p className="text-sm text-cultivax-text-secondary mb-6">
          {message}
        </p>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="btn-secondary" disabled={loading}>
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={clsx(
              variant === 'danger' ? 'btn-danger' : 'btn-primary'
            )}
            disabled={loading}
          >
            {loading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
