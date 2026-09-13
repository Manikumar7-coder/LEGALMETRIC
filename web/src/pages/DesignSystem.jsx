import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Info, 
  ShieldCheck, 
  Scale, 
  Layers, 
  Download, 
  Search, 
  Trash2, 
  Plus, 
  Save, 
  ExternalLink,
  X,
  RefreshCw,
  Sliders,
  Sparkles
} from 'lucide-react';

export const DesignSystemPage = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [inputText, setInputText] = useState('Commodity Packaged Good');
  const [inputError, setInputError] = useState('Mandatory declaration missing under Rule 6(1)');
  const [hasError, setHasError] = useState(true);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '36px', maxWidth: '1120px', margin: '0 auto' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#38BDF8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Design System Foundation
          </span>
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: '800', color: '#FFFFFF', marginTop: '4px' }}>
          SAFEMETRIC GovTech UI Specification
        </h1>
        <p style={{ fontSize: '0.9rem', color: '#94A3B8', marginTop: '4px' }}>
          Comprehensive visual design foundation, design tokens, and components for Legal Metrology compliance enforcement.
        </p>
      </div>

      {/* 1. Typography Hierarchy */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>1. Typography Hierarchy</h3>
          <span className="badge badge-info">Font: Plus Jakarta Sans & JetBrains Mono</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', textTransform: 'uppercase', fontWeight: '700' }}>Display / Hero Title (2.25rem, 800)</div>
            <h1>Automated Legal Metrology Verification</h1>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', textTransform: 'uppercase', fontWeight: '700' }}>Heading 2 (1.75rem, 800)</div>
            <h2>Statutory Packaged Commodities Audit</h2>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', textTransform: 'uppercase', fontWeight: '700' }}>Heading 3 (1.25rem, 700)</div>
            <h3>Rule 6(1) Mandatory Declarations</h3>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', textTransform: 'uppercase', fontWeight: '700' }}>Heading 4 (1.05rem, 700)</div>
            <h4>Unit Sale Price & Metric Measurement Verification</h4>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', textTransform: 'uppercase', fontWeight: '700' }}>Body Text (0.95rem, 400, line-height: 1.6)</div>
            <p>
              Under Section 18 of the Legal Metrology Act, 2009, no person shall manufacture, pack, sell, distribute, deliver, offer, expose or possess for sale by wholesale or retail, any commodity in packaged form unless such package complies with standard statements.
            </p>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', textTransform: 'uppercase', fontWeight: '700' }}>Monospace Transcript / Code (JetBrains Mono)</div>
            <pre style={{ padding: '12px', backgroundColor: '#070F1E', borderRadius: '8px', border: '1px solid var(--border-subtle)', color: '#38BDF8', fontSize: '0.85rem' }}>
              RULE-REF: PCR-2011-R6-1-EA | CALC: MRP / NET_QTY | STATUS: PASS
            </pre>
          </div>
        </div>
      </div>

      {/* 2. Spacing Scale */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>2. Modular Spacing Scale (4px / 8px Base)</h3>
          <span className="badge badge-neutral">CSS Tokens: --space-1 to --space-16</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '12px' }}>
          {[
            { name: '--space-1', val: '4px' },
            { name: '--space-2', val: '8px' },
            { name: '--space-3', val: '12px' },
            { name: '--space-4', val: '16px' },
            { name: '--space-6', val: '24px' },
            { name: '--space-8', val: '32px' },
            { name: '--space-12', val: '48px' },
          ].map((s, idx) => (
            <div key={idx} style={{ padding: '12px', backgroundColor: '#070D19', borderRadius: '8px', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
              <div style={{ height: '8px', width: s.val, backgroundColor: '#38BDF8', margin: '0 auto 8px', borderRadius: '2px' }} />
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#FFFFFF' }}>{s.val}</div>
              <div style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '2px' }}>{s.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Buttons System */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>3. Buttons System</h3>
          <span className="badge badge-info">Interactive States & Elevation</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
            <button className="btn-primary">
              <Plus size={16} /> Primary Action
            </button>
            <button className="btn-secondary">
              <RefreshCw size={16} /> Secondary Action
            </button>
            <button className="btn-outline">
              <ExternalLink size={16} /> Outline Action
            </button>
            <button className="btn-success">
              <CheckCircle2 size={16} /> Statutory Approval
            </button>
            <button className="btn-danger">
              <Trash2 size={16} /> Destructive Action
            </button>
            <button className="btn-primary" disabled>
              Disabled Action
            </button>
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
            <span style={{ fontSize: '0.75rem', color: '#94A3B8', fontWeight: '600', textTransform: 'uppercase' }}>Sizes:</span>
            <button className="btn-primary btn-sm">Small (btn-sm)</button>
            <button className="btn-primary">Medium (Default)</button>
            <button className="btn-primary btn-lg">Large (btn-lg)</button>
          </div>
        </div>
      </div>

      {/* 4. Cards & Statistical Containers */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>4. Cards & Containers</h3>
          <span className="badge badge-neutral">Standard, Interactive, and Metric Cards</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div className="card card-stat">
            <div className="stat-header">
              <span className="stat-label">Total Commodity Audits</span>
              <span className="badge badge-info">Live</span>
            </div>
            <div className="stat-value">1,420</div>
            <div className="stat-subtext">Statutory inspections registered</div>
          </div>

          <div className="card card-stat" style={{ borderLeft: '3px solid var(--status-compliant)' }}>
            <div className="stat-header">
              <span className="stat-label">PCR Compliance Pass</span>
              <span className="badge badge-compliant">Standard</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--status-compliant)' }}>88.4%</div>
            <div className="stat-subtext">Conforms to PCR 2011</div>
          </div>

          <div className="card card-interactive" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={18} color="#38BDF8" />
              <h4 style={{ margin: 0 }}>Interactive Hover Card</h4>
            </div>
            <p style={{ fontSize: '0.82rem', margin: 0 }}>
              Features subtle elevation translateY, border brightening, and soft glow on hover.
            </p>
          </div>
        </div>
      </div>

      {/* 5. Forms & Inputs */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>5. Forms, Inputs & Controls</h3>
          <button 
            type="button" 
            onClick={() => setHasError(!hasError)} 
            className="btn-outline btn-sm"
          >
            Toggle Input Error State
          </button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
          <div className="form-group">
            <label className="form-label">Standard Text Input</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g. Commodity Brand Name" 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <span className="form-hint">Must match physical packaged commodity label.</span>
          </div>

          <div className="form-group">
            <label className="form-label">Validation Error State</label>
            <input 
              type="text" 
              className={`form-input ${hasError ? 'form-input-error' : ''}`}
              defaultValue="Invalid MRP string format"
            />
            {hasError && <span className="form-error-msg">{inputError}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">Select Dropdown</label>
            <select className="form-select">
              <option>Edible Oils & Fats (Rule 6(1))</option>
              <option>Pre-packed Grains & Cereals</option>
              <option>Packaged Bakery Products</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Disabled Input</label>
            <input 
              type="text" 
              className="form-input" 
              value="System Generated UID (Locked)" 
              disabled 
            />
          </div>
        </div>
      </div>

      {/* 6. Badges & Regulatory Status Indicators */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>6. Status Badges & Legal Metrology Indicators</h3>
          <span className="badge badge-info">Statutory Rule Verification</span>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span className="badge badge-compliant">
            <span className="status-dot status-dot-compliant" /> Compliant (Rule Passed)
          </span>
          <span className="badge badge-noncompliant">
            <span className="status-dot status-dot-noncompliant" /> Non-Compliant (Infraction)
          </span>
          <span className="badge badge-review">
            <span className="status-dot status-dot-review" /> Review Required (Low Conf.)
          </span>
          <span className="badge badge-info">Information</span>
          <span className="badge badge-neutral">Archived / Neutral</span>
        </div>
      </div>

      {/* 7. Tables Design */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0 }}>7. Responsive Data Table</h3>
            <p style={{ fontSize: '0.78rem', color: '#94A3B8', marginTop: '2px' }}>
              Statutory declaration audit representation with optical recognition confidence
            </p>
          </div>
          <span className="badge badge-neutral">Scrollable on Mobile</span>
        </div>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mandatory Declaration</th>
                <th>Extracted Value</th>
                <th>Status</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: '600', color: '#FFFFFF' }}>RULE 6(1)(B) GENERIC NAME</td>
                <td style={{ color: '#CBD5E1' }}>Edible Sunflower Oil</td>
                <td><span className="badge badge-compliant">Found</span></td>
                <td style={{ fontWeight: '700', color: '#10B981' }}>98.5%</td>
              </tr>
              <tr>
                <td style={{ fontWeight: '600', color: '#FFFFFF' }}>RULE 6(1)(E) MAXIMUM RETAIL PRICE</td>
                <td style={{ color: '#CBD5E1' }}>Rs. 185 (Incl. of all taxes)</td>
                <td><span className="badge badge-compliant">Found</span></td>
                <td style={{ fontWeight: '700', color: '#10B981' }}>97.2%</td>
              </tr>
              <tr>
                <td style={{ fontWeight: '600', color: '#FFFFFF' }}>RULE 6(1)(EA) UNIT SALE PRICE</td>
                <td style={{ color: '#F87171' }}>Missing / Non-standard</td>
                <td><span className="badge badge-noncompliant">Missing</span></td>
                <td style={{ fontWeight: '700', color: '#EF4444' }}>—</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 8. Alerts & Statutory Notices */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>8. Alerts & Banners</h3>
          <span className="badge badge-neutral">Semantic Alert Colors</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="alert alert-success">
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <b>Statutory Verification Complete:</b> All mandatory declarations under Rule 6(1) of the Legal Metrology (Packaged Commodities) Rules, 2011 have been successfully detected.
            </div>
          </div>

          <div className="alert alert-error">
            <XCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <b>Compliance Infraction Detected:</b> Missing Unit Sale Price (USP) declaration in violation of Rule 6(1)(ea). Recommended action: Issue Form-1 inquiry notice.
            </div>
          </div>

          <div className="alert alert-warning">
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <b>Low Optical Confidence Warning:</b> Packaging image resolution or illumination is sub-optimal. Review bounding box coordinates manually.
            </div>
          </div>

          <div className="alert alert-info">
            <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <b>Statutory Information:</b> Inspection reports are archived locally in SQLite and encrypted under officer security credentials.
            </div>
          </div>
        </div>
      </div>

      {/* 9. Modal / Dialog Preview */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>9. Modal / Dialog Styles</h3>
          <button 
            type="button" 
            onClick={() => setModalOpen(true)} 
            className="btn-primary btn-sm"
          >
            Launch Interactive Modal
          </button>
        </div>
        <p style={{ margin: 0 }}>
          Click the button above to trigger an accessible, responsive modal dialog window with backdrop blur and header/body/footer structure.
        </p>

        {modalOpen && (
          <div className="modal-backdrop" onClick={() => setModalOpen(false)}>
            <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={20} color="#38BDF8" />
                  <h4 className="modal-title">Statutory Audit Confirmation</h4>
                </div>
                <button type="button" onClick={() => setModalOpen(false)} className="btn-icon">
                  <X size={18} />
                </button>
              </div>
              <div className="modal-body">
                <p>
                  You are about to finalize official Legal Metrology compliance record <b>#INS-VERIFY</b>. This record will generate a signed, tamper-evident ReportLab PDF inspection certificate.
                </p>
                <div style={{ marginTop: '14px', padding: '12px', backgroundColor: '#070D19', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.78rem', color: '#38BDF8', fontWeight: '700' }}>GOVERNMENT ENFORCEMENT DISPATCH</div>
                  <div style={{ fontSize: '0.82rem', color: '#CBD5E1', marginTop: '4px' }}>
                    Authorizing Officer: Inspector Rajesh Kumar (Delhi Zone)
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="button" onClick={() => setModalOpen(false)} className="btn-primary">
                  Confirm & Export Certificate
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 10. Loading & Skeleton States */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>10. Loading & Skeleton Shimmer States</h3>
          <span className="badge badge-info">Asynchronous Visual Feedback</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {/* Spinner */}
          <div className="loading-spinner-container" style={{ backgroundColor: '#070D19', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div className="animate-spin" style={{ width: '28px', height: '28px', border: '3px solid #1E2E4E', borderTopColor: '#3B82F6', borderRadius: '50%' }} />
            <span>Analyzing commodity optical declarations...</span>
          </div>

          {/* Skeleton Shimmer */}
          <div style={{ padding: '20px', backgroundColor: '#070D19', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div className="skeleton skeleton-title" />
            <div className="skeleton skeleton-text" style={{ width: '90%' }} />
            <div className="skeleton skeleton-text" style={{ width: '75%' }} />
            <div className="skeleton skeleton-text" style={{ width: '60%' }} />
          </div>
        </div>
      </div>

      {/* 11. Error & Empty States */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>11. Error & Empty State Layouts</h3>
          <span className="badge badge-neutral">Graceful Fallbacks</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          <div className="error-state" style={{ backgroundColor: '#070D19', borderRadius: '8px', border: '1px solid var(--border-subtle)', width: '100%' }}>
            <div className="error-state-icon">
              <AlertTriangle size={28} />
            </div>
            <h4 style={{ margin: 0, color: '#FFFFFF' }}>Inspection Record Inaccessible</h4>
            <p style={{ margin: 0, fontSize: '0.82rem' }}>
              The requested inspection record could not be loaded from the local database.
            </p>
            <button className="btn-secondary btn-sm" style={{ marginTop: '8px' }}>
              Retry Inspection Query
            </button>
          </div>

          <div className="empty-state" style={{ backgroundColor: '#070D19', borderRadius: '8px', border: '1px solid var(--border-subtle)', width: '100%' }}>
            <div className="empty-state-icon">
              <Layers size={28} />
            </div>
            <h4 style={{ margin: 0, color: '#FFFFFF' }}>No Infractions Found</h4>
            <p style={{ margin: 0, fontSize: '0.82rem' }}>
              Commodity label matches all legal declaration requirements under PCR 2011.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DesignSystemPage;
