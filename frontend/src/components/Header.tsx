'use client';

/**
 * Header — Top navigation bar
 *
 * Contains: hamburger (mobile), search bar, notification bell,
 * language switcher, accessibility panel, user dropdown.
 *
 * Accessibility toggles now use the useAccessibility hook — settings
 * persist to backend and survive page refresh.
 */

import { useState, useRef, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  Menu,
  Search,
  Bell,
  User,
  LogOut,
  Settings,
  HelpCircle,
  Eye,
  Type,
  Wind,
  Moon,
  Sun,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';
import { useAccessibility } from '@/hooks/useAccessibility';
import { useUnreadAlertsCount } from '@/hooks/useUnreadAlertsCount';
import LanguageSwitcher from './LanguageSwitcher';

interface HeaderProps {
  onMenuToggle: () => void;
  sidebarCollapsed?: boolean;
}

export default function Header({ onMenuToggle, sidebarCollapsed }: HeaderProps) {
  const { user, logout } = useAuth();
  const { count: unreadAlertsCount } = useUnreadAlertsCount({ enabled: !!user });
  const {
    settings,
    toggleLargeText,
    toggleHighContrast,
    toggleReducedMotion,
    toggleTheme,
  } = useAccessibility();

  const pathname              = usePathname();
  const router                = useRouter();
  const [showUserMenu, setShowUserMenu]   = useState(false);
  const [showA11yMenu, setShowA11yMenu]   = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const a11yRef     = useRef<HTMLDivElement>(null);

  // Close menus on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
      if (a11yRef.current && !a11yRef.current.contains(e.target as Node)) {
        setShowA11yMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Generate page title from pathname
  const getPageTitle = () => {
    const segments = pathname.split('/').filter(Boolean);
    if (segments.length === 0) return 'Home';
    const last = segments[segments.length - 1];
    return last.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  // A11y toggle row helper
  const A11yRow = ({
    icon: Icon,
    label,
    active,
    onToggle,
    id,
  }: {
    icon: React.ElementType;
    label: string;
    active: boolean;
    onToggle: () => void;
    id: string;
  }) => (
    <button
      id={id}
      onClick={onToggle}
      aria-pressed={active}
      className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
    >
      <span className="flex items-center gap-2">
        <Icon className="w-4 h-4" />
        {label}
      </span>
      {/* Toggle pill */}
      <span
        className={clsx(
          'w-8 h-4 rounded-full transition-colors flex-shrink-0',
          active ? 'bg-cultivax-primary' : 'bg-cultivax-elevated'
        )}
      >
        <span
          className={clsx(
            'block w-3.5 h-3.5 rounded-full bg-white transition-transform mt-[1px]',
            active ? 'translate-x-4' : 'translate-x-0.5'
          )}
        />
      </span>
    </button>
  );

  return (
    <header
      className={clsx(
        'fixed top-0 right-0 h-[60px] bg-cultivax-surface/95 backdrop-blur-sm',
        'border-b border-cultivax-border z-30',
        'flex items-center justify-between px-4 gap-4',
        'transition-all duration-300',
        sidebarCollapsed ? 'md:left-[72px]' : 'md:left-64',
        'left-0'
      )}
    >
      {/* Left section */}
      <div className="flex items-center gap-3">
        {/* Hamburger (mobile) */}
        <button
          onClick={onMenuToggle}
          className="btn-icon md:hidden"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Page title (mobile only) */}
        <h1 className="text-base font-semibold text-cultivax-text-primary md:hidden truncate">
          {getPageTitle()}
        </h1>

        {/* Search bar (desktop) */}
        <div className="hidden md:flex items-center bg-cultivax-elevated rounded-lg px-3 py-1.5 w-80 border border-transparent focus-within:border-cultivax-primary transition-colors">
          <Search className="w-4 h-4 text-cultivax-text-muted mr-2 flex-shrink-0" />
          <input
            type="text"
            placeholder="Search crops, actions, services..."
            className="bg-transparent border-none outline-none text-sm text-cultivax-text-primary placeholder:text-cultivax-text-muted w-full p-0 focus:ring-0"
          />
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-1">
        {/* Accessibility panel */}
        <div className="relative hidden sm:block" ref={a11yRef}>
          <button
            id="header-a11y-toggle"
            onClick={() => setShowA11yMenu(!showA11yMenu)}
            className="btn-icon"
            title="Accessibility"
            aria-label="Accessibility settings"
          >
            <Eye className="w-4 h-4" />
          </button>

          {showA11yMenu && (
            <div className="absolute right-0 top-full mt-1 bg-cultivax-surface border border-cultivax-border rounded-lg shadow-elevated py-1 w-56 animate-slide-down">
              <p className="px-4 py-1.5 text-xs font-semibold text-cultivax-text-muted uppercase tracking-wider">
                Accessibility
              </p>
              <A11yRow
                id="a11y-high-contrast"
                icon={Eye}
                label="High Contrast"
                active={!!settings.highContrast}
                onToggle={toggleHighContrast}
              />
              <A11yRow
                id="a11y-large-text"
                icon={Type}
                label="Large Text"
                active={!!settings.largeText}
                onToggle={toggleLargeText}
              />
              <A11yRow
                id="a11y-reduced-motion"
                icon={Wind}
                label="Reduce Motion"
                active={!!settings.reducedMotion}
                onToggle={toggleReducedMotion}
              />
              <A11yRow
                id="a11y-dark-mode"
                icon={settings.theme === 'dark' ? Sun : Moon}
                label={settings.theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                active={settings.theme === 'dark'}
                onToggle={toggleTheme}
              />
            </div>
          )}
        </div>

        {/* Language switcher */}
        <LanguageSwitcher compact />

        {/* Notifications */}
        <button
          id="header-notifications"
          className="btn-icon relative"
          title="Notifications"
          aria-label="Open alerts"
          onClick={() => router.push('/alerts')}
        >
          <Bell className="w-4 h-4" />
          {unreadAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-cultivax-danger text-[10px] leading-4 text-white text-center font-semibold">
              {unreadAlertsCount > 99 ? '99+' : unreadAlertsCount}
            </span>
          )}
        </button>

        {/* User menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            id="header-user-menu"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 ml-1 p-1.5 rounded-lg hover:bg-cultivax-elevated transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-cultivax-primary/20 flex items-center justify-center text-cultivax-primary font-semibold text-sm">
              {(user?.full_name || user?.phone || 'U').charAt(0).toUpperCase()}
            </div>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-full mt-1 bg-cultivax-surface border border-cultivax-border rounded-lg shadow-elevated py-1 w-52 animate-slide-down">
              {/* User info */}
              <div className="px-4 py-3 border-b border-cultivax-border">
                <p className="text-sm font-medium text-cultivax-text-primary truncate">
                  {user?.full_name || 'User'}
                </p>
                <p className="text-xs text-cultivax-text-muted capitalize">
                  {user?.role}
                </p>
                <p className="text-xs text-cultivax-text-muted truncate">
                  {user?.phone || user?.email}
                </p>
              </div>

              <button
                id="header-profile"
                onClick={() => { setShowUserMenu(false); router.push('/profile'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <User className="w-4 h-4" /> Profile
              </button>
              <button
                id="header-settings"
                onClick={() => { setShowUserMenu(false); router.push('/settings'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <Settings className="w-4 h-4" /> Settings
              </button>
              <button
                id="header-help"
                onClick={() => { setShowUserMenu(false); window.open('https://docs.cultivax.com', '_blank'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <HelpCircle className="w-4 h-4" /> Help
              </button>

              <div className="border-t border-cultivax-border mt-1 pt-1">
                <button
                  id="header-logout"
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" /> Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
