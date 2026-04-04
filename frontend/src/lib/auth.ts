/**
 * Auth Utilities — Cookie-Based Session Management
 *
 * Tokens are stored in HttpOnly cookies (set by the backend).
 * JavaScript CANNOT access these tokens — this is by design (XSS protection).
 *
 * Session verification works by calling /api/v1/auth/me which reads
 * the HttpOnly cookie server-side and returns the user if valid.
 *
 * DEPRECATED: getToken/setToken/removeToken functions are removed.
 * All token management now happens via HttpOnly cookies.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USER_KEY = 'cultivax_user_cache';

/**
 * Check if user is authenticated by calling /auth/me.
 * The HttpOnly cookie is sent automatically by the browser.
 */
export async function verifySession(): Promise<any | null> {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/me`, {
      credentials: 'include',
    });

    if (!response.ok) return null;

    const user = await response.json();
    // Cache user data for instant access (non-sensitive data only)
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    }
    return user;
  } catch {
    return null;
  }
}

/**
 * Get cached user data (for instant render before /me completes).
 * This is NOT a security check — just a UX optimization.
 */
export function getCachedUser(): any | null {
  if (typeof window === 'undefined') return null;
  const data = sessionStorage.getItem(USER_KEY);
  return data ? JSON.parse(data) : null;
}

/**
 * Set cached user data (after login/register).
 */
export function setCachedUser(user: any): void {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Clear cached user data on logout.
 */
export function clearCachedUser(): void {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem(USER_KEY);
  }
}

/**
 * Perform logout — calls /auth/logout to revoke session & clear cookies.
 */
export async function performLogout(): Promise<void> {
  try {
    await fetch(`${API_URL}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
  } catch {
    // Logout request failed — still clear client cache
  }
  clearCachedUser();
}
