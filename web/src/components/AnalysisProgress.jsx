import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, Sparkles, ShieldAlert, Cpu } from 'lucide-react';

const STAGES = [
  { id: 1, label: 'Image received & verified', message: 'Verifying label image resolution and clarity...' },
  { id: 2, label: 'OpenCV image preprocessing', message: 'Applying bilateral denoising, CLAHE contrast & sharpening...' },
  { id: 3, label: 'OCR text extraction (PaddleOCR)', message: 'Extracting alphanumeric text and bounding boxes...' },
  { id: 4, label: 'Statutory declaration extraction', message: 'Parsing MRP, Net Qty, Dates, Manufacturer & Consumer Care...' },
  { id: 5, label: 'Legal Metrology rule engine validation', message: 'Checking against Packaged Commodities Rules, 2011...' },
  { id: 6, label: 'Statutory compliance analysis', message: 'Calculating compliance score and classifying violations...' },
  { id: 7, label: 'Report & audit trail preparation', message: 'Generating official PDF report and saving audit record...' },
];

export const AnalysisProgress = ({ onComplete }) => {
  const [currentStage, setCurrentStage] = useState(1);
  const [progressPct, setProgressPct] = useState(10);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev < 7) {
          const next = prev + 1;
          setProgressPct(Math.round((next / 7) * 100));
          return next;
        } else {
          clearInterval(interval);
          if (onComplete) {
            setTimeout(onComplete, 400);
          }
          return 7;
        }
      });
    }, 550);

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div style={{
      maxWidth: '680px',
      margin: '40px auto',
      backgroundColor: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-xl)',
      padding: '36px',
      boxShadow: 'var(--shadow-lg)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Laser scan line effect */}
      <div className="scan-line" style={{ top: '20%' }} />

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px',
          boxShadow: '0 8px 20px rgba(37, 99, 235, 0.4)'
        }}>
          <Cpu size={28} color="#FFFFFF" className="animate-spin" style={{ animationDuration: '3s' }} />
        </div>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#FFFFFF' }}>
          Analyzing Product Label Declarations
        </h3>
        <p style={{ fontSize: '0.85rem', color: '#94A3B8', marginTop: '6px' }}>
          {STAGES[currentStage - 1].message}
        </p>
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          fontWeight: '700',
          color: '#38BDF8',
          marginBottom: '8px'
        }}>
          <span>PROCESSING PIPELINE</span>
          <span>{progressPct}% COMPLETED</span>
        </div>
        <div style={{
          height: '8px',
          backgroundColor: '#070D19',
          borderRadius: '9999px',
          overflow: 'hidden',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{
            height: '100%',
            width: `${progressPct}%`,
            background: 'linear-gradient(90deg, #2563EB, #38BDF8)',
            borderRadius: '9999px',
            transition: 'width 0.4s ease',
            boxShadow: '0 0 12px #38BDF8'
          }} />
        </div>
      </div>

      {/* Stages List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {STAGES.map((stage) => {
          const isDone = stage.id < currentStage;
          const isCurrent = stage.id === currentStage;

          return (
            <div
              key={stage.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isCurrent ? 'rgba(37, 99, 235, 0.12)' : (isDone ? 'rgba(16, 185, 129, 0.05)' : 'transparent'),
                border: isCurrent ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{ flexShrink: 0 }}>
                {isDone ? (
                  <CheckCircle2 size={18} color="#10B981" />
                ) : isCurrent ? (
                  <Loader2 size={18} color="#38BDF8" className="animate-spin" />
                ) : (
                  <div style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    border: '1.5px solid #334155',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.65rem',
                    color: '#64748B'
                  }}>
                    {stage.id}
                  </div>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: '0.85rem',
                  fontWeight: isCurrent ? '700' : (isDone ? '600' : '400'),
                  color: isCurrent ? '#FFFFFF' : (isDone ? '#CBD5E1' : '#64748B')
                }}>
                  {stage.label}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AnalysisProgress;
