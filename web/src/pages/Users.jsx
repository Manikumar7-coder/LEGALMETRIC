import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Shield, 
  UserCheck, 
  Trash2, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw 
} from 'lucide-react';
import { userAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const UsersPage = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await userAPI.list();
      setUsers(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load user accounts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingId(userId);
    setSuccessMsg(null);
    setError(null);
    try {
      await userAPI.updateRole(userId, newRole);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
      setSuccessMsg(`Role updated successfully to ${newRole}.`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user role.');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDeleteUser = async (userId, email) => {
    if (!window.confirm(`Are you sure you want to delete user account "${email}"?`)) {
      return;
    }
    setError(null);
    try {
      await userAPI.delete(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      setSuccessMsg(`User ${email} deleted.`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete user.');
    }
  };

  const getRoleBadge = (role) => {
    const r = (role || '').toLowerCase();
    if (r === 'admin') {
      return <span className="badge badge-noncompliant" style={{ fontSize: '0.75rem', padding: '3px 8px' }}>ADMIN</span>;
    } else if (r === 'supervisor') {
      return <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: '#3B82F6', border: '1px solid rgba(59, 130, 246, 0.3)', fontSize: '0.75rem', padding: '3px 8px' }}>SUPERVISOR</span>;
    } else {
      return <span className="badge badge-compliant" style={{ fontSize: '0.75rem', padding: '3px 8px' }}>INSPECTOR</span>;
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '900', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Users size={28} color="#2563EB" /> User Management & Access Control
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Configure officer accounts and enforce role permissions (Admin, Supervisor, Inspector)
          </p>
        </div>

        <button 
          onClick={fetchUsers} 
          disabled={loading}
          className="btn-secondary"
          style={{ fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Users
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: '#EF4444',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.85rem'
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: '#10B981',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.85rem'
        }}>
          <CheckCircle2 size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Users Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Officer Name</th>
              <th>Email Address</th>
              <th>Current Tier</th>
              <th>Organization / Jurisdiction</th>
              <th>Assign Role</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = u.id === currentUser?.id;
              return (
                <tr key={u.id}>
                  <td style={{ fontWeight: '700', color: 'var(--text-muted)' }}>#{u.id}</td>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {u.name} {isSelf && <span style={{ fontSize: '0.7rem', color: '#38BDF8' }}>(You)</span>}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                  <td>{getRoleBadge(u.role)}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {u.organization || 'Legal Metrology Department'}
                  </td>
                  <td>
                    <select
                      value={u.role}
                      disabled={updatingId === u.id || isSelf}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      style={{
                        padding: '4px 8px',
                        fontSize: '0.78rem',
                        backgroundColor: 'var(--bg-canvas)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: isSelf ? 'not-allowed' : 'pointer'
                      }}
                    >
                      <option value="Inspector">Inspector (Field Officer)</option>
                      <option value="Supervisor">Supervisor (Reviewer)</option>
                      <option value="Admin">Admin (Full Control)</option>
                    </select>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    {!isSelf ? (
                      <button
                        onClick={() => handleDeleteUser(u.id, u.email)}
                        style={{
                          background: 'transparent',
                          border: '1px solid rgba(239, 68, 68, 0.25)',
                          color: '#EF4444',
                          padding: '5px 8px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '0.72rem'
                        }}
                        title="Delete User Account"
                      >
                        <Trash2 size={13} /> Delete
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Active Session</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default UsersPage;
