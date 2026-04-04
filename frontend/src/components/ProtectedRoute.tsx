'use client';

/**
 * ProtectedRoute
 *
 * Wraps pages that require authentication.
 * Optionally enforces role-based access (RBAC).
 *
 * Usage:
 *   <ProtectedRoute>...</ProtectedRoute>             // any logged-in user
 *   <ProtectedRoute requiredRole="admin">...</>       // admin only
 *   <ProtectedRoute requiredRole={["admin","provider"]}>...</>
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ShieldAlert } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Single role or array of allowed roles. Omit to allow any authenticated user. */
  requiredRole?: string | string[];
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  // Role-based access control
  if (requiredRole && user) {
    const allowed = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
    if (!allowed.includes(user.role)) {
      return (
        <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-red-500/15 flex items-center justify-center">
            <ShieldAlert className="w-8 h-8 text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-cultivax-text-primary">
            Access Denied
          </h2>
          <p className="text-sm text-cultivax-text-muted max-w-md">
            You don&apos;t have permission to view this page. Required role:{' '}
            <span className="text-cultivax-primary font-medium">
              {allowed.join(' or ')}
            </span>
          </p>
          <button
            onClick={() => router.back()}
            className="mt-2 px-4 py-2 text-sm bg-cultivax-elevated text-cultivax-text-secondary rounded-lg hover:bg-cultivax-border transition-colors"
          >
            Go Back
          </button>
        </div>
      );
    }
  }

  return <>{children}</>;
}
