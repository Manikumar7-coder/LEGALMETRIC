import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  ArrowUpDown, 
  Eye, 
  Trash2, 
  Calendar, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Scan,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Clock
} from 'lucide-react';
import { inspectionAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const HistoryPage = () => {
  const { isAdmin } = useAuth();
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('newest');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await inspectionAPI.list({
        status: statusFilter,
        search: search || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        sort_by: sortBy,
        page: 1,
        page_size: 100 // fetch sufficient to support client or server pagination
      });
      setInspections(Array.isArray(data) ? data : (data?.items || []));
      setPage(1);
    } catch (err) {
      console.error('Failed to load inspection history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [statusFilter, sortBy, fromDate, toDate]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchHistory();
  };

  const handleResetFilters = () => {
    setSearch('');
    setStatusFilter('ALL');
    setFromDate('');
    setToDate('');
    setSortBy('newest');
  };

  const handleDelete = async (id, name) => {
    if (window.confirm(`Are you sure you want to delete inspection record for "${name}" (#INS-${id})?`)) {
      try {
        await inspectionAPI.delete(id);
        setInspections((prev) => prev.filter((i) => i.id !== id));
      } catch (err) {
        alert('Failed to delete inspection.');
      }
    }
  };

  const hasActiveFilters = Boolean(search || statusFilter !== 'ALL' || fromDate || toDate);

  // Pagination calculation
  const totalRecords = inspections.length;
  const totalPages = Math.ceil(totalRecords / pageSize) || 1;
  const paginatedInspections = inspections.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div style={{ maxWidth: '1140px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-primary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Statutory Inspection Audit Trail
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>
            Inspection History & Records
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Permanent database of Legal Metrology package image audits conducted under PCR, 2011
          </p>
        </div>

        <Link to="/scan" className="btn-primary" style={{ padding: '10px 18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Scan size={18} /> Inspect New Commodity
        </Link>
      </div>

      {/* Filter & Search Bar */}
      <div className="card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Status Filter Tabs */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {['ALL', 'COMPLIANT', 'PARTIALLY COMPLIANT', 'NON-COMPLIANT', 'NEEDS REVIEW'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: '7px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.78rem',
                  fontWeight: '700',
                  border: statusFilter === st ? '1px solid #38BDF8' : '1px solid var(--border-subtle)',
                  backgroundColor: statusFilter === st ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-canvas)',
                  color: statusFilter === st ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {st}
              </button>
            ))}
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleResetFilters}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                fontSize: '0.78rem',
                cursor: 'pointer'
              }}
            >
              <RotateCcw size={14} /> Reset Filters
            </button>
          )}
        </div>

        {/* Search, Dates & Sort Controls */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <form onSubmit={handleSearchSubmit} style={{ position: 'relative', minWidth: '260px', flex: '1 1 260px' }}>
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              placeholder="Search by commodity name or inspection ID..."
              className="form-input"
              style={{ paddingLeft: '36px', height: '40px', fontSize: '0.82rem', width: '100%' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>

          {/* Date Filter Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--bg-canvas)', padding: '4px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <Calendar size={14} color="#94A3B8" />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>From:</span>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.78rem',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--bg-canvas)', padding: '4px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <Calendar size={14} color="#94A3B8" />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>To:</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.78rem',
                  outline: 'none'
                }}
              />
            </div>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="form-input"
              style={{ width: '140px', height: '40px', fontSize: '0.82rem' }}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="score">Highest Score</option>
            </select>
          </div>
        </div>
      </div>

      {/* Inspections Table / Empty State */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="animate-spin" style={{ width: '24px', height: '24px', border: '3px solid #1E2E4E', borderTopColor: 'var(--accent-primary)', borderRadius: '50%', margin: '0 auto 12px' }} />
            Loading inspection records from database...
          </div>
        ) : paginatedInspections.length > 0 ? (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '14px 18px' }}>Commodity</th>
                    <th style={{ textAlign: 'left', padding: '14px 18px' }}>Inspection Reference</th>
                    <th style={{ textAlign: 'left', padding: '14px 18px' }}>Date & Time</th>
                    <th style={{ textAlign: 'left', padding: '14px 18px' }}>Compliance Determination</th>
                    <th style={{ textAlign: 'center', padding: '14px 18px' }}>Score</th>
                    <th style={{ textAlign: 'center', padding: '14px 18px' }}>Violations</th>
                    <th style={{ textAlign: 'right', padding: '14px 18px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedInspections.map((i) => {
                    const statusStr = (i.status || i.compliance_status || '').toUpperCase();
                    let badgeClass = 'badge-review';
                    let badgeColor = 'var(--accent-primary)';
                    let badgeText = i.status || i.compliance_status || 'Under Review';

                    if (statusStr.includes('NON')) {
                      badgeClass = 'badge-noncompliant';
                      badgeColor = '#EF4444';
                    } else if (statusStr.includes('PARTIAL')) {
                      badgeClass = 'badge-warning';
                      badgeColor = '#F59E0B';
                    } else if (statusStr.includes('COMPLIANT')) {
                      badgeClass = 'badge-compliant';
                      badgeColor = '#10B981';
                    }

                    const insDate = i.created_at || i.inspection_date;
                    const dateFormatted = insDate 
                      ? new Date(insDate).toLocaleString('en-GB', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      : 'Recently Audited';

                    return (
                      <tr key={i.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '14px 18px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{
                              width: '42px',
                              height: '42px',
                              borderRadius: '8px',
                              overflow: 'hidden',
                              backgroundColor: 'var(--bg-canvas)',
                              border: '1px solid var(--border-subtle)',
                              flexShrink: 0
                            }}>
                              <img
                                src={i.image_url || `/api/inspections/${i.id}/image`}
                                alt={i.product_name}
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={(e) => { e.currentTarget.style.display = 'none'; }}
                              />
                            </div>
                            <div>
                              <Link to={`/result/${i.id}`} style={{ fontWeight: '700', color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.9rem' }}>
                                {i.product_name}
                              </Link>
                              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                                Packaging Image Audit
                              </div>
                            </div>
                          </div>
                        </td>

                        <td style={{ padding: '14px 18px', color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '0.82rem' }}>
                          {i.inspection_id || `#INS-${i.id}`}
                        </td>

                        <td style={{ padding: '14px 18px', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Clock size={13} color="#64748B" />
                            {dateFormatted}
                          </div>
                        </td>

                        <td style={{ padding: '14px 18px' }}>
                          <span className={`badge ${badgeClass}`} style={{ fontSize: '0.72rem', padding: '4px 10px' }}>
                            {badgeText}
                          </span>
                        </td>

                        <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                          <span style={{ fontWeight: '800', fontSize: '1rem', color: badgeColor }}>
                            {typeof i.compliance_score === 'number' ? `${i.compliance_score.toFixed(1)}%` : '0.0%'}
                          </span>
                        </td>

                        <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                          <span style={{
                            fontSize: '0.78rem',
                            fontWeight: '700',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            backgroundColor: i.violations_count > 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: i.violations_count > 0 ? '#EF4444' : '#10B981'
                          }}>
                            {i.violations_count > 0 ? `${i.violations_count} detected` : '0 infractions'}
                          </span>
                        </td>

                        <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                            <Link
                              to={`/result/${i.id}`}
                              className="btn-primary"
                              style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                              title="View Complete Statutory Result"
                            >
                              <Eye size={13} /> Result
                            </Link>
                            <Link
                              to={`/inspection/${i.id}`}
                              className="btn-secondary"
                              style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                              title="Audit Trail Log"
                            >
                              Details
                            </Link>
                            {isAdmin && (
                              <button
                                type="button"
                                onClick={() => handleDelete(i.id, i.product_name)}
                                style={{
                                  background: 'transparent',
                                  border: '1px solid rgba(239, 68, 68, 0.25)',
                                  color: '#EF4444',
                                  padding: '6px 8px',
                                  borderRadius: '6px',
                                  cursor: 'pointer'
                                }}
                                title="Delete Record (Admin Only)"
                              >
                                <Trash2 size={13} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls Bar */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px 20px',
              borderTop: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-canvas)',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Showing <b>{((page - 1) * pageSize) + 1}</b> to <b>{Math.min(page * pageSize, totalRecords)}</b> of <b>{totalRecords}</b> inspection records
              </span>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.78rem', opacity: page === 1 ? 0.4 : 1, cursor: page === 1 ? 'not-allowed' : 'pointer' }}
                >
                  <ChevronLeft size={14} /> Previous
                </button>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)', padding: '0 8px' }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  disabled={page === totalPages}
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.78rem', opacity: page === totalPages ? 0.4 : 1, cursor: page === totalPages ? 'not-allowed' : 'pointer' }}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </>
        ) : hasActiveFilters ? (
          /* Empty state when filters return 0 results */
          <div style={{ textAlign: 'center', padding: '60px 24px' }}>
            <FileText size={40} color="#64748B" style={{ margin: '0 auto 12px' }} />
            <h4 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              No inspections match current criteria
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', maxWidth: '440px', margin: '4px auto 16px' }}>
              No commodity packaging records were found for the selected status, date range, or search keyword.
            </p>
            <button
              type="button"
              onClick={handleResetFilters}
              className="btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <RotateCcw size={14} /> Clear All Filters
            </button>
          </div>
        ) : (
          /* Empty state when database has 0 inspections */
          <div style={{ textAlign: 'center', padding: '70px 24px' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              backgroundColor: 'var(--status-info-bg)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}>
              <ShieldCheck size={28} color="#38BDF8" />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--text-primary)' }}>
              No Inspection Records Stored Yet
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', maxWidth: '480px', margin: '8px auto 20px', lineHeight: '1.5' }}>
              Upload your first packaged commodity image to conduct automated optical character recognition, declaration extraction, and statutory Legal Metrology auditing.
            </p>
            <Link to="/scan" className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', fontSize: '0.9rem' }}>
              <Scan size={18} /> + Inspect First Commodity
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
