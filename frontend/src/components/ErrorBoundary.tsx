'use client';

/**
 * Global Error Boundary — CultivaX
 * 
 * Catches unhandled React errors and displays a graceful fallback UI
 * instead of a blank screen. Uses the M3 glass design system.
 */

import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-[50vh] p-8">
          <div className="glass-card rounded-2xl border border-m3-error/20 p-8 max-w-md text-center animate-fade-in">
            <div className="w-16 h-16 rounded-full bg-m3-error/10 flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-8 h-8 text-m3-error" />
            </div>

            <h2 className="text-xl font-bold text-m3-on-surface mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-m3-on-surface-variant mb-6">
              An unexpected error occurred. This has been logged for investigation.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-3 rounded-lg bg-m3-surface-container-low text-left">
                <p className="text-xs font-mono text-m3-error break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex items-center justify-center gap-3">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-m3-primary text-m3-on-primary text-sm font-semibold hover:opacity-90 transition-opacity"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <a
                href="/dashboard"
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-m3-outline-variant/20 text-sm font-semibold text-m3-on-surface hover:bg-m3-surface-container-high transition-colors"
              >
                <Home className="w-4 h-4" />
                Dashboard
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
