'use client';

/**
 * Sidebar — Unified navigation component
 * 
 * Role-based nav items with Lucide icons.
 * Active state: green left border + bg tint.
 * Mobile: Slide-out overlay with hamburger toggle.
 * Onboarding: Pulse-animates "My Crops" if user has no crops.
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Sprout,
  MapPin,
  ShoppingBag,
  Users,
  Bell,
  Settings,
  Wrench,
  Star,
  Shield,
  Landmark,
  UserCheck,
  FileText,
  Heart,
  Skull,
  Activity,
  X,
  ChevronLeft,
  ChevronRight,
  Leaf,
  CloudSun,
  ArrowRight,
  MessageSquare,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';
import { useUnreadAlertsCount } from '@/hooks/useUnreadAlertsCount';
import { useTranslation } from 'react-i18next';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  highlight?: boolean; // For onboarding pulse
}

const FARMER_NAV: NavItem[] = [
  { label: 'nav.dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'nav.crops', href: '/crops', icon: Sprout, highlight: true },
  { label: 'nav.my_fields', href: '/land-parcels', icon: MapPin },
  { label: 'nav.weather', href: '/weather', icon: CloudSun },
  { label: 'nav.services', href: '/services', icon: ShoppingBag },
  { label: 'nav.labor', href: '/labor', icon: Users },
  { label: 'nav.alerts', href: '/alerts', icon: Bell },
  { label: 'nav.messages', href: '/messages', icon: MessageSquare },
  { label: 'nav.marketplace', href: '/marketplace', icon: ShoppingBag },
  { label: 'nav.schemes', href: '/schemes', icon: Landmark },
];

const PROVIDER_NAV: NavItem[] = [
  { label: 'nav.dashboard', href: '/provider', icon: LayoutDashboard },
  { label: 'nav.equipment', href: '/provider/equipment', icon: Wrench },
  { label: 'nav.reviews', href: '/provider/reviews', icon: Star },
];

const ADMIN_NAV: NavItem[] = [
  { label: 'nav.dashboard', href: '/admin', icon: LayoutDashboard },
  { label: 'nav.user_management', href: '/admin/users', icon: UserCheck },
  { label: 'nav.provider_management', href: '/admin/providers', icon: Shield },
  { label: 'nav.rule_templates', href: '/admin/templates', icon: FileText },
  { label: 'nav.system_health', href: '/admin/health', icon: Activity },
  { label: 'nav.dead_letters', href: '/admin/dead-letters', icon: Skull },
];

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

export default function Sidebar({ isOpen, onToggle, isCollapsed: controlledCollapsed, onToggleCollapse, className }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const { count: unreadAlertsCount } = useUnreadAlertsCount({ enabled: !!user });
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const { t } = useTranslation();

  // Controlled mode: parent (layout) owns collapse state
  // Uncontrolled mode: sidebar manages its own state
  const isCollapsed = controlledCollapsed ?? internalCollapsed;
  const handleCollapse = () => {
    if (onToggleCollapse) {
      onToggleCollapse();
    } else {
      setInternalCollapsed(!internalCollapsed);
    }
  };

  // Determine nav items based on role
  const role = user?.role || 'farmer';
  const navItems =
    role === 'admin' ? ADMIN_NAV : role === 'provider' ? PROVIDER_NAV : FARMER_NAV;

  // Check if user needs onboarding highlight
  const needsOnboarding = role === 'farmer' && user && !user.is_onboarded;

  const isActive = (href: string) => {
    if (href === '/dashboard' || href === '/admin' || href === '/provider') {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-0 left-0 h-screen z-50 bg-cultivax-surface border-r border-cultivax-border',
          'flex flex-col transition-all duration-300 ease-in-out',
          // Mobile: slide out
          'md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          // Desktop: collapsible
          isCollapsed ? 'md:w-[72px]' : 'md:w-64',
          'w-72',
          className
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-4 h-[60px] border-b border-cultivax-border">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-cultivax-primary/15 rounded-lg flex items-center justify-center">
              <Leaf className="w-5 h-5 text-cultivax-primary" />
            </div>
            {!isCollapsed && (
              <span className="font-bold text-lg text-cultivax-text-primary">
                CultivaX
              </span>
            )}
          </Link>

          {/* Close on mobile */}
          <button onClick={onToggle} className="btn-icon md:hidden" title="Close Sidebar" aria-label="Close Sidebar">
            <X className="w-5 h-5" />
          </button>

          {/* Collapse on desktop */}
          <button
            onClick={handleCollapse}
            className="btn-icon hidden md:flex"
            title="Toggle Sidebar"
            aria-label="Toggle Sidebar"
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActive(item.href);
            const showPulse = needsOnboarding && item.highlight;
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => {
                  // Close mobile sidebar on navigation
                  if (window.innerWidth < 768) onToggle();
                }}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                  'transition-all duration-200 relative group',
                  active
                    ? 'bg-cultivax-primary/10 text-cultivax-primary border-l-[3px] border-cultivax-primary -ml-[3px] pl-[15px]'
                    : 'text-cultivax-text-secondary hover:bg-cultivax-elevated hover:text-cultivax-text-primary',
                  showPulse && !active && 'onboarding-pulse'
                )}
                title={isCollapsed ? t(item.label) : undefined}
              >
                <Icon
                  className={clsx(
                    'w-5 h-5 flex-shrink-0',
                    active
                      ? 'text-cultivax-primary'
                      : 'text-cultivax-text-muted group-hover:text-cultivax-text-secondary'
                  )}
                />
                {!isCollapsed && <span>{t(item.label)}</span>}

                {item.href === '/alerts' && unreadAlertsCount > 0 && (
                  <span
                    className={clsx(
                      'ml-auto rounded-full bg-cultivax-danger text-white text-[10px] font-semibold px-1.5 h-4 leading-4',
                      isCollapsed && 'absolute top-1.5 right-1.5'
                    )}
                  >
                    {unreadAlertsCount > 99 ? '99+' : unreadAlertsCount}
                  </span>
                )}

                {/* Onboarding tooltip */}
                {showPulse && !active && !isCollapsed && (
                  <span className="ml-auto text-[10px] bg-cultivax-primary text-white px-1.5 py-0.5 rounded-full font-semibold animate-pulse">
                    START
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Upsell: Become a provider */}
        {role === 'farmer' && !isCollapsed && (
          <div className="mx-3 mb-4 p-3 bg-cultivax-primary/5 rounded-lg border border-cultivax-primary/20">
            <span className="block text-xs font-semibold text-cultivax-primary mb-1 flex items-center gap-1">
              <ShoppingBag className="w-3 h-3" /> {t('nav.earn_cultivax', 'Earn with CultivaX')}
            </span>
            <p className="text-[10px] text-cultivax-text-muted mb-2">{t('nav.offer_idle', 'Offer your idle equipment and labor to others.')}</p>
            <Link 
              href="/provider/onboarding" 
              className="text-xs font-semibold text-cultivax-primary hover:underline flex items-center gap-1"
              onClick={() => { if (window.innerWidth < 768) onToggle(); }}
            >
              {t('nav.become_provider', 'Become a Provider')} <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        )}

        {/* User profile card */}
        {user && !isCollapsed && (
          <div className="border-t border-cultivax-border p-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-cultivax-primary/20 flex items-center justify-center text-cultivax-primary font-semibold text-sm">
                {(user.full_name || user.phone || 'U')
                  .charAt(0)
                  .toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-cultivax-text-primary truncate">
                  {user.full_name || 'Farmer'}
                </p>
                <p className="text-xs text-cultivax-text-muted capitalize">
                  {user.role || 'farmer'}
                </p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
