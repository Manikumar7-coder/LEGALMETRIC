import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  AlertCircle,
  FileDown, 
  ArrowLeft, 
  Scan, 
  Shield, 
  Scale, 
  Layers, 
  ExternalLink,
  Info,
  FileText,
  Crosshair,
  Eye,
  Sparkles,
  BookOpen,
  Calculator,
  ChevronDown,
  ChevronUp,
  Type
} from 'lucide-react';
import { inspectionAPI, reportAPI } from '../services/api';
import EvidenceViewer from '../components/EvidenceViewer';

export const ResultPage = () => {
  const { id } = useParams();
  const [inspection, setInspection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [activeRuleFilter, setActiveRuleFilter] = useState('ALL');
  const [showScoreBreakdown, setShowScoreBreakdown] = useState(false);

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const data = await inspectionAPI.getById(id);
        setInspection(data);
      } catch (err) {
        setError('Failed to fetch inspection record. Please verify the inspection ID.');
      } finally {
        setLoading(false);
      }
    };
    fetchResult();
  }, [id]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: 'var(--text-secondary)', gap: '12px' }}>
        <div className="animate-spin" style={{ width: '24px', height: '24px', border: '3px solid #1E2E4E', borderTopColor: '#3B82F6', borderRadius: '50%' }} />
        Retrieving Legal Metrology Compliance Evaluation...
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="card" style={{ maxWidth: '600px', margin: '40px auto', textAlign: 'center', padding: '40px 24px' }}>
        <AlertTriangle size={36} color="#EF4444" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-primary)' }}>{error || 'Inspection Not Found'}</h3>
        <Link to="/dashboard" className="btn-primary" style={{ marginTop: '20px' }}>
          Return to Dashboard
        </Link>
      </div>
    );
  }

  // 1. Overall Compliance Status: Normalize to clear statuses
  const rawStatus = (inspection.status || inspection.normalized_status || inspection.compliance_status || '').toUpperCase().trim();
  let displayStatus = 'Needs Review';
  let statusColor = '#F59E0B';
  let statusBg = 'rgba(245, 158, 11, 0.12)';
  let statusBorder = '#D97706';
  let StatusIcon = AlertTriangle;

  if (rawStatus.includes('NON')) {
    displayStatus = 'Non-Compliant';
    statusColor = '#EF4444';
    statusBg = 'rgba(239, 68, 68, 0.12)';
    statusBorder = '#DC2626';
    StatusIcon = XCircle;
  } else if (rawStatus.includes('PARTIAL')) {
    displayStatus = 'Partially Compliant';
    statusColor = '#F59E0B';
    statusBg = 'rgba(245, 158, 11, 0.12)';
    statusBorder = '#D97706';
    StatusIcon = AlertCircle;
  } else if (rawStatus.includes('REVIEW') || rawStatus.includes('NEEDS')) {
    displayStatus = 'Needs Review';
    statusColor = 'var(--accent-primary)';
    statusBg = 'rgba(56, 189, 248, 0.12)';
    statusBorder = '#0284C7';
    StatusIcon = AlertTriangle;
  } else if (rawStatus.includes('COMPLIANT')) {
    displayStatus = 'Compliant';
    statusColor = '#10B981';
    statusBg = 'rgba(16, 185, 129, 0.12)';
    statusBorder = '#059669';
    StatusIcon = CheckCircle2;
  }

  // 2. Compliance Score
  const complianceScore = typeof inspection.compliance_score === 'number' 
    ? Math.round(inspection.compliance_score * 10) / 10 
    : 0;

  // Extracted Declarations and Lists
  const ext = inspection.extracted_data || {};
  const violations = inspection.violations || [];
  const fields = inspection.fields || [];
  const recommendations = inspection.recommendations || [];
  const legalReferences = inspection.legal_references || inspection.rule_results || [];
  const scoreBreakdown = inspection.score_breakdown || null;

  // 3, 4, 5. Check Counters
  const passedCount = typeof inspection.passed_count === 'number'
    ? inspection.passed_count
    : fields.filter(f => f.status === 'Found').length;

  const failedCount = typeof inspection.failed_count === 'number'
    ? inspection.failed_count
    : violations.length;

  const needsReviewCount = typeof inspection.needs_review_count === 'number'
    ? inspection.needs_review_count
    : fields.filter(f => f.status === 'Low Confidence').length;

  const pdfDownloadUrl = reportAPI.getDownloadUrl(inspection.id, 'pdf');
  const docxDownloadUrl = reportAPI.getDownloadUrl(inspection.id, 'docx');
  const csvDownloadUrl = reportAPI.getDownloadUrl(inspection.id, 'csv');
  const imageUrl = inspectionAPI.getImageUrl(inspection.id);

  // Filter legal references for tabbed view
  const filteredRules = legalReferences.filter(r => {
    if (activeRuleFilter === 'ALL') return true;
    if (activeRuleFilter === 'PASS') return r.status === 'PASS';
    if (activeRuleFilter === 'FAIL') return r.status === 'FAIL';
    if (activeRuleFilter === 'NEEDS_REVIEW') return r.status === 'NEEDS_REVIEW';
    return true;
  });

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header & Breadcrumbs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <Link to="/history" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            <ArrowLeft size={14} /> Back to Inspections
          </Link>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '900', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Inspection #{inspection.inspection_id || inspection.id}
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Conducted on {new Date(inspection.created_at || inspection.inspection_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <Link to={`/inspection/${inspection.id}`} className="btn-secondary" style={{ fontSize: '0.82rem' }}>
            <FileText size={16} /> Audit Log
          </Link>
          <Link to="/scan" className="btn-secondary" style={{ fontSize: '0.82rem' }}>
            <Scan size={16} /> Scan Next Commodity
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--bg-canvas)', padding: '2px 4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-secondary)', padding: '0 6px' }}>EXPORT:</span>
            <a
              href={pdfDownloadUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-primary"
              style={{ fontSize: '0.78rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '5px' }}
              title="Official PDF Statutory Report"
            >
              <FileDown size={14} /> PDF
            </a>
            <a
              href={docxDownloadUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary"
              style={{ fontSize: '0.78rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '5px' }}
              title="Editable Microsoft Word Report Draft"
            >
              <FileText size={14} /> Word (.docx)
            </a>
            <a
              href={csvDownloadUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary"
              style={{ fontSize: '0.78rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '5px' }}
              title="Spreadsheet CSV Audit Export"
            >
              <Scale size={14} /> CSV
            </a>
          </div>
        </div>
      </div>

      {/* 1. Overall Compliance Status & Hero Result Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${statusBg} 0%, var(--bg-card) 100%)`,
        border: `1px solid ${statusBorder}`,
        borderRadius: 'var(--radius-xl)',
        padding: '32px 36px',
        boxShadow: `0 8px 32px ${statusColor}22, inset 0 1px 0 rgba(255,255,255,0.05)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '24px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle grid background for the banner */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)',
          backgroundSize: '20px 20px', pointerEvents: 'none', zIndex: 0
        }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', zIndex: 1 }}>
          <div style={{
            width: '68px',
            height: '68px',
            borderRadius: '20px',
            backgroundColor: statusColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 6px 24px ${statusColor}66`
          }}>
            <StatusIcon size={40} color="#FFFFFF" />
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: '800', letterSpacing: '0.08em', textTransform: 'uppercase', color: statusColor }}>
              STATUTORY COMPLIANCE DETERMINATION
            </div>
            <h1 style={{ fontSize: '2.4rem', fontWeight: '900', color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              {displayStatus}
            </h1>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Commodity: <b style={{ color: 'var(--text-primary)' }}>{inspection.product_name}</b> • Record Ref: <b>#INS-{inspection.id}</b>
            </p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '6px', fontStyle: 'italic' }}>
              * Evaluated per the Legal Metrology (Packaged Commodities) Rules, 2011
            </p>
          </div>
        </div>

        {/* Score Ring / Gauge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '12px 24px',
          backgroundColor: 'var(--bg-canvas)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              COMPLIANCE SCORE
            </div>
            <div style={{ fontSize: '2.4rem', fontWeight: '900', color: statusColor, lineHeight: 1, marginTop: '2px' }}>
              {complianceScore}%
            </div>
          </div>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            background: `conic-gradient(${statusColor} ${complianceScore * 3.6}deg, #1E2E4E 0deg)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'var(--bg-canvas)' }} />
          </div>
        </div>
      </div>

      {/* 2, 3, 4, 5. Metrics Counters Bar (Score, Passed, Failed, Needs Review) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        <div className="card" style={{ padding: '20px', borderLeft: `4px solid ${statusColor}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Compliance Score
            </span>
            <Shield size={18} color={statusColor} />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--text-primary)', marginTop: '6px' }}>
            {complianceScore}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Legal Metrology compliance rating
          </div>
        </div>

        <div className="card" style={{ padding: '20px', borderLeft: '4px solid #10B981' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Passed Checks
            </span>
            <CheckCircle2 size={18} color="#10B981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#10B981', marginTop: '6px' }}>
            {passedCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Statutory requirements fulfilled
          </div>
        </div>

        <div className="card" style={{ padding: '20px', borderLeft: '4px solid #EF4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Failed Checks
            </span>
            <XCircle size={18} color="#EF4444" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#EF4444', marginTop: '6px' }}>
            {failedCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Statutory infractions identified
          </div>
        </div>

        <div className="card" style={{ padding: '20px', borderLeft: '4px solid #F59E0B' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Needs Review
            </span>
            <AlertTriangle size={18} color="#F59E0B" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#F59E0B', marginTop: '6px' }}>
            {needsReviewCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Requires physical / optical verification
          </div>
        </div>
      </div>

      {/* Compliance Score Transparency & Calculation Details */}
      {scoreBreakdown && (
        <div className="card" style={{
          backgroundColor: 'var(--bg-canvas)',
          border: '1px solid var(--border-subtle)',
          padding: '18px 24px',
          borderRadius: 'var(--radius-lg)'
        }}>
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              userSelect: 'none'
            }}
            onClick={() => setShowScoreBreakdown(prev => !prev)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                backgroundColor: 'var(--status-info-bg)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Calculator size={18} color="#38BDF8" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.95rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                    Statutory Scoring Audit & Mathematical Transparency
                  </span>
                  <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                    Deterministic & Explainable
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {scoreBreakdown.points_earned} earned / {scoreBreakdown.points_possible} applicable points • {scoreBreakdown.total_applicable_rules} rules evaluated ({scoreBreakdown.not_applicable_rules} not applicable excluded from denominator)
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)', fontSize: '0.8rem', fontWeight: '600' }}>
              <span>{showScoreBreakdown ? 'Hide Calculation' : 'View Formula & Breakdown'}</span>
              {showScoreBreakdown ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>
          </div>

          {showScoreBreakdown && (
            <div style={{ marginTop: '18px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Formula & Explanation */}
              <div style={{
                padding: '12px 16px',
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: '800', color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
                  <Scale size={14} /> Statutory Scoring Formula
                </div>
                <code style={{ fontSize: '0.85rem', color: 'var(--bg-canvas)', backgroundColor: 'var(--bg-canvas)', padding: '8px 12px', borderRadius: '6px', border: '1px solid #1E293B', fontFamily: 'monospace' }}>
                  {scoreBreakdown.formula}
                </code>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  {scoreBreakdown.explanation}
                </div>
              </div>

              {/* Weighting Principles Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-canvas)', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
                  <div style={{ fontSize: '0.7rem', color: '#10B981', fontWeight: '700', textTransform: 'uppercase' }}>PASS (100% Full Credit)</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>{scoreBreakdown.passed_rules} rules</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Weight: 1.0 pt each</div>
                </div>
                <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-canvas)', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
                  <div style={{ fontSize: '0.7rem', color: '#F59E0B', fontWeight: '700', textTransform: 'uppercase' }}>NEEDS REVIEW (50% Provisional)</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>{scoreBreakdown.needs_review_rules} rules</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Optical uncertainty: 0.5 pt each</div>
                </div>
                <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-canvas)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
                  <div style={{ fontSize: '0.7rem', color: '#EF4444', fontWeight: '700', textTransform: 'uppercase' }}>FAIL (0% No Credit)</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>{scoreBreakdown.failed_rules} rules</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Statutory non-compliance: 0.0 pt</div>
                </div>
                <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-canvas)', borderRadius: '6px', border: '1px solid #1E293B' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: '700', textTransform: 'uppercase' }}>NOT APPLICABLE (Excluded)</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>{scoreBreakdown.not_applicable_rules} rules</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>0.0 max pts (zero denominator impact)</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 10. Statutory Recommendations & Corrective Actions */}
      <div className="card" style={{
        borderColor: recommendations.some(r => r.urgency === 'Immediate') ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-subtle)',
        backgroundColor: 'var(--bg-card)',
        padding: '24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={22} color="#38BDF8" />
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                Statutory Recommendations & Actionable Guidance
              </h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Prescribed compliance directives under Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011
              </p>
            </div>
          </div>
          <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
            {recommendations.length} Action Items
          </span>
        </div>

        {recommendations.length === 0 ? (
          <div style={{ padding: '18px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            No specific corrective actions required. All statutory declarations conform to metrology standards.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {recommendations.map((rec, idx) => {
              const isUrgent = rec.urgency === 'Immediate' || rec.urgency === 'High';
              return (
                <div
                  key={idx}
                  style={{
                    padding: '16px 20px',
                    backgroundColor: 'var(--bg-canvas)',
                    borderLeft: `4px solid ${isUrgent ? '#EF4444' : (rec.urgency === 'Moderate' ? '#F59E0B' : '#10B981')}`,
                    borderRadius: 'var(--radius-md)',
                    borderTop: '1px solid var(--border-subtle)',
                    borderRight: '1px solid var(--border-subtle)',
                    borderBottom: '1px solid var(--border-subtle)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          color: isUrgent ? '#EF4444' : 'var(--accent-primary)'
                        }}>
                          {rec.action_type || 'Corrective Action'}
                        </span>
                        {rec.field && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                            • Field: <b style={{ color: 'var(--text-secondary)' }}>{rec.field}</b>
                          </span>
                        )}
                      </div>
                      <h4 style={{ fontSize: '0.98rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '4px' }}>
                        {rec.title}
                      </h4>
                    </div>

                    <span className={`badge ${
                      rec.urgency === 'Immediate' ? 'badge-noncompliant' : (rec.urgency === 'High' ? 'badge-review' : 'badge-compliant')
                    }`} style={{ fontSize: '0.68rem' }}>
                      {rec.urgency ? `${rec.urgency.toUpperCase()} URGENCY` : 'ACTION REQUIRED'}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: 1.45 }}>
                    {rec.detail}
                  </p>

                  {rec.legal_reference && (
                    <div style={{ marginTop: '8px', fontSize: '0.76rem', color: 'var(--accent-primary)', fontWeight: '600' }}>
                      Legal Citation: {rec.legal_reference}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Extracted Declarations Key Summary Cards */}
      <div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} color="#38BDF8" /> Extracted Statutory Declarations
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
          gap: '14px'
        }}>
          {[
            { label: 'Product / Brand Name', val: ext.product_name?.value || inspection.product_name, stat: ext.product_name?.status },
            { label: 'Generic / Common Name (Rule 6(1)(b))', val: ext.generic_name?.value, stat: ext.generic_name?.status },
            { label: 'Maximum Retail Price (MRP)', val: ext.mrp?.value, stat: ext.mrp?.status },
            { label: 'Unit Sale Price (USP) (Rule 6(1)(ea))', val: ext.unit_sale_price?.value, stat: ext.unit_sale_price?.status },
            { label: 'Net Quantity', val: ext.net_quantity?.value, stat: ext.net_quantity?.status },
            { label: 'Manufacturing Date', val: ext.manufacturing_date?.value, stat: ext.manufacturing_date?.status },
            { label: 'Best Before / Use By', val: ext.best_before?.value, stat: ext.best_before?.status },
            { label: 'Manufacturer Name', val: ext.manufacturer_name?.value, stat: ext.manufacturer_name?.status },
            { label: 'Manufacturer Address', val: ext.manufacturer_address?.value, stat: ext.manufacturer_address?.status },
            { label: 'Consumer Care Helpline', val: ext.consumer_care?.value, stat: ext.consumer_care?.status },
            { label: 'Country of Origin', val: ext.country_of_origin?.value, stat: ext.country_of_origin?.status },
            { label: 'Batch / Lot Number', val: ext.batch_number?.value, stat: ext.batch_number?.status },
          ].map((item, idx) => (
            <div key={idx} className="card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                  {item.label}
                </span>
                <span className={`badge ${item.stat === 'Found' ? 'badge-compliant' : (item.stat === 'Low Confidence' ? 'badge-review' : 'badge-noncompliant')}`} style={{ fontSize: '0.65rem' }}>
                  {item.stat || 'Missing'}
                </span>
              </div>
              <div style={{
                fontSize: '0.9rem',
                fontWeight: '600',
                color: item.val ? 'var(--text-primary)' : 'var(--text-muted)',
                marginTop: '8px',
                wordBreak: 'break-word',
                lineHeight: 1.3
              }}>
                {item.val || '— Not Detected —'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 7. Statutory Violations & Compliance Issues */}
      {violations.length > 0 ? (
        <div className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', backgroundColor: 'var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <XCircle size={22} color="#EF4444" />
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                Compliance Issues & Statutory Violations ({violations.length})
              </h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--status-noncompliant)' }}>
                Infractions detected under the Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {violations.map((v, idx) => {
              const isSelected = selectedViolation && (selectedViolation.rule_id === v.rule_id || selectedViolation.field === v.field);
              return (
                <div
                  key={idx}
                  onClick={() => {
                    setSelectedViolation(v);
                    document.getElementById('evidence-viewer')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  style={{
                    padding: '16px',
                    backgroundColor: isSelected ? 'rgba(239, 68, 68, 0.14)' : 'var(--bg-canvas)',
                    border: isSelected ? '2px solid #EF4444' : '1px solid rgba(239, 68, 68, 0.25)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <span style={{ fontSize: '0.7rem', fontWeight: '800', color: '#EF4444', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {v.field}
                      </span>
                      <h4 style={{ fontSize: '0.98rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                        <span style={{ color: 'var(--status-noncompliant)' }}>Evidence: </span>{v.issue}
                      </h4>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`badge ${v.severity === 'CRITICAL' || v.severity === 'HIGH' ? 'badge-noncompliant' : 'badge-review'}`}>
                        {v.severity || 'HIGH'} SEVERITY
                      </span>
                      <button
                        type="button"
                        className="btn-secondary"
                        style={{
                          padding: '5px 12px',
                          fontSize: '0.72rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                          backgroundColor: isSelected ? '#EF4444' : 'var(--border-subtle)',
                          color: 'var(--text-primary)',
                          borderColor: isSelected ? '#EF4444' : 'var(--border-subtle)'
                        }}
                      >
                        <Crosshair size={13} /> View on Image
                      </button>
                    </div>
                  </div>

                  <div style={{ marginTop: '10px', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: '600' }}>
                      Legal Citation: {v.rule_reference || v.rule_id}
                    </div>
                    {v.recommendation && (
                      <div style={{ marginTop: '3px', color: 'var(--text-secondary)' }}>
                        <b>Advisory:</b> {v.recommendation}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="card" style={{
          borderColor: 'rgba(16, 185, 129, 0.4)',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          padding: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px'
        }}>
          <CheckCircle2 size={32} color="#10B981" />
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--text-primary)' }}>
              Zero Statutory Violations Detected
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              All verified label declarations meet the requirements of the Legal Metrology (Packaged Commodities) Rules, 2011.
            </p>
          </div>
        </div>
      )}

      {/* 6. Extracted Declaration Audit Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            Statutory Declaration Audit Table
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Detailed breakdown of OCR extracted values and optical recognition confidence
          </p>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Field / Requirement</th>
              <th>Detected Value</th>
              <th>Compliance Status</th>
              <th>OCR Confidence</th>
              <th>Rule 7 Font Size</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((f, idx) => {
              const fontFld = inspection.font_analysis?.fields?.[f.field_name];
              return (
                <tr key={idx}>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {f.field_name.replace(/_/g, ' ').toUpperCase()}
                  </td>
                  <td style={{ color: f.extracted_value ? 'var(--text-secondary)' : 'var(--text-muted)', maxWidth: '340px', wordBreak: 'break-word' }}>
                    {f.extracted_value || '—'}
                  </td>
                  <td>
                    <span className={`badge ${
                      f.status === 'Found' ? 'badge-compliant' : (f.status === 'Low Confidence' ? 'badge-review' : 'badge-noncompliant')
                    }`}>
                      {f.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: '600', color: f.confidence >= 90 ? '#10B981' : (f.confidence >= 70 ? '#F59E0B' : '#EF4444') }}>
                    {f.status === 'Missing' ? '—' : `${f.confidence}%`}
                  </td>
                  <td>
                    {fontFld?.char_height_mm ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                        <span style={{
                          fontWeight: '800',
                          color: fontFld.status === 'PASS' ? '#10B981' : (fontFld.status === 'FAIL' ? '#EF4444' : '#F59E0B')
                        }}>
                          {fontFld.char_height_mm} mm
                        </span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                          (min {fontFld.min_required_mm} mm)
                        </span>
                        <span className={`badge ${
                          fontFld.status === 'PASS' ? 'badge-compliant' : (fontFld.status === 'FAIL' ? 'badge-noncompliant' : 'badge-review')
                        }`} style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                          {fontFld.status}
                        </span>
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>N/A</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 6b. Font Size & Readability Analysis Card (Rule 7, PCR 2011) */}
      {inspection.font_analysis && (
        <div className="card" style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: inspection.font_analysis.overall_status === 'FAIL' ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-subtle)',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Type size={22} color="#38BDF8" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                    Font Size & Label Readability Analysis
                  </h3>
                  <span className={`badge ${
                    inspection.font_analysis.overall_status === 'PASS'
                      ? 'badge-compliant'
                      : (inspection.font_analysis.overall_status === 'FAIL' ? 'badge-noncompliant' : 'badge-review')
                  }`}>
                    {inspection.font_analysis.overall_status}
                  </span>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Statutory character & numeral height verification under Rule 7(1)-(3) & Tables I & II, PCR 2011
                </p>
              </div>
            </div>

            {/* Methodology & Scale Metadata */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
                Scale: {inspection.font_analysis.pixel_to_mm_ratio ? `${inspection.font_analysis.pixel_to_mm_ratio} mm/px` : 'Dynamic'}
              </span>
              <span className={`badge ${inspection.font_analysis.confidence >= 0.8 ? 'badge-compliant' : 'badge-review'}`} style={{ fontSize: '0.72rem' }}>
                {Math.round(inspection.font_analysis.confidence * 100)}% Confidence ({inspection.font_analysis.estimation_method === 'user_calibrated_package_dimensions' ? 'User Calibrated' : 'Tier Heuristic'})
              </span>
            </div>
          </div>

          {/* Grid of Measured Font Fields */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px', marginTop: '12px' }}>
            {Object.entries(inspection.font_analysis.fields || {}).map(([key, fld]) => {
              const isP = fld.status === 'PASS';
              const isF = fld.status === 'FAIL';
              const bdColor = isP ? '#10B981' : (isF ? '#EF4444' : '#F59E0B');
              return (
                <div key={key} style={{
                  padding: '14px 16px',
                  backgroundColor: 'var(--bg-canvas)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  borderLeft: `4px solid ${bdColor}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      {fld.field_label}
                    </span>
                    <span className={`badge ${isP ? 'badge-compliant' : (isF ? 'badge-noncompliant' : 'badge-review')}`} style={{ fontSize: '0.65rem' }}>
                      {fld.status}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
                    <span style={{ fontSize: '1.4rem', fontWeight: '900', color: bdColor }}>
                      {fld.char_height_mm ? `${fld.char_height_mm} mm` : '—'}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      min required: <b style={{ color: 'var(--text-primary)' }}>{fld.min_required_mm || 1.0} mm</b>
                    </span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {fld.threshold_citation || 'Rule 7(3) requirement'}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Limitations / Legal Accuracy Banner */}
          {inspection.font_analysis.limitations && (
            <div style={{
              marginTop: '16px',
              padding: '12px 16px',
              backgroundColor: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Info size={16} color="#F59E0B" style={{ flexShrink: 0 }} />
              <span>{inspection.font_analysis.limitations}</span>
            </div>
          )}
        </div>
      )}

      {/* 7b. Declaration Placement & Grouping Analysis (Rule 8, PCR 2011) */}
      {inspection.placement_analysis && (
        <div className="card" style={{
          padding: '24px',
          borderColor: inspection.placement_analysis.status === 'FAIL' ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-subtle)',
          backgroundColor: inspection.placement_analysis.status === 'FAIL' ? 'rgba(239, 68, 68, 0.02)' : 'var(--bg-canvas)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={20} color="#6366F1" /> Declaration Placement & Grouping (Rule 8, PCR 2011)
              </h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Principal Display Panel grouping check and statutory clear space analysis surrounding net quantity numeral
              </p>
            </div>
            <div>
              <span className={`badge ${
                inspection.placement_analysis.status === 'PASS'
                  ? 'badge-compliant'
                  : (inspection.placement_analysis.status === 'FAIL' ? 'badge-noncompliant' : 'badge-review')
              }`} style={{ fontSize: '0.82rem', padding: '6px 14px' }}>
                Rule 8 Verdict: {inspection.placement_analysis.status}
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px', marginTop: '14px' }}>
            {/* Grouping Sub-Card */}
            <div style={{
              padding: '16px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                  PDP Spatial Grouping
                </span>
                <span className={`badge ${
                  inspection.placement_analysis.grouping?.status === 'PASS'
                    ? 'badge-compliant'
                    : (inspection.placement_analysis.grouping?.status === 'FAIL' ? 'badge-noncompliant' : 'badge-review')
                }`} style={{ fontSize: '0.72rem' }}>
                  {inspection.placement_analysis.grouping?.status || 'NEEDS_REVIEW'}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {inspection.placement_analysis.grouping?.explanation}
              </p>
              {inspection.placement_analysis.grouping?.fields_analyzed?.length > 0 && (
                <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {inspection.placement_analysis.grouping.fields_analyzed.map(f => (
                    <span key={f} style={{
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      backgroundColor: 'rgba(99, 102, 241, 0.1)',
                      color: '#818CF8',
                      borderRadius: '4px'
                    }}>
                      {f}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Clear Space Sub-Card */}
            <div style={{
              padding: '16px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                  Net Qty Clear Space (Rule 8(1) Proviso)
                </span>
                <span className={`badge ${
                  inspection.placement_analysis.clear_space?.status === 'PASS'
                    ? 'badge-compliant'
                    : (inspection.placement_analysis.clear_space?.status === 'FAIL' ? 'badge-noncompliant' : 'badge-review')
                }`} style={{ fontSize: '0.72rem' }}>
                  {inspection.placement_analysis.clear_space?.status || 'NEEDS_REVIEW'}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {inspection.placement_analysis.clear_space?.explanation}
              </p>
              {inspection.placement_analysis.clear_space?.numeral_height_px && (
                <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Numeral Height: {inspection.placement_analysis.clear_space.numeral_height_px}px | 
                  Vert Clear: {inspection.placement_analysis.clear_space.required_vertical_clearance_px}px | 
                  Horiz Clear: {inspection.placement_analysis.clear_space.required_horizontal_clearance_px}px
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 8. Legal References & Statutory Rule Breakdown */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BookOpen size={20} color="#38BDF8" /> Legal References & Statutory Rule Breakdown
              </h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Provisions evaluated under Legal Metrology Act, 2009 and Legal Metrology (Packaged Commodities) Rules, 2011
              </p>
            </div>

            {/* Rule Filter Tabs */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {[
                { key: 'ALL', label: `All (${legalReferences.length})` },
                { key: 'PASS', label: `Passed (${passedCount})` },
                { key: 'FAIL', label: `Violations (${failedCount})` },
                { key: 'NEEDS_REVIEW', label: `Review (${needsReviewCount})` },
              ].map(tab => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveRuleFilter(tab.key)}
                  style={{
                    padding: '4px 10px',
                    fontSize: '0.72rem',
                    borderRadius: 'var(--radius-sm)',
                    fontWeight: '700',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: activeRuleFilter === tab.key ? '#3B82F6' : 'var(--bg-canvas)',
                    color: activeRuleFilter === tab.key ? 'var(--text-primary)' : 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '28%' }}>Legal Reference & Rule Citation</th>
              <th style={{ width: '30%' }}>Statutory Requirement</th>
              <th style={{ width: '14%' }}>Result</th>
              <th style={{ width: '28%' }}>Finding & Explanation</th>
            </tr>
          </thead>
          <tbody>
            {filteredRules.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '24px' }}>
                  No rules found for the selected filter.
                </td>
              </tr>
            ) : (
              filteredRules.map((r, idx) => (
                <tr key={idx}>
                  <td>
                    <div style={{ fontWeight: '700', color: 'var(--accent-primary)', fontSize: '0.82rem' }}>
                      {r.legal_reference || r.rule_id}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      ID: {r.rule_id}
                    </div>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    {r.requirement || r.expected_requirement || 'Statutory requirement under PCR 2011'}
                  </td>
                  <td>
                    <span className={`badge ${
                      r.status === 'PASS' 
                        ? 'badge-compliant' 
                        : (r.status === 'FAIL' ? 'badge-noncompliant' : (r.status === 'NEEDS_REVIEW' ? 'badge-review' : 'badge-neutral'))
                    }`} style={{ fontSize: '0.68rem' }}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                    <div style={{ color: r.status === 'FAIL' ? 'var(--status-noncompliant)' : '#E2E8F0' }}>
                      {r.explanation}
                    </div>
                    {r.detected_value && (
                      <div style={{ marginTop: '4px', color: 'var(--text-secondary)', fontSize: '0.72rem' }}>
                        Detected: <code style={{ color: 'var(--text-secondary)', background: '#0F1D36', padding: '1px 4px', borderRadius: '3px' }}>{String(r.detected_value)}</code>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 9. Visual Evidence Viewer with Highlighted Violation Regions & Inspector */}
      <div id="evidence-viewer">
        <EvidenceViewer
          imageUrl={imageUrl}
          boundingBoxes={inspection.bounding_boxes || inspection.extracted_data?._bounding_boxes || []}
          evidence={inspection.evidence}
          violations={violations}
          selectedViolation={selectedViolation}
          onSelectViolation={(v) => setSelectedViolation(v)}
          productName={inspection.product_name}
        />
      </div>

      {/* Regulatory Legal Disclaimer */}
      <div style={{
        padding: '16px 20px',
        backgroundColor: 'var(--bg-canvas)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px'
      }}>
        <Scale size={20} color="#94A3B8" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
          <b>Legal Metrology Regulatory Disclaimer:</b> This report provides automated label-compliance assistance based on detected declarations and configured Legal Metrology rules under the Legal Metrology (Packaged Commodities) Rules, 2011. SafeMetric evaluates label declaration compliance only and does not verify physical or consumable product safety. Final regulatory determination remains subject to authorized physical inspection by a designated Legal Metrology officer.
        </div>
      </div>
    </div>
  );
};

export default ResultPage;
