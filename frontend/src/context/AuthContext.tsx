'use client';

/**
 * Auth Context
 * Provides authentication state and methods to all components.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getToken, setToken, removeToken, getStoredUser, setStoredUser } from '@/lib/auth';
import { apiPost } from '@/lib/api';

interface User {
  id: string;
  full_name: string;
  phone: string;
  email?: string;
  role: string;
  region?: string;
  is_onboarded: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (phone: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Restore session from localStorage
    const savedToken = getToken();
    const savedUser = getStoredUser();
    if (savedToken && savedUser) {
      setTokenState(savedToken);
      setUser(savedUser);
    }
    setIsLoading(false);
  }, []);

  const login = async (phone: string, password: string) => {
    const response = await apiPost<{ access_token: string; user: User }>(
      '/api/v1/auth/login',
      { phone, password }
    );
    setToken(response.access_token);
    setStoredUser(response.user);
    setTokenState(response.access_token);
    setUser(response.user);
  };

  const register = async (data: any) => {
    const response = await apiPost<{ access_token: string; user: User }>(
      '/api/v1/auth/register',
      data
    );
    setToken(response.access_token);
    setStoredUser(response.user);
    setTokenState(response.access_token);
    setUser(response.user);
  };

  const logout = () => {
    removeToken();
    setTokenState(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
