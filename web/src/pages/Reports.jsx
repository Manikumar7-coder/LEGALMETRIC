import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Download, Eye, ExternalLink, ShieldCheck, Calendar } from 'lucide-react';
import { reportAPI } from '../services/api';

export const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data = await reportAPI.list();
        setReports(data);
      } catch (err) {
        console.error('Failed to load reports archive:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  return (
    <div style={{ maxWidth: '1120px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-primary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Statutory Archive
          </span>
        </div>
        <h1 style={{ fontSize: '1.65rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>
          Inspection Reports & Official Certificates
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Generated official PDF inspection summaries with Legal Metrology rule citations and forensic photo evidence
        </p>
      </div>

      {/* Reports Table Card */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="animate-spin" style={{ width: '24px', height: '24px', border: '3px solid #1E2E4E', borderTopColor: '#3B82F6', borderRadius: '50%', margin: '0 auto 12px' }} />
            Loading statutory reports...
          </div>
        ) : reports.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Report ID</th>
                <th>Commodity Name</th>
                <th>Inspection Date</th>
                <th>Status</th>
                <th>Score</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.report_id}>
                  <td style={{ fontFamily: 'monospace', color: 'var(--accent-primary)', fontWeight: '600' }}>
                    #REP-2026-{r.report_id}
                  </td>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {r.product_name}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {new Date(r.created_at).toLocaleDateString('en-GB', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td>
                    <span className={`badge ${
                      r.compliance_status === 'COMPLIANT'
                        ? 'badge-compliant'
                        : (r.compliance_status === 'NON-COMPLIANT' ? 'badge-noncompliant' : 'badge-review')
                    }`}>
                      {r.compliance_status}
                    </span>
                  </td>
                  <td style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                    {r.compliance_score}%
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <Link
                        to={`/result/${r.inspection_id}`}
                        className="btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                      >
                        <Eye size={14} /> View
                      </Link>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <a
                          href={reportAPI.getDownloadUrl(r.inspection_id, 'pdf')}
                          download
                          target="_blank"
                          rel="noreferrer"
                          className="btn-primary"
                          style={{ padding: '6px 10px', fontSize: '0.72rem' }}
                          title="Download PDF"
                        >
                          <Download size={13} /> PDF
                        </a>
                        <a
                          href={reportAPI.getDownloadUrl(r.inspection_id, 'docx')}
                          download
                          target="_blank"
                          rel="noreferrer"
                          className="btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '0.72rem' }}
                          title="Download Editable Word Document (.docx)"
                        >
                          DOCX
                        </a>
                        <a
                          href={reportAPI.getDownloadUrl(r.inspection_id, 'csv')}
                          download
                          target="_blank"
                          rel="noreferrer"
                          className="btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '0.72rem' }}
                          title="Download CSV Audit Export"
                        >
                          CSV
                        </a>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px 24px' }}>
            <FileText size={36} color="#64748B" style={{ margin: '0 auto 12px' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              No generated reports in archive
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Reports are automatically produced whenever a commodity label is analyzed.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportsPage;
