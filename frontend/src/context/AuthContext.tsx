import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isOffline: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (name: string, email: string, pass: string, role?: string) => Promise<void>;
  logout: () => void;
  updateUser: (u: User) => void;
  checkBackendHealth: () => Promise<boolean>;
}

const DEFAULT_DEMO_USER: User = {
  id: 'usr_recruiter_demo',
  email: 'recruiter@talentmatch.ai',
  full_name: 'Sarah Jenkins (Senior Recruiter)',
  role: 'recruiter',
  is_active: true,
  created_at: new Date().toISOString(),
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);
  const [isOffline, setIsOffline] = useState(false);

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
      const explicitLogout = sessionStorage.getItem('talentmatch_logged_out') === 'true';

      // 1. If we have a saved token, try verifying it
      if (savedToken) {
        try {
          const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Auth init timeout')), 5000)
          );
          const me = await Promise.race([authApi.getMe(), timeoutPromise]);
          if (isMounted) {
            setUser(me);
            setToken(savedToken);
            setIsOffline(false);
            setLoading(false);
            return;
          }
        } catch {
          // Token invalid or backend temporarily slow
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        }
      }

      // 2. If no valid token and user has NOT explicitly clicked logout:
      // Seamlessly authenticate with default demo recruiter so /resumes/upload and all routes work out-of-the-box!
      if (!explicitLogout) {
        try {
          const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Demo login timeout')), 4000)
          );
          const res = await Promise.race([
            authApi.login({ email: 'recruiter@talentmatch.ai', password: 'Recruiter@123456' }),
            timeoutPromise,
          ]);
          if (isMounted) {
            localStorage.setItem('access_token', res.access_token);
            setToken(res.access_token);
            setUser(res.user);
            setIsOffline(false);
            setLoading(false);
            return;
          }
        } catch {
          // Backend might be offline or initializing - fall back gracefully
          if (isMounted) {
            setIsOffline(true);
            setUser(DEFAULT_DEMO_USER);
            setToken('demo_offline_token');
            setLoading(false);
            return;
          }
        }
      }

      // 3. If explicit logout was set, stay logged out
      if (isMounted) {
        setToken(null);
        setUser(null);
        setLoading(false);
      }
    };

    initAuth();

    // Listen for 401 unauthorized events from api interceptor
    const handleUnauthorized = () => {
      if (isMounted) {
        setUser(null);
        setToken(null);
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
    const res = await authApi.login({ email, password: pass });
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setIsOffline(false);
  };

  const register = async (name: string, email: string, pass: string, role?: string) => {
    sessionStorage.removeItem('talentmatch_logged_out');
    const res = await authApi.register({ full_name: name, email, password: pass, role });
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setIsOffline(false);
  };

  const logout = () => {
    sessionStorage.setItem('talentmatch_logged_out', 'true');
    try {
      authApi.logout().catch(() => {});
    } catch {
      // ignore network errors on logout
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const updateUser = (u: User) => {
    setUser(u);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isOffline,
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
