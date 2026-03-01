'use client';

/**
 * Root Layout
 * App shell with sidebar navigation and dark theme.
 */

import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <title>CultivaX — Intelligent Crop Management</title>
        <meta name="description" content="Intelligent Crop Lifecycle Management & Service Orchestration Platform" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-cultivax-bg text-white min-h-screen">
        <AuthProvider>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-y-auto p-6">
                {children}
              </main>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
