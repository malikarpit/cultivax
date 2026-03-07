'use client';

/**
 * Sidebar Navigation
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/crops', label: 'My Crops', icon: '🌾' },
  { href: '/marketplace', label: 'Services', icon: '🏪' },
  { href: '/alerts', label: 'Alerts', icon: '🔔' },
];

const adminItems = [
  { href: '/admin', label: 'Admin Panel', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, user } = useAuth();

  // Hide sidebar on auth pages
  if (pathname === '/login' || pathname === '/register') return null;
  if (!isAuthenticated) return null;

  const items = user?.role === 'admin' ? [...navItems, ...adminItems] : navItems;

  return (
    <aside className="w-64 bg-cultivax-surface border-r border-cultivax-card flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-cultivax-card">
        <h1 className="text-2xl font-bold">
          <span className="text-cultivax-primary">Cultiva</span>
          <span className="text-cultivax-accent">X</span>
        </h1>
        <p className="text-xs text-gray-500 mt-1">Crop Intelligence Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {items.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-cultivax-primary/10 text-cultivax-primary border-l-2 border-cultivax-primary'
                  : 'text-gray-400 hover:text-white hover:bg-cultivax-card/50'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-cultivax-card">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-cultivax-primary/20 flex items-center justify-center text-sm">
            {user?.full_name?.[0] || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
