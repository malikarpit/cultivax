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
  WifiOff,
  Shield,
  Database,
  Landmark,
  AlertTriangle,
  Wifi,
  CloudSun,
  Activity,
  Plus,
  Loader2,
  Sprout,
  ShoppingBag,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';
import { apiGet } from '@/lib/api';
import { useAccessibility } from '@/hooks/useAccessibility';
import { useUnreadAlertsCount } from '@/hooks/useUnreadAlertsCount';
import { useOfflineActions } from '@/hooks/useOfflineActions';
import LanguageSwitcher from './LanguageSwitcher';
import { useTranslation } from 'react-i18next';
interface HeaderProps {
  onMenuToggle: () => void;
  sidebarCollapsed?: boolean;
}

export default function Header({ onMenuToggle, sidebarCollapsed }: HeaderProps) {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const { count: unreadAlertsCount } = useUnreadAlertsCount({ enabled: !!user });
  const {
    settings,
    toggleLargeText,
    toggleHighContrast,
    toggleReducedMotion,
    toggleTheme,
  } = useAccessibility();
  const { pendingCount } = useOfflineActions();

  const [isOnline, setIsOnline] = useState(typeof window !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const pathname              = usePathname();
  const router                = useRouter();
  const [showUserMenu, setShowUserMenu]   = useState(false);
  const [showA11yMenu, setShowA11yMenu]   = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const a11yRef     = useRef<HTMLDivElement>(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchDrop, setShowSearchDrop] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Search Debouncer
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res: any = await apiGet(`/api/v1/search?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(res.results || []);
      } catch (err) {
        console.error(err);
      } finally {
        setIsSearching(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // General click outside handler
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) setShowUserMenu(false);
      if (a11yRef.current && !a11yRef.current.contains(e.target as Node)) setShowA11yMenu(false);
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setShowSearchDrop(false);
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
        <div ref={searchRef} className="hidden md:flex relative items-center bg-cultivax-elevated rounded-lg px-3 py-1.5 w-80 border border-transparent focus-within:border-cultivax-primary transition-colors">
          <Search className="w-4 h-4 text-cultivax-text-muted mr-2 flex-shrink-0" />
          <input
            type="text"
            placeholder={t('header.search', 'Search crops, actions, services...')}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowSearchDrop(true);
            }}
            onFocus={() => { if (searchQuery) setShowSearchDrop(true); }}
            className="bg-transparent border-none outline-none text-sm text-cultivax-text-primary placeholder:text-cultivax-text-muted w-full p-0 focus:ring-0"
          />
          {isSearching && <Loader2 className="w-4 h-4 text-cultivax-primary animate-spin absolute right-3" />}
          
          {/* Search Dropdown */}
          {showSearchDrop && (searchQuery.trim().length > 0) && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-cultivax-surface border border-cultivax-border rounded-lg shadow-elevated overflow-hidden animate-slide-down">
              {searchResults.length > 0 ? (
                <div className="flex flex-col">
                  <div className="px-3 py-2 text-xs font-semibold text-cultivax-text-muted uppercase tracking-wider bg-cultivax-elevated border-b border-cultivax-border">
                    Suggestions
                  </div>
                  {searchResults.map((res: any, i: number) => {
                    const iconMap: Record<string, any> = { Sprout, CloudSun, ShoppingBag, Bell, Activity, Plus, Search };
                    const Icon = iconMap[res.icon] || Search;
                    return (
                      <button
                        key={i}
                        onClick={() => {
                          setSearchQuery('');
                          setShowSearchDrop(false);
                          router.push(res.url);
                        }}
                        className="flex items-center gap-3 px-4 py-3 text-sm text-left hover:bg-cultivax-elevated transition-colors border-b border-cultivax-border last:border-0"
                      >
                        <div className="w-8 h-8 rounded bg-cultivax-primary/10 flex items-center justify-center flex-shrink-0">
                          <Icon className="w-4 h-4 text-cultivax-primary" />
                        </div>
                        <span className="text-cultivax-text-primary truncate">{res.title}</span>
                      </button>
                    );
                  })}
                </div>
              ) : !isSearching ? (
                <div className="px-4 py-6 text-center text-sm text-cultivax-text-muted">
                  No results found for "{searchQuery}"
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-1">
        {/* Network indicator — Visual green dot when online, red when offline */}
        <div 
          className="hidden sm:flex group relative items-center"
          title={isOnline ? "You are online" : "Offline. Your actions will be stored locally and synced when you are online."}
        >
          <div className={clsx(
            "flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-colors cursor-help",
            isOnline ? "bg-emerald-500/10 border-emerald-500/20" : "bg-red-500/10 border-red-500/20 animate-pulse"
          )}>
            {isOnline ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-[11px] font-semibold text-emerald-500 font-mono">{t('header.online', 'Online')}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-red-500" />
                <span className="text-[11px] font-semibold text-red-500 font-mono">
                  {pendingCount > 0 ? `${pendingCount} queued` : t('header.offline', 'Offline')}
                </span>
              </>
            )}
          </div>
          
          {/* Detailed connection tooltip message */}
          {!isOnline && (
            <div className="absolute right-0 top-full mt-2 w-64 p-3 bg-cultivax-surface border border-cultivax-border rounded-lg shadow-elevated opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-cultivax-text-secondary leading-relaxed">
                  You are offline. Your actions will be stored locally and updated to the database when you are back online.
                </p>
              </div>
            </div>
          )}
        </div>
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
                {t('header.accessibility', 'ACCESSIBILITY')}
              </p>
              <A11yRow
                id="a11y-high-contrast"
                icon={Eye}
                label={t('header.high_contrast', 'High Contrast')}
                active={!!settings.highContrast}
                onToggle={toggleHighContrast}
              />
              <A11yRow
                id="a11y-large-text"
                icon={Type}
                label={t('header.large_text', 'Large Text Toggle')}
                active={!!settings.largeText}
                onToggle={toggleLargeText}
              />
              <div className="px-4 py-3 border-t border-b border-cultivax-border bg-cultivax-bg/50">
                <label className="flex items-center justify-between text-xs font-medium text-cultivax-text-secondary mb-2">
                  <span>{t('header.font_scale', 'Font Scale Slider')}</span>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => {
                        const slider = document.getElementById('a11y-font-slider') as HTMLInputElement;
                        if (slider) slider.value = '16';
                        document.documentElement.style.fontSize = '16px';
                      }}
                      className="text-[10px] text-cultivax-primary hover:underline px-1 py-0.5"
                    >
                      {t('header.reset', 'Reset')}
                    </button>
                    <span className="text-cultivax-primary font-mono bg-cultivax-primary/10 px-1 py-0.5 rounded">Aa</span>
                  </div>
                </label>
                <input 
                  id="a11y-font-slider"
                  type="range" 
                  min="12" max="24" 
                  defaultValue="16"
                  onChange={(e) => {
                    document.documentElement.style.fontSize = `${e.target.value}px`;
                  }}
                  className="w-full accent-cultivax-primary"
                />
              </div>
              <A11yRow
                id="a11y-reduced-motion"
                icon={Wind}
                label={t('header.reduce_motion', 'Reduce Motion')}
                active={!!settings.reducedMotion}
                onToggle={toggleReducedMotion}
              />
              <A11yRow
                id="a11y-dark-mode"
                icon={settings.theme === 'dark' ? Sun : Moon}
                label={settings.theme === 'dark' ? 'Light Mode' : t('header.dark_mode', 'Dark Mode')}
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
                <User className="w-4 h-4" /> {t('header.profile', 'Profile')}
              </button>
              <button
                id="header-settings"
                onClick={() => { setShowUserMenu(false); router.push('/settings'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <Settings className="w-4 h-4" /> {t('header.settings', 'Settings')}
              </button>
              <button
                id="header-privacy"
                onClick={() => { setShowUserMenu(false); router.push('/settings/consent'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <Shield className="w-4 h-4" /> {t('header.privacy', 'Privacy & Consent')}
              </button>
              <button
                id="header-schemes"
                onClick={() => { setShowUserMenu(false); router.push('/schemes'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <Landmark className="w-4 h-4" /> {t('header.schemes', 'Govt. Schemes')}
              </button>
              <button
                id="header-disputes"
                onClick={() => { setShowUserMenu(false); router.push('/disputes'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <AlertTriangle className="w-4 h-4" /> {t('header.disputes', 'Disputes')}
              </button>
              <button
                id="header-help"
                onClick={() => { setShowUserMenu(false); window.open('https://docs.cultivax.com', '_blank'); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated transition-colors"
              >
                <HelpCircle className="w-4 h-4" /> {t('header.help', 'Help')}
              </button>

              <div className="border-t border-cultivax-border mt-1 pt-1">
                <button
                  id="header-logout"
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" /> {t('header.logout', 'Logout')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
