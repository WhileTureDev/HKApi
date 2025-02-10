'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      console.log('Checking auth...');
      const storedToken = localStorage.getItem('token');
      
      if (!storedToken) {
        console.log('No token found');
        setUser(null);
        setToken(null);
        setLoading(false);
        return;
      }

      const response = await fetch('/api/auth/check', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${storedToken}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Auth check response:', response.status);

      if (!response.ok) {
        console.log('Auth check failed');
        localStorage.removeItem('token');
        setUser(null);
        setToken(null);
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log('Auth check successful:', data);
      setUser(data.user);
      setToken(storedToken);
    } catch (error) {
      console.error('Auth check error:', error);
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('Auth context mounted');
    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      console.log('Logging in...');
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        console.log('Login failed:', response.status);
        throw new Error('Login failed');
      }

      const data = await response.json();
      console.log('Login successful:', data);
      
      if (!data.token) {
        console.error('No token received');
        throw new Error('No token received');
      }

      localStorage.setItem('token', data.token);
      await checkAuth();
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      console.log('Logging out...');
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
      localStorage.removeItem('token');
      setUser(null);
      setToken(null);
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!user && !!token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
