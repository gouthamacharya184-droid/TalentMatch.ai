import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isOffline: boolean;
  authError: string | null;
  clearAuthError: () => void;
  login: (email: string, pass: string) => Promise<void>;
  register: (name: string, email: string, pass: string, role?: string) => Promise<void>;
  logout: () => void;
  updateUser: (u: User) => void;
  checkBackendHealth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState<boolean>(() => Boolean(localStorage.getItem('access_token')));
  const [isOffline, setIsOffline] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const clearAuthError = useCallback(() => {
    setAuthError(null);
  }, []);

  const checkBackendHealth = useCallback(async (): Promise<boolean> => {
    try {
      const resp = await fetch('/api/health', { signal: AbortSignal.timeout(3000) });
      const ok = resp.ok;
      setIsOffline(!ok);
      return ok;
    } catch {
      setIsOffline(true);
      return false;
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      const savedToken = localStorage.getItem('access_token');

      if (savedToken) {
        try {
          const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Auth verification timeout')), 6000)
          );
          const me = await Promise.race([authApi.getMe(), timeoutPromise]);
          if (isMounted) {
            setUser(me);
            localStorage.setItem('user', JSON.stringify(me));
            setToken(savedToken);
            setIsOffline(false);
            setLoading(false);
            return;
          }
        } catch (err: any) {
          const reason = err?.response?.data?.detail || err?.message || 'Authentication required';
          if (err?.response?.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            if (isMounted) {
              setToken(null);
              setUser(null);
              setAuthError(`Session expired: ${reason}. Please sign in.`);
            }
          }
        }
      }

      if (isMounted) {
        setLoading(false);
      }
    };

    initAuth();

    // Listen for 401 unauthorized events from api interceptor
    const handleUnauthorized = (e: any) => {
      if (isMounted) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setUser(null);
        setToken(null);
        setAuthError(e?.detail?.message || 'Session expired. Please log in again.');
      }
    };
    window.addEventListener('talentmatch:unauthorized', handleUnauthorized);

    return () => {
      isMounted = false;
      window.removeEventListener('talentmatch:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email: string, pass: string) => {
    sessionStorage.removeItem('talentmatch_logged_out');
    setAuthError(null);
    const res = await authApi.login({ email: email.trim(), password: pass });
    if (!res || !res.access_token || !res.user) {
      throw new Error('Authentication response is missing access token or user profile.');
    }
    localStorage.setItem('access_token', res.access_token);
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token);
    }
    localStorage.setItem('user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
    setIsOffline(false);
    setLoading(false);
  };

  const register = async (name: string, email: string, pass: string, role?: string) => {
    sessionStorage.removeItem('talentmatch_logged_out');
    setAuthError(null);
    const res = await authApi.register({ full_name: name.trim(), email: email.trim(), password: pass, role });
    if (!res || !res.access_token || !res.user) {
      throw new Error('Registration response is missing access token or user profile.');
    }
    localStorage.setItem('access_token', res.access_token);
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token);
    }
    localStorage.setItem('user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
    setIsOffline(false);
    setLoading(false);
  };

  const logout = () => {
    sessionStorage.setItem('talentmatch_logged_out', 'true');
    try {
      authApi.logout().catch(() => {});
    } catch {
      // ignore network errors on logout
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setAuthError(null);
    setLoading(false);
  };

  const updateUser = (u: User) => {
    setUser(u);
    localStorage.setItem('user', JSON.stringify(u));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isOffline,
        authError,
        clearAuthError,
        login,
        register,
        logout,
        updateUser,
        checkBackendHealth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
