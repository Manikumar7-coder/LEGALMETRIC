import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  FileDown, 
  Eye, 
  Trash2, 
  Calendar, 
  Scale, 
  Layers, 
  FileText,
  Clock,
  Shield,
  ExternalLink
} from 'lucide-react';
import { inspectionAPI, reportAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const InspectionDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [inspection, setInspection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('declarations'); // 'declarations', 'violations', 'raw_ocr'
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetchRecord = async () => {
      try {
        const data = await inspectionAPI.getById(id);
        setInspection(data);
      } catch (err) {
        setError('Failed to fetch inspection record. Please verify the inspection ID.');
      } finally {
        setLoading(false);
      }
    };
    fetchRecord();
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete inspection record #INS-${id}?`)) {
      return;
    }
    setDeleting(true);
    try {
      await inspectionAPI.delete(id);
      navigate('/history');
    } catch (err) {
      alert('Failed to delete inspection record.');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: 'var(--text-secondary)', gap: '12px' }}>
        <div className="animate-spin" style={{ width: '24px', height: '24px', border: '3px solid #1E2E4E', borderTopColor: '#3B82F6', borderRadius: '50%' }} />
        Retrieving Statutory Inspection Record #{id}...
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="card" style={{ maxWidth: '600px', margin: '40px auto', textAlign: 'center', padding: '40px 24px' }}>
        <AlertTriangle size={36} color="#EF4444" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-primary)' }}>{error || 'Inspection Record Not Found'}</h3>
        <Link to="/history" className="btn-primary" style={{ marginTop: '20px' }}>
          Back to Inspection History
        </Link>
      </div>
    );
  }

  const isCompliant = inspection.compliance_status === 'COMPLIANT';
  const isNonCompliant = inspection.compliance_status === 'NON-COMPLIANT';
  const statusColor = isCompliant ? '#10B981' : (isNonCompliant ? '#EF4444' : '#F59E0B');

  const pdfDownloadUrl = reportAPI.getDownloadUrl(inspection.id);
  const imageUrl = inspectionAPI.getImageUrl(inspection.id);
  const violations = inspection.violations || [];
  const fields = inspection.fields || [];

  return (
    <div style={{ maxWidth: '1120px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Breadcrumb & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <Link to="/history" style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: '500' }}>
          <ArrowLeft size={16} /> Back to Inspection Records
        </Link>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to={`/result/${inspection.id}`} className="btn-secondary" style={{ fontSize: '0.82rem' }}>
            <Eye size={16} /> Interactive Evidence Viewer
          </Link>
          <a
            href={pdfDownloadUrl}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
            style={{ fontSize: '0.82rem', padding: '8px 18px' }}
          >
            <FileDown size={16} /> Download PDF Certificate
          </a>
          {isAdmin && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="btn-secondary"
              style={{ fontSize: '0.82rem', color: '#EF4444', borderColor: 'rgba(239, 68, 68, 0.4)' }}
              title="Delete Record (Admin Only)"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Hero Record Banner */}
      <div className="card" style={{
        padding: '24px 30px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '20px',
        borderLeft: `4px solid ${statusColor}`
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            overflow: 'hidden',
            backgroundColor: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            flexShrink: 0
          }}>
            <img
              src={imageUrl}
              alt={inspection.product_name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onError={(e) => { e.currentTarget.style.display = 'none'; }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-primary)', letterSpacing: '0.05em' }}>
                RECORD REF: #INS-{inspection.id}
              </span>
              <span className={`badge ${isCompliant ? 'badge-compliant' : (isNonCompliant ? 'badge-noncompliant' : 'badge-review')}`}>
                {inspection.compliance_status}
              </span>
            </div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px', lineHeight: 1.2 }}>
              {inspection.product_name}
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={14} /> {new Date(inspection.inspection_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} /> {new Date(inspection.inspection_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Shield size={14} /> Quality Score: <b>{inspection.quality_score}%</b>
              </span>
            </div>
          </div>
        </div>

        {/* Score Ring */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Compliance Rating
            </div>
            <div style={{ fontSize: '2rem', fontWeight: '900', color: statusColor, lineHeight: 1 }}>
              {inspection.compliance_score}%
            </div>
          </div>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '50%',
            background: `conic-gradient(${statusColor} ${inspection.compliance_score * 3.6}deg, #1E2E4E 0deg)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{ width: '34px', height: '34px', borderRadius: '50%', backgroundColor: 'var(--bg-canvas)' }} />
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-subtle)',
        gap: '12px'
      }}>
        {[
          { id: 'declarations', label: `Statutory Declarations (${fields.length})`, icon: Layers },
          { id: 'violations', label: `Compliance Infractions (${violations.length})`, icon: AlertTriangle },
          { id: 'raw_ocr', label: 'Raw Optical OCR Stream', icon: FileText },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 18px',
                background: 'transparent',
                borderBottom: isActive ? '2px solid #3B82F6' : '2px solid transparent',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: isActive ? '700' : '500',
                fontSize: '0.88rem'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Contents */}
      {activeTab === 'declarations' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              Extracted Declarations under Packaged Commodities Rules, 2011
            </h3>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Statutory Requirement</th>
                <th>Detected Declaration</th>
                <th>Compliance Status</th>
                <th>Optical Confidence</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((f, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {f.field_name.replace(/_/g, ' ').toUpperCase()}
                  </td>
                  <td style={{ color: f.extracted_value ? 'var(--text-secondary)' : 'var(--text-muted)', maxWidth: '380px', wordBreak: 'break-word' }}>
                    {f.extracted_value || '— Not Detected —'}
                  </td>
                  <td>
                    <span className={`badge ${f.status === 'Found' ? 'badge-compliant' : (f.status === 'Low Confidence' ? 'badge-review' : 'badge-noncompliant')}`}>
                      {f.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: '600', color: f.confidence >= 90 ? '#10B981' : (f.confidence >= 70 ? '#F59E0B' : '#EF4444') }}>
                    {f.status === 'Missing' ? '—' : `${f.confidence}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'violations' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {violations.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
              <CheckCircle2 size={36} color="#10B981" style={{ margin: '0 auto 10px' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>Full Statutory Compliance Verified</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                No violations detected under the Legal Metrology (Packaged Commodities) Rules, 2011.
              </p>
            </div>
          ) : (
            violations.map((v, idx) => (
              <div
                key={idx}
                className="card"
                style={{
                  padding: '18px 20px',
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: '800', color: '#EF4444', textTransform: 'uppercase' }}>
                      {v.field}
                    </span>
                    <h4 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                      {v.issue}
                    </h4>
                  </div>
                  <span className={`badge ${v.severity === 'HIGH' ? 'badge-noncompliant' : 'badge-review'}`}>
                    {v.severity} SEVERITY
                  </span>
                </div>

                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.4 }}>
                  <div style={{ color: 'var(--accent-primary)', fontWeight: '600' }}>Legal Metrology Citation: {v.rule_reference}</div>
                  <div style={{ marginTop: '2px' }}>Corrective Recommendation: {v.recommendation}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'raw_ocr' && (
        <div className="card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
            Optical Character Recognition Raw Transcript
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Unprocessed optical text recognition extracted directly by the vision engine from the physical packaging label:
          </p>
          <pre style={{
            padding: '16px',
            backgroundColor: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            color: '#A5F3FC',
            fontSize: '0.85rem',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            overflowX: 'auto'
          }}>
            {inspection.raw_ocr_text || 'No OCR transcript available.'}
          </pre>
        </div>
      )}
    </div>
  );
};

export default InspectionDetailsPage;
