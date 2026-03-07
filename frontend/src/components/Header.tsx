'use client';

/**
 * Header
 */

import { useAuth } from '@/context/AuthContext';
import { usePathname } from 'next/navigation';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/crops': 'My Crops',
  '/marketplace': 'Service Marketplace',
  '/alerts': 'Alerts & Notifications',
  '/admin': 'Admin Panel',
};

export default function Header() {
  const { user, logout, isAuthenticated } = useAuth();
  const pathname = usePathname();

  if (pathname === '/login' || pathname === '/register') return null;
  if (!isAuthenticated) return null;

  const title = pageTitles[pathname] || 'CultivaX';

  return (
    <header className="h-16 bg-cultivax-surface border-b border-cultivax-card flex items-center justify-between px-6">
      <h2 className="text-lg font-semibold">{title}</h2>

      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-400">
          {user?.region && `📍 ${user.region}`}
        </span>
        <button
          onClick={logout}
          className="text-sm text-gray-400 hover:text-red-400 transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
