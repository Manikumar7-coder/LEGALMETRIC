import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  User, 
  Shield, 
  Building, 
  Mail, 
  Calendar, 
  KeyRound, 
  CheckCircle2, 
  Save, 
  AlertCircle,
  Settings,
  Scale,
  Cpu,
  Database,
  FileCheck
} from 'lucide-react';
import { profileAPI, settingsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const ProfilePage = () => {
  const { user: authUser, setUser: setAuthUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState(location.pathname === '/settings' ? 'settings' : 'profile');
  const [profileData, setProfileData] = useState(null);
  const [settingsData, setSettingsData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Edit fields
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [organization, setOrganization] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (location.pathname === '/settings') {
      setActiveTab('settings');
    } else if (location.pathname === '/profile') {
      setActiveTab('profile');
    }
  }, [location.pathname]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [pData, sData] = await Promise.all([
          profileAPI.get().catch(() => null),
          settingsAPI.get().catch(() => null)
        ]);
        if (pData) {
          setProfileData(pData);
          setName(pData.name || '');
          setRole(pData.role || '');
          setOrganization(pData.organization || '');
        }
        if (sData) {
          setSettingsData(sData);
        }
      } catch (err) {
        console.error('Failed to load profile data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (newPassword && newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    if (newPassword && newPassword.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name,
        role,
        organization,
        new_password: newPassword || undefined
      };
      const res = await profileAPI.update(payload);
      setMessage('Officer credentials updated successfully.');
      setNewPassword('');
      setConfirmPassword('');
      if (res.user) {
        setAuthUser(res.user);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#94A3B8', gap: '10px' }}>
        <div className="animate-spin" style={{ width: '24px', height: '24px', border: '3px solid #1E2E4E', borderTopColor: '#3B82F6', borderRadius: '50%' }} />
        Loading Officer Profile & Settings...
      </div>
    );
  }

  const stats = profileData?.stats || { total_inspections: 0, compliant: 0, non_compliant: 0, review_required: 0 };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#38BDF8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Enforcement Administration
          </span>
        </div>
        <h1 style={{ fontSize: '1.65rem', fontWeight: '800', color: '#FFFFFF', marginTop: '2px' }}>
          {activeTab === 'settings' ? 'System & Enforcement Settings' : 'Inspector Profile & Credentials'}
        </h1>
        <p style={{ fontSize: '0.85rem', color: '#94A3B8', marginTop: '4px' }}>
          {activeTab === 'settings'
            ? 'Configure statutory inspection parameters, OCR thresholds, and compliance rule enforcement'
            : 'Manage your official enforcement credentials, department association, and personal inspection record audit'
          }
        </p>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-subtle)',
        gap: '12px'
      }}>
        <button
          type="button"
          onClick={() => { setActiveTab('profile'); navigate('/profile'); }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            background: 'transparent',
            borderBottom: activeTab === 'profile' ? '2px solid #3B82F6' : '2px solid transparent',
            color: activeTab === 'profile' ? '#FFFFFF' : 'var(--text-secondary)',
            fontWeight: activeTab === 'profile' ? '700' : '500',
            fontSize: '0.88rem'
          }}
        >
          <User size={16} /> Inspector Profile
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('settings'); navigate('/settings'); }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            background: 'transparent',
            borderBottom: activeTab === 'settings' ? '2px solid #3B82F6' : '2px solid transparent',
            color: activeTab === 'settings' ? '#FFFFFF' : 'var(--text-secondary)',
            fontWeight: activeTab === 'settings' ? '700' : '500',
            fontSize: '0.88rem'
          }}
        >
          <Settings size={16} /> System & Rule Settings
        </button>
      </div>

      {message && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid #10B981',
          color: '#6EE7B7',
          padding: '12px 16px',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid #DC2626',
          color: '#FCA5A5',
          padding: '12px 16px',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {activeTab === 'profile' && (
        <>
          {/* Profile Overview Card */}
          <div className="card" style={{
            padding: '28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '24px',
            background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(15, 29, 54, 0.6) 100%)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{
                width: '72px',
                height: '72px',
                borderRadius: '50%',
                backgroundColor: '#1E40AF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.8rem',
                fontWeight: '800',
                color: '#FFFFFF',
                boxShadow: '0 4px 16px rgba(37, 99, 235, 0.4)',
                border: '2px solid #3B82F6'
              }}>
                {name ? name.charAt(0).toUpperCase() : 'O'}
              </div>
              <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: '800', color: '#FFFFFF' }}>
                  {name || 'Legal Metrology Officer'}
                </h2>
                <div style={{ fontSize: '0.85rem', color: '#93C5FD', marginTop: '2px', fontWeight: '600' }}>
                  {role || 'Enforcement Inspector'}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '8px', fontSize: '0.78rem', color: '#94A3B8' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Building size={14} /> {organization || 'Department of Legal Metrology'}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Mail size={14} /> {profileData?.email}
                  </span>
                </div>
              </div>
            </div>

            {/* Officer Audit Stats */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <div style={{
                padding: '12px 18px',
                backgroundColor: '#070D19',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                textAlign: 'center',
                minWidth: '90px'
              }}>
                <div style={{ fontSize: '0.7rem', color: '#94A3B8', fontWeight: '700', textTransform: 'uppercase' }}>Audits</div>
                <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#FFFFFF', marginTop: '2px' }}>{stats.total_inspections}</div>
              </div>
              <div style={{
                padding: '12px 18px',
                backgroundColor: '#070D19',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                textAlign: 'center',
                minWidth: '90px'
              }}>
                <div style={{ fontSize: '0.7rem', color: '#10B981', fontWeight: '700', textTransform: 'uppercase' }}>Passed</div>
                <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#10B981', marginTop: '2px' }}>{stats.compliant}</div>
              </div>
              <div style={{
                padding: '12px 18px',
                backgroundColor: '#070D19',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                textAlign: 'center',
                minWidth: '90px'
              }}>
                <div style={{ fontSize: '0.7rem', color: '#EF4444', fontWeight: '700', textTransform: 'uppercase' }}>Violations</div>
                <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#EF4444', marginTop: '2px' }}>{stats.non_compliant}</div>
              </div>
            </div>
          </div>

          {/* Edit Form */}
          <div className="card" style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '20px' }}>
              Update Official Credentials
            </h3>

            <form onSubmit={handleUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Official Email (Read-Only)</label>
                  <input
                    type="email"
                    className="form-input"
                    value={profileData?.email || ''}
                    disabled
                    style={{ opacity: 0.6, cursor: 'not-allowed' }}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Official Designation / Role</label>
                  <input
                    type="text"
                    className="form-input"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Department / Jurisdiction</label>
                  <input
                    type="text"
                    className="form-input"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                  />
                </div>
              </div>

              {/* Password Section */}
              <div style={{
                borderTop: '1px solid var(--border-subtle)',
                paddingTop: '20px',
                marginTop: '6px'
              }}>
                <h4 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <KeyRound size={16} color="#38BDF8" /> Change Security Password
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">New Password (leave blank to keep current)</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Minimum 6 characters"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Confirm New Password</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Repeat new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-primary"
                  style={{ padding: '10px 24px' }}
                >
                  <Save size={16} />
                  {saving ? 'Saving Updates...' : 'Save Profile Changes'}
                </button>
              </div>
            </form>
          </div>
        </>
      )}

      {activeTab === 'settings' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Engine Parameters Card */}
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <Cpu size={20} color="#38BDF8" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF' }}>
                  Vision Intelligence & OCR Engine Configuration
                </h3>
                <p style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                  Active model runtime and confidence evaluation thresholds
                </p>
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '14px'
            }}>
              <div style={{ padding: '16px', backgroundColor: '#070D19', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: '#94A3B8', fontWeight: '700', textTransform: 'uppercase' }}>OCR Engine</div>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: '#FFFFFF', marginTop: '4px' }}>
                  {settingsData?.ocr_engine || 'RapidOCR ONNX (PP-OCRv4)'}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#10B981', marginTop: '2px' }}>Operational • CPU/ONNX</div>
              </div>

              <div style={{ padding: '16px', backgroundColor: '#070D19', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: '#94A3B8', fontWeight: '700', textTransform: 'uppercase' }}>Confidence Warning Floor</div>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: '#FFFFFF', marginTop: '4px' }}>
                  {settingsData?.min_confidence_warning_threshold || 70.0}%
                </div>
                <div style={{ fontSize: '0.75rem', color: '#F59E0B', marginTop: '2px' }}>Flags low-clarity text</div>
              </div>

              <div style={{ padding: '16px', backgroundColor: '#070D19', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: '#94A3B8', fontWeight: '700', textTransform: 'uppercase' }}>Product DB Dependency</div>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: '#10B981', marginTop: '4px' }}>
                  None (Autonomous)
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '2px' }}>Physical label is ground truth</div>
              </div>
            </div>
          </div>

          {/* Statutory Regulations Card */}
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <Scale size={20} color="#38BDF8" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF' }}>
                  Statutory Rule Enforcement Set ({settingsData?.active_rules_count || 12} Rules Active)
                </h3>
                <p style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                  Rules enforced under the Legal Metrology (Packaged Commodities) Rules, 2011
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { name: 'Rule 6(1)(a) — Identity & Postal Address', sev: 'HIGH', status: 'ACTIVE' },
                { name: 'Rule 6(1)(b) — Generic / Common Commodity Name', sev: 'HIGH', status: 'ACTIVE' },
                { name: 'Rule 6(1)(c) — Net Quantity in Metric SI Units', sev: 'HIGH', status: 'ACTIVE' },
                { name: 'Rule 6(1)(d) — Month & Year of Manufacture/Packing', sev: 'MEDIUM', status: 'ACTIVE' },
                { name: 'Rule 6(1)(da) — Best Before / Use-By Date', sev: 'MEDIUM', status: 'ACTIVE' },
                { name: 'Rule 6(1)(e) — Maximum Retail Price (MRP Incl. taxes)', sev: 'HIGH', status: 'ACTIVE' },
                { name: 'Rule 6(1)(ea) — Unit Sale Price (USP) Mathematical Check', sev: 'MEDIUM', status: 'ACTIVE' },
                { name: 'Rule 6(1)(f) — Consumer Care Grievance Redressal', sev: 'HIGH', status: 'ACTIVE' },
                { name: 'Rule 6(1)(h) — Country of Origin Declaration', sev: 'MEDIUM', status: 'ACTIVE' },
                { name: 'Rule 9 — Declaration Font Size & Letter Height', sev: 'HIGH', status: 'ACTIVE' },
                { name: 'Rule 24 — Non-Standard Qualifying Expressions', sev: 'MEDIUM', status: 'ACTIVE' },
                { name: 'Section 18 — Misleading / Deceptive Packaging Prohibition', sev: 'HIGH', status: 'ACTIVE' }
              ].map((r, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    backgroundColor: '#070D19',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)'
                  }}
                >
                  <span style={{ fontSize: '0.85rem', color: '#FFFFFF', fontWeight: '500' }}>{r.name}</span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className={`badge ${r.sev === 'HIGH' ? 'badge-noncompliant' : 'badge-review'}`} style={{ fontSize: '0.65rem' }}>
                      {r.sev}
                    </span>
                    <span className="badge badge-compliant" style={{ fontSize: '0.65rem' }}>
                      {r.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Database & Audit Card */}
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <Database size={20} color="#38BDF8" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF' }}>
                  Local Audit Trail Database
                </h3>
                <p style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                  Enforcement records persistence and tamper-evident PDF generation
                </p>
              </div>
            </div>

            <div style={{ fontSize: '0.82rem', color: '#94A3B8', lineHeight: 1.6 }}>
              <div>• <b>Storage Engine:</b> SQLite 3 with SQLAlchemy ORM (`safemetric.db`)</div>
              <div>• <b>Report Generator:</b> ReportLab Flowable Engine (A4 official certificate format)</div>
              <div>• <b>Security:</b> JWT Authorization with bcrypt password hashing</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
