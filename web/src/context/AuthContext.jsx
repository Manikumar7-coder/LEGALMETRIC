import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('safemetric_token');
      const savedUser = localStorage.getItem('safemetric_user');

      if (savedToken && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          // Verify with /auth/me in background
          const me = await authAPI.getMe();
          setUser(me);
          localStorage.setItem('safemetric_user', JSON.stringify(me));
        } catch (err) {
          console.warn('Session expired or invalid token:', err);
          localStorage.removeItem('safemetric_token');
          localStorage.removeItem('safemetric_user');
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const data = await authAPI.login(email, password);
    localStorage.setItem('safemetric_token', data.access_token);
    localStorage.setItem('safemetric_user', JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  };

  const register = async (name, email, password, role, organization) => {
    const data = await authAPI.register(name, email, password, role, organization);
    localStorage.setItem('safemetric_token', data.access_token);
    localStorage.setItem('safemetric_user', JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  };

  const logout = async () => {
    await authAPI.logout();
    setUser(null);
  };

  const userRole = (user?.role || '').toLowerCase();
  const isAdmin = userRole === 'admin' || userRole === 'administrator';
  const isSupervisor = isAdmin || userRole === 'supervisor' || userRole === 'chief inspector';
  const isInspector = true;

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      login, 
      register, 
      logout, 
      setUser,
      role: user?.role || 'Inspector',
      isAdmin,
      isSupervisor,
      isInspector
    }}>
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
