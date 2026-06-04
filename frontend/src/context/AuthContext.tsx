import React, { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';
import { apiLogout, fetchCurrentUser, setLogoutCallback } from '../services/api';
import { UserRole } from '../types/user';

interface User {
  id: number;
  email: string;
  role: UserRole;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = async () => {
    if (token) {
      await apiLogout();
    }
    setToken(null);
    setUser(null);
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
  };

  useEffect(() => {
    setLogoutCallback(logout);
  });

  useEffect(() => {
    const storedToken = sessionStorage.getItem('token');
    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    try {
      const decoded = jwtDecode<{ exp: number }>(storedToken);
      if (decoded.exp * 1000 < Date.now()) {
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
        setIsLoading(false);
        return;
      }
    } catch {
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('user');
      setIsLoading(false);
      return;
    }

    setToken(storedToken);

    fetchCurrentUser()
      .then((freshUser: User) => {
        setUser(freshUser);
        sessionStorage.setItem('user', JSON.stringify(freshUser));
      })
      .catch(() => {
        setToken(null);
        setUser(null);
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    sessionStorage.setItem('token', newToken);
    sessionStorage.setItem('user', JSON.stringify(newUser));
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
