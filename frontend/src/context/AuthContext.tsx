'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type UserRole = 'ADMIN' | 'NGO' | 'DONOR';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  apiFetch: (endpoint: string, options?: RequestInit) => Promise<any>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('ngo_auth_token');
    const storedUser = localStorage.getItem('ngo_auth_user');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('ngo_auth_token');
        localStorage.removeItem('ngo_auth_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('ngo_auth_token', newToken);
    localStorage.setItem('ngo_auth_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('ngo_auth_token');
    localStorage.removeItem('ngo_auth_user');
  };

  const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    // Always read the freshest token: state may be null during page-navigation
    // hydration because the useEffect that restores token from localStorage is
    // asynchronous.  Falling back to localStorage prevents the race condition
    // where apiFetch is called before the state update propagates.
    const activeToken = token || (typeof window !== 'undefined' ? localStorage.getItem('ngo_auth_token') : null);
    if (activeToken) {
      headers['Authorization'] = `Bearer ${activeToken}`;
    }

    // Don't set Content-Type if uploading FormData
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);

    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        ...options,
        headers,
        signal: options.signal || controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));

        // These endpoints do not require auth (OTP endpoints are unauthenticated now)
        // or are the primary auth endpoints. Never auto-logout on 401 from them.
        const isOtpEndpoint = (
          endpoint.includes('/api/auth/verify-login-otp') ||
          endpoint.includes('/api/auth/resend-login-otp') ||
          endpoint.includes('/api/auth/generate-role-otp') ||
          endpoint.includes('/api/auth/forgot-password') ||
          endpoint.includes('/api/auth/verify-reset-otp') ||
          endpoint.includes('/api/auth/reset-password')
        );
        const isAuthEndpoint = (
          endpoint.includes('/api/auth/login') ||
          endpoint.includes('/api/auth/register')
        );

        if (response.status === 401 && !isAuthEndpoint && !isOtpEndpoint) {
          logout();
        }

        let errorMessage = `HTTP Error ${response.status}`;
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (typeof errorData.message === 'string') {
          errorMessage = errorData.message;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail
            .map((item: any) => {
              if (item?.msg) {
                const loc = Array.isArray(item.loc) ? item.loc.filter((l: any) => l !== 'body').join('.') : '';
                return loc ? `${loc}: ${item.msg}` : item.msg;
              }
              return String(item);
            })
            .join('; ');
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Document analysis request timed out. Please check server status or try a smaller file.');
      }
      if (err.name === 'TypeError' && (err.message === 'Failed to fetch' || err.message.includes('fetch'))) {
        throw new Error(`Unable to connect to the server (${baseUrl}). Please ensure the backend is running.`);
      }
      throw err;
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, apiFetch }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
