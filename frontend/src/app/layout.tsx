'use client';

/**
 * Root Layout — CultivaX Application Shell
 *
 * Two layout modes:
 * - Public: Full-width (landing, login, register, tour)
 * - Authenticated: Sidebar + Header + Content area
 *
 * Features:
 * - Dynamic <html lang> attribute (synced from user preference)
 * - i18n initialization (react-i18next)
 * - Noto Sans Indic fonts loaded via Google Fonts for Hindi/Tamil/Telugu
 */

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ErrorBoundary from '@/components/ErrorBoundary';

// Import i18n (side-effect — initializes the library)
import '@/lib/i18n';
import { useTranslation } from 'react-i18next';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

// Routes that don't use the authenticated layout
const PUBLIC_ROUTES = ['/', '/login', '/register', '/tour'];

/**
 * LangSync — Reactively sets document.documentElement.lang when the
 * user's preferred_language changes. Also tells i18next to switch.
 */
function LangSync() {
  const { user } = useAuth();
  const { i18n } = useTranslation();

  useEffect(() => {
    const lang = user?.preferred_language || 'en';
    document.documentElement.lang = lang;
    if (i18n.language !== lang) {
      i18n.changeLanguage(lang);
    }
  }, [user?.preferred_language, i18n]);

  return null;
}

function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);
  const isAuthenticated = !!user && !isLoading;

  // Safety net: redirect unauthenticated users from private routes → /login
  useEffect(() => {
    if (!isLoading && !user && !isPublicRoute) {
      router.replace('/login');
    }
  }, [isLoading, user, isPublicRoute, router]);

  // Convenience: redirect authenticated users away from public routes
  // (e.g. logged-in user visits /login → send to their dashboard)
  useEffect(() => {
    if (isAuthenticated && (pathname === '/login' || pathname === '/register')) {
      const routes: Record<string, string> = {
        farmer: '/dashboard',
        provider: '/provider',
        admin: '/admin',
      };
      router.replace(routes[user!.role] || '/dashboard');
    }
  }, [isAuthenticated, pathname, user, router]);

  // Show loading spinner during auth verification
  if (isLoading) {
    return (
      <div className="min-h-screen bg-cultivax-bg flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (isPublicRoute || !isAuthenticated) {
    // Public layout — full width, no sidebar/header
    return (
      <div className="min-h-screen bg-cultivax-bg">
        {children}
      </div>
    );
  }

  // Authenticated layout — sidebar + header + content
  return (
    <div className="min-h-screen bg-cultivax-bg">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <Header
        onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
        sidebarCollapsed={sidebarCollapsed}
      />

      <main
        className={`
          pt-[60px] transition-all duration-300
          ${sidebarCollapsed ? 'md:pl-[72px]' : 'md:pl-64'}
        `}
      >
        <div className="p-4 sm:p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable}`}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0B0F19" />
        <meta
          name="description"
          content="CultivaX — Intelligent Crop Management for Indian Farmers"
        />
        <title>CultivaX — Intelligent Crop Management</title>
        <link rel="icon" href="/favicon.ico" />
        {/* Indic font support (Google Fonts CDN) */}
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;500;600;700&family=Noto+Sans+Telugu:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${inter.className} antialiased`}>
        <AuthProvider>
          <LangSync />
          <ErrorBoundary>
            <LayoutShell>{children}</LayoutShell>
          </ErrorBoundary>
        </AuthProvider>
      </body>
    </html>
  );
}
