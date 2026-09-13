import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: '#0A1120',
        color: '#94A3B8',
        fontSize: '1rem',
        fontWeight: '500',
        gap: '12px'
      }}>
        <div className="animate-spin" style={{
          width: '24px',
          height: '24px',
          border: '3px solid #1E2E4E',
          borderTopColor: '#3B82F6',
          borderRadius: '50%'
        }} />
        Authenticating SafeMetric Inspector Session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
