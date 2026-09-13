import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Scan, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  TrendingUp, 
  Clock, 
  Eye, 
  FileWarning, 
  Sparkles,
  Layers,
  ArrowUpRight,
  Shield
} from 'lucide-react';
import { dashboardAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardAPI.getStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard statistics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: 'var(--text-secondary)', gap: '10px' }}>
        <div className="animate-spin" style={{ width: '24px', height: '24px', border: '3px solid #1E2E4E', borderTopColor: '#3B82F6', borderRadius: '50%' }} />
        Loading Legal Metrology Dashboard Metrics...
      </div>
    );
  }

  const total = stats?.total_inspections || 0;
  const compliant = stats?.compliant_count || 0;
  const partiallyCompliant = stats?.partially_compliant_count || 0;
  const nonCompliant = stats?.non_compliant_count || 0;
  const needsReview = stats?.needs_review_count || 0;
  const avgScore = stats?.average_compliance_score || 0;
  const compliancePct = stats?.compliance_percentage || 0;
  const recent = stats?.recent_inspections || [];
  const violationsMap = stats?.violations_breakdown || {};
  const commonViolations = stats?.common_violations || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Officer Greeting & Quick Action Banner */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: 'var(--radius-lg)',
        padding: '28px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '20px',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-primary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Statutory Inspection Portal
            </span>
            <span className="badge badge-info" style={{ backgroundColor: 'var(--status-info-bg)', borderColor: 'var(--status-info-border)', color: 'var(--accent-primary)', fontSize: '0.65rem' }}>
              <Shield size={10} /> GOVT OFFICIAL MODE
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px' }}>
            Good day, {user?.name || 'Inspector'}
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px', maxWidth: '640px' }}>
            SafeMetric automated regulatory compliance engine under the <b>Legal Metrology (Packaged Commodities) Rules, 2011</b>.
          </p>
        </div>

        <Link
          to="/scan"
          className="btn-primary"
          style={{
            padding: '14px 28px',
            fontSize: '1rem',
            fontWeight: '700',
            borderRadius: 'var(--radius-md)',
            boxShadow: '0 8px 24px rgba(37, 99, 235, 0.4)'
          }}
        >
          <Scan size={20} />
          + SCAN PRODUCT
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px'
      }}>
        {/* Total Inspections */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Total Inspections
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '6px' }}>
                {total}
              </div>
            </div>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(59, 130, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Layers size={20} color="#3B82F6" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '10px', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Clock size={13} /> Recorded in audit DB
          </div>
        </div>

        {/* Compliant */}
        <div className="card" style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#10B981', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Compliant
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: '800', color: '#10B981', marginTop: '6px' }}>
                {compliant}
              </div>
            </div>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'var(--status-compliant-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <CheckCircle2 size={20} color="#10B981" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10B981', marginTop: '10px' }}>
            {total > 0 ? `${compliancePct}% pass rate` : '0%'}
          </div>
        </div>

        {/* Partially Compliant */}
        <div className="card" style={{ borderColor: 'rgba(56, 189, 248, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Partially Compliant
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: '800', color: 'var(--accent-primary)', marginTop: '6px' }}>
                {partiallyCompliant}
              </div>
            </div>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Sparkles size={20} color="#38BDF8" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', marginTop: '10px' }}>
            Minor non-critical deviations
          </div>
        </div>

        {/* Non-Compliant */}
        <div className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#EF4444', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Non-Compliant
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: '800', color: '#EF4444', marginTop: '6px' }}>
                {nonCompliant}
              </div>
            </div>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'var(--status-noncompliant-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <XCircle size={20} color="#EF4444" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#EF4444', marginTop: '10px' }}>
            Statutory violations detected
          </div>
        </div>

        {/* Needs Review */}
        <div className="card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#F59E0B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Needs Review
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: '800', color: '#F59E0B', marginTop: '6px' }}>
                {needsReview}
              </div>
            </div>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'var(--status-review-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AlertTriangle size={20} color="#F59E0B" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#F59E0B', marginTop: '10px' }}>
            Requires manual physical audit
          </div>
        </div>

        {/* Average Compliance Score */}
        <div className="card" style={{ borderColor: 'rgba(139, 92, 246, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#A78BFA', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Average Score
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: '800', color: '#A78BFA', marginTop: '6px' }}>
                {avgScore}%
              </div>
            </div>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(139, 92, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <TrendingUp size={20} color="#A78BFA" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#A78BFA', marginTop: '10px' }}>
            Across all verified labels
          </div>
        </div>
      </div>

      {/* Middle Grid: Compliance Health & Violations Breakdown */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '20px'
      }}>
        {/* Compliance Meter & Statutory Summary */}
        <div className="card">
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={18} color="#38BDF8" />
            Overall Compliance Performance
          </h3>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px', margin: '20px 0' }}>
            {/* Circular Gauge */}
            <div style={{
              width: '110px',
              height: '110px',
              borderRadius: '50%',
              background: `conic-gradient(#10B981 ${compliancePct * 3.6}deg, #1E2E4E 0deg)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <div style={{
                width: '84px',
                height: '84px',
                borderRadius: '50%',
                backgroundColor: 'var(--bg-card)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '1.35rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {compliancePct}%
                </span>
                <span style={{ fontSize: '0.62rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                  COMPLIANT
                </span>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Legal Metrology Benchmark
              </h4>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.4' }}>
                Enforcement rate evaluated across mandatory declarations: MRP, Net Quantity, Dates, Manufacturer & Consumer Care Cell.
              </p>
            </div>
          </div>

          <div style={{
            padding: '12px',
            backgroundColor: 'var(--bg-canvas)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            lineHeight: '1.4'
          }}>
            <b>Statutory Note:</b> A commodity is declared <b>NON-COMPLIANT</b> if any mandatory high-severity declaration is missing, regardless of overall percentage.
          </div>
        </div>

        {/* Violations Breakdown by Field */}
        <div className="card">
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileWarning size={18} color="#EF4444" />
            Top Declaration Violations Detected
          </h3>

          {commonViolations.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {commonViolations.slice(0, 5).map((item, idx) => {
                const maxCount = commonViolations[0]?.count || 1;
                const pct = Math.round((item.count / maxCount) * 100);
                return (
                  <div key={item.category}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ 
                          width: '18px', 
                          height: '18px', 
                          borderRadius: '4px', 
                          background: 'rgba(239, 68, 68, 0.15)', 
                          color: '#EF4444', 
                          fontSize: '0.7rem', 
                          fontWeight: '700', 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          justifyContent: 'center' 
                        }}>
                          #{idx + 1}
                        </span>
                        {item.category}
                      </span>
                      <span style={{ color: '#EF4444', fontWeight: '700' }}>
                        {item.count} {item.count === 1 ? 'violation' : 'violations'}
                      </span>
                    </div>
                    <div style={{ height: '6px', backgroundColor: 'var(--bg-canvas)', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${pct}%`,
                        backgroundColor: '#EF4444',
                        borderRadius: '9999px',
                        transition: 'width 0.4s ease'
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <CheckCircle2 size={32} color="#10B981" style={{ margin: '0 auto 8px', display: 'block' }} />
              No statutory violations recorded in current audit batch.
            </div>
          )}
        </div>
      </div>

      {/* Recent Inspections Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              Recent Commodity Inspections
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Audit log of latest product scans and compliance results
            </p>
          </div>
          <Link
            to="/history"
            style={{
              fontSize: '0.8rem',
              fontWeight: '600',
              color: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            View Complete History <ArrowUpRight size={16} />
          </Link>
        </div>

        {recent.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Product / Commodity</th>
                <th>Inspection Date</th>
                <th>Status</th>
                <th>Compliance Score</th>
                <th>Issues</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((insp) => {
                const s = (insp.compliance_status || '').toUpperCase();
                const badgeClass = s.includes('NON') 
                  ? 'badge-noncompliant' 
                  : (s.includes('PARTIAL') || s.includes('REVIEW') || s.includes('NEEDS') ? 'badge-review' : 'badge-compliant');

                return (
                  <tr key={insp.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                          width: '38px',
                          height: '38px',
                          borderRadius: '8px',
                          overflow: 'hidden',
                          backgroundColor: 'var(--bg-canvas)',
                          border: '1px solid var(--border-subtle)',
                          flexShrink: 0
                        }}>
                          <img
                            src={insp.image_url}
                            alt={insp.product_name}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                          />
                        </div>
                        <div>
                          <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                            {insp.product_name}
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            ID: #{insp.inspection_id || `INS-${insp.id}`}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {new Date(insp.inspection_date).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </td>
                    <td>
                      <span className={`badge ${badgeClass}`}>
                        {insp.compliance_status}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                        {insp.compliance_score}%
                      </span>
                    </td>
                    <td style={{ color: insp.violations_count > 0 ? '#EF4444' : '#10B981', fontWeight: '500' }}>
                      {insp.violations_count > 0 ? `${insp.violations_count} issues` : '0 issues'}
                    </td>
                    <td>
                      <Link
                        to={`/result/${insp.id}`}
                        className="btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                      >
                        <Eye size={14} />
                        View Result
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <Scan size={36} color="#38BDF8" style={{ margin: '0 auto 12px', opacity: 0.8 }} />
            <h4 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              No inspections recorded yet
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px', marginBottom: '16px' }}>
              Capture or upload a product label to start verifying Legal Metrology compliance.
            </p>
            <Link to="/scan" className="btn-primary" style={{ padding: '8px 20px' }}>
              Inspect First Product
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
