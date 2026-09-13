import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Scan, 
  History, 
  FileText, 
  Settings, 
  LogOut,
  Scale,
  Home,
  Users
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar = ({ isOpen = false, onClose = () => {} }) => {
  const { user, logout, isAdmin, isSupervisor } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/scan', label: 'New Inspection', icon: Scan },
    { to: '/history', label: 'Inspection History', icon: History },
    { to: '/reports', label: 'Reports', icon: FileText },
    ...(isAdmin ? [{ to: '/users', label: 'User Management', icon: Users }] : []),
    { to: '/settings', label: 'Settings & Profile', icon: Settings },
  ];

  return (
    <>
      <div 
        className={`sidebar-backdrop ${isOpen ? 'open' : ''}`} 
        onClick={onClose}
        aria-hidden="true" 
      />
      <aside className={`app-sidebar ${isOpen ? 'open' : ''}`}>
      {/* Brand Header */}
      <div style={{
        padding: '24px 20px',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <NavLink to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.4)'
          }}>
            <ShieldCheck size={22} color="#FFFFFF" />
          </div>
          <div>
            <h1 style={{
              fontSize: '1.15rem',
              fontWeight: '800',
              letterSpacing: '-0.02em',
              color: 'var(--text-primary)',
              lineHeight: 1.1
            }}>
              SAFE METRIC
            </h1>
            <span style={{
              fontSize: '0.68rem',
              color: 'var(--accent-primary)',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              GovTech AI Compliance
            </span>
          </div>
        </NavLink>
        <p style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginTop: '10px',
          lineHeight: '1.3'
        }}>
          Legal Metrology (Packaged Commodities) Rules, 2011
        </p>
      </div>

      {/* Navigation Links */}
      <nav style={{ padding: '16px 12px', flex: 1 }}>
        <div style={{
          fontSize: '0.7rem',
          fontWeight: '700',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--text-muted)',
          padding: '0 12px 10px'
        }}>
          Enforcement Suite
        </div>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.875rem',
                    fontWeight: isActive ? '600' : '500',
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    backgroundColor: isActive ? 'rgba(37, 99, 235, 0.18)' : 'transparent',
                    border: isActive ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
                    transition: 'all 0.15s ease',
                  })}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>

        {/* Regulatory Badge */}
        <div style={{
          marginTop: '32px',
          padding: '12px',
          background: '#0F1D36',
          border: '1px solid #1E2E4E',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          gap: '10px',
          alignItems: 'flex-start'
        }}>
          <Scale size={18} color="#38BDF8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#FFFFFF' }}>
              Statutory Authority
            </div>
            <div style={{ fontSize: '0.7rem', color: '#CBD5E1', marginTop: '2px', lineHeight: '1.4' }}>
              Automated assistance under Legal Metrology Act, 2009.
            </div>
          </div>
        </div>
      </nav>

      {/* User Footer */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-canvas)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              backgroundColor: '#1E3A8A',
              color: '#93C5FD',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: '700',
              fontSize: '0.85rem',
              flexShrink: 0,
              border: '1px solid #3B82F6'
            }}>
              {user?.name ? user.name.charAt(0).toUpperCase() : 'O'}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{
                fontSize: '0.82rem',
                fontWeight: '600',
                color: 'var(--text-primary)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {user?.name || 'Authorized Officer'}
              </div>
              <div style={{
                fontSize: '0.7rem',
                color: 'var(--text-muted)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {user?.role || 'Inspector'}
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            style={{
              background: 'transparent',
              color: 'var(--text-muted)',
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = '#EF4444'}
            onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
    </>
  );
};

export default Sidebar;
