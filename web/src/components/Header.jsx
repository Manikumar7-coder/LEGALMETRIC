import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Plus, CheckCircle2, Shield, Menu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Header = ({ onToggleSidebar = () => {} }) => {
  const { user } = useAuth();
  const location = useLocation();

  const getPageTitle = (pathname) => {
    if (pathname === '/dashboard') return 'Enforcement Dashboard';
    if (pathname === '/scan' || pathname.startsWith('/inspection/new')) return 'New Commodity Inspection';
    if (pathname.startsWith('/result') || pathname.startsWith('/inspection/result')) return 'Statutory Compliance Result';
    if (pathname === '/history' || pathname === '/inspections') return 'Inspection History & Audit Trail';
    if (pathname.startsWith('/inspection/') || pathname.startsWith('/history/')) return 'Inspection Record Details';
    if (pathname === '/reports') return 'Statutory Reports Archive';
    if (pathname === '/profile' || pathname === '/settings') return 'Settings & Inspector Profile';
    return 'SafeMetric System';
  };

  return (
    <header style={{
      height: '64px',
      backgroundColor: 'var(--bg-card)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 36px',
      position: 'sticky',
      top: 0,
      zIndex: 20
    }}>
      {/* Title & Department */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <button
          type="button"
          onClick={onToggleSidebar}
          className="btn-icon mobile-menu-btn"
          aria-label="Toggle Navigation Menu"
          style={{ display: 'none' }}
        >
          <Menu size={20} />
        </button>
        <h2 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          {getPageTitle(location.pathname)}
        </h2>
        <span style={{
          fontSize: '0.75rem',
          fontWeight: '600',
          backgroundColor: '#EFF6FF',
          color: '#1E40AF',
          padding: '3px 10px',
          borderRadius: '9999px',
          border: '1px solid #BFDBFE',
          display: 'flex',
          alignItems: 'center',
          gap: '5px'
        }}>
          <Shield size={12} color="#1E40AF" />
          {user?.organization || 'Legal Metrology Department'}
        </span>
      </div>

      {/* Right Action & System Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '0.78rem',
          color: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          padding: '4px 10px',
          borderRadius: '9999px',
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: '#10B981',
            display: 'inline-block',
            boxShadow: '0 0 8px #10B981'
          }} />
          Engine Online • PCR 2011 Active
        </div>

        {location.pathname !== '/scan' && (
          <Link
            to="/scan"
            className="btn-primary"
            style={{ padding: '8px 16px', fontSize: '0.82rem' }}
          >
            <Plus size={16} />
            Scan Product
          </Link>
        )}
      </div>
    </header>
  );
};

export default Header;
