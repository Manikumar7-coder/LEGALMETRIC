import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  Scale, 
  Scan, 
  LayoutDashboard, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  Layers, 
  Eye, 
  AlertTriangle,
  FileDown,
  UserCheck,
  Award,
  BookOpen
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LandingPage = () => {
  const { user } = useAuth();

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#070D19',
      color: '#F8FAFC',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Top Navigation Bar */}
      <header style={{
        height: '72px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        backgroundColor: 'rgba(7, 13, 25, 0.85)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 40px'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)',
            padding: '10px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)'
          }}>
            <ShieldCheck size={24} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#FFFFFF', lineHeight: 1.1 }}>
              SAFEMETRIC
            </div>
            <div style={{ fontSize: '0.65rem', color: '#38BDF8', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Legal Metrology Compliance AI
            </div>
          </div>
        </div>

        {/* Center Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
          <Link to="/" style={{ color: '#FFFFFF', fontSize: '0.875rem', fontWeight: '600' }}>Home</Link>
          <a href="#features" style={{ color: '#94A3B8', fontSize: '0.875rem', fontWeight: '500' }}>Features</a>
          <a href="#rules" style={{ color: '#94A3B8', fontSize: '0.875rem', fontWeight: '500' }}>Statutory Rules</a>
          <a href="#pipeline" style={{ color: '#94A3B8', fontSize: '0.875rem', fontWeight: '500' }}>Architecture</a>
        </nav>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '0.85rem', color: '#94A3B8' }}>
                Officer: <b style={{ color: '#FFFFFF' }}>{user.name}</b>
              </span>
              <Link to="/dashboard" className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.85rem' }}>
                <LayoutDashboard size={16} /> Open Dashboard
              </Link>
            </div>
          ) : (
            <>
              <Link to="/login" className="btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
                Officer Sign In
              </Link>
              <Link to="/register" className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.85rem' }}>
                Register Inspector
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        padding: '80px 40px 60px',
        maxWidth: '1200px',
        margin: '0 auto',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '24px'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          borderRadius: '9999px',
          backgroundColor: 'rgba(37, 99, 235, 0.15)',
          border: '1px solid rgba(59, 130, 246, 0.35)',
          color: '#60A5FA',
          fontSize: '0.8rem',
          fontWeight: '700',
          letterSpacing: '0.04em',
          textTransform: 'uppercase'
        }}>
          <Award size={16} /> Smart India Hackathon 2026 Innovation
        </div>

        <h1 style={{
          fontSize: '3.4rem',
          fontWeight: '900',
          lineHeight: 1.15,
          letterSpacing: '-0.03em',
          maxWidth: '900px',
          background: 'linear-gradient(180deg, #FFFFFF 30%, #94A3B8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          margin: 0
        }}>
          Automated Legal Metrology Compliance for Packaged Commodities
        </h1>

        <p style={{
          fontSize: '1.15rem',
          color: '#94A3B8',
          maxWidth: '780px',
          lineHeight: 1.6,
          margin: 0
        }}>
          Autonomous AI enforcement engine verifying label declarations directly from package photographs under the <b style={{ color: '#E2E8F0' }}>Legal Metrology Act, 2009</b> and <b style={{ color: '#E2E8F0' }}>Legal Metrology (Packaged Commodities) Rules, 2011</b> — with zero external product database dependencies.
        </p>

        {/* CTA Buttons */}
        <div style={{ display: 'flex', gap: '16px', marginTop: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link
            to={user ? "/scan" : "/login"}
            className="btn-primary"
            style={{
              padding: '14px 28px',
              fontSize: '1rem',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: '0 8px 24px rgba(37, 99, 235, 0.4)'
            }}
          >
            <Scan size={20} /> Launch New Inspection <ArrowRight size={18} />
          </Link>
          <Link
            to={user ? "/dashboard" : "/login"}
            className="btn-secondary"
            style={{
              padding: '14px 24px',
              fontSize: '1rem',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <LayoutDashboard size={20} /> Enforcement Dashboard
          </Link>
        </div>

        {/* Statutory Compliance Badges */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '24px',
          marginTop: '24px',
          flexWrap: 'wrap',
          justifyContent: 'center',
          color: '#64748B',
          fontSize: '0.85rem',
          fontWeight: '500'
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} color="#10B981" /> PCR 2011 Rule 6(1) Enforced
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} color="#10B981" /> Automated USP Verification
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} color="#10B981" /> Dynamic RapidOCR (PP-OCRv4)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} color="#10B981" /> Statutory PDF Reports
          </span>
        </div>
      </section>

      {/* Architecture Flow Section */}
      <section id="pipeline" style={{
        padding: '60px 40px',
        backgroundColor: 'rgba(15, 29, 54, 0.4)',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <div style={{ maxWidth: '1120px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#38BDF8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Autonomous Processing Pipeline
            </span>
            <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#FFFFFF', marginTop: '6px' }}>
              From Physical Package to Statutory Certificate
            </h2>
            <p style={{ fontSize: '0.9rem', color: '#94A3B8', marginTop: '6px' }}>
              Primary input is strictly the photographed commodity label. No barcode lookup or pre-seeded database required.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px'
          }}>
            {[
              { step: '01', title: 'Image Preprocessing', desc: 'Adaptive thresholding, deskew, and illumination normalization via OpenCV.' },
              { step: '02', title: 'Dynamic RapidOCR', desc: 'PP-OCRv4 ONNX model extracts text polygons and optical confidence scores.' },
              { step: '03', title: 'Declaration Parsing', desc: 'Extracts 12 statutory PCR declarations including MRP, USP, Generic Name, and Net Qty.' },
              { step: '04', title: 'Rules Engine', desc: 'Verifies 12 legal requirements, validates metric units, and checks USP mathematics.' },
              { step: '05', title: 'Evidence & Certificate', desc: 'Interactive bounding box overlay and tamper-evident ReportLab PDF report.' },
            ].map((s, idx) => (
              <div
                key={idx}
                style={{
                  padding: '24px 20px',
                  backgroundColor: '#070D19',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                <div style={{ fontSize: '1.5rem', fontWeight: '900', color: '#3B82F6' }}>{s.step}</div>
                <h4 style={{ fontSize: '1rem', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>{s.title}</h4>
                <p style={{ fontSize: '0.8rem', color: '#94A3B8', margin: 0, lineHeight: 1.4 }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Statutory Rules Grid */}
      <section id="rules" style={{ padding: '70px 40px', maxWidth: '1120px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#38BDF8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Legal Framework
          </span>
          <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#FFFFFF', marginTop: '6px' }}>
            Enforcing The Packaged Commodities Rules, 2011
          </h2>
          <p style={{ fontSize: '0.9rem', color: '#94A3B8', marginTop: '6px' }}>
            Automated compliance checking across all mandatory statutory declarations
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '20px'
        }}>
          {[
            { rule: 'Rule 6(1)(a)', title: 'Manufacturer / Packer Identity', desc: 'Mandatory declaration of complete name and registered postal address.' },
            { rule: 'Rule 6(1)(b)', title: 'Generic or Common Name', desc: 'Prominent declaration of generic commodity name on the principal display panel.' },
            { rule: 'Rule 6(1)(c)', title: 'Net Quantity in Metric Units', desc: 'Strict standard SI units (g, kg, ml, l). Non-standard qualifying words prohibited.' },
            { rule: 'Rule 6(1)(d)', title: 'Month & Year of Manufacture', desc: 'Mandatory manufacturing or pre-packing date for shelf-life traceability.' },
            { rule: 'Rule 6(1)(e)', title: 'Maximum Retail Price (MRP)', desc: 'Must declare inclusive of all taxes in standard Indian currency format.' },
            { rule: 'Rule 6(1)(ea)', title: 'Unit Sale Price (USP)', desc: 'Automated calculation and verification (MRP / Net Qty) in Rs. per unit measure.' },
            { rule: 'Rule 6(1)(f)', title: 'Consumer Care Cell', desc: 'Toll-free number, email, and address for consumer grievance redressal.' },
            { rule: 'Rule 6(1)(h)', title: 'Country of Origin', desc: 'Mandatory country declaration for domestic and imported packaged goods.' },
            { rule: 'Section 18', title: 'Non-Deceptive Packaging', desc: 'Guarantees packaging is not misleading regarding commodity quantity or size.' },
          ].map((r, idx) => (
            <div
              key={idx}
              style={{
                padding: '20px',
                backgroundColor: 'rgba(15, 29, 54, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '800', color: '#38BDF8' }}>{r.rule}</span>
                <Scale size={16} color="#64748B" />
              </div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>{r.title}</h4>
              <p style={{ fontSize: '0.8rem', color: '#94A3B8', margin: 0, lineHeight: 1.4 }}>{r.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Navigation Quick Links / Callout */}
      <section style={{
        padding: '60px 40px',
        backgroundColor: '#0B162C',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#FFFFFF', margin: 0 }}>
            Ready to Inspect Packaged Commodities?
          </h2>
          <p style={{ fontSize: '0.95rem', color: '#94A3B8', margin: 0 }}>
            Sign in as a Legal Metrology officer to begin automated package audits, view inspection history, and export certificates.
          </p>
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <Link to="/login" className="btn-primary" style={{ padding: '12px 24px', fontSize: '0.95rem' }}>
              Sign In to Enforcement Portal
            </Link>
            <Link to="/register" className="btn-secondary" style={{ padding: '12px 24px', fontSize: '0.95rem' }}>
              Register Officer Account
            </Link>
            <Link to="/dashboard" className="btn-secondary" style={{ padding: '12px 24px', fontSize: '0.95rem' }}>
              View Enforcement Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '28px 40px',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.78rem',
        color: '#64748B',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <b>SAFEMETRIC</b> — Smart India Hackathon 2026 • Legal Metrology Automated Audit System
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>Legal Metrology Act, 2009</span>
          <span>•</span>
          <span>PCR 2011</span>
          <span>•</span>
          <span>Ministry of Consumer Affairs</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
