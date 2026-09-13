import React, { useState, useEffect, useRef } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Download, 
  Eye, 
  Layers, 
  AlertOctagon, 
  CheckCircle2, 
  AlertTriangle,
  Info,
  Maximize2,
  Crosshair,
  FileSearch
} from 'lucide-react';

export const EvidenceViewer = ({ 
  imageUrl, 
  boundingBoxes = [], 
  evidence = null,
  violations = [], 
  selectedViolation = null,
  onSelectViolation = () => {},
  productName = "Product Label" 
}) => {
  const [zoom, setZoom] = useState(1);
  const [filterMode, setFilterMode] = useState('ALL'); // 'ALL' | 'VIOLATIONS_ONLY' | 'NONE'
  const [activeBoxIndex, setActiveBoxIndex] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [naturalSize, setNaturalSize] = useState({ width: 800, height: 1000 });
  const containerRef = useRef(null);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.75));
  const handleReset = () => setZoom(1);

  const handleImageLoad = (e) => {
    const { naturalWidth, naturalHeight } = e.target;
    if (naturalWidth && naturalHeight) {
      setNaturalSize({ width: naturalWidth, height: naturalHeight });
    }
  };

  // Compile unified visual regions from evidence items or bounding boxes
  const visualRegions = React.useMemo(() => {
    // Priority 1: Use structured evidence items if provided
    if (evidence && Array.isArray(evidence.items) && evidence.items.length > 0) {
      return evidence.items
        .filter(item => item.bounding_box && item.bounding_box.length >= 4)
        .map((item, idx) => ({
          id: item.evidence_id || `ev_${idx}`,
          box: item.bounding_box,
          text: item.ocr_text || item.declaration_value || '',
          confidence: item.confidence || 0,
          declaration: item.associated_declaration || '',
          rule: item.associated_rule || '',
          legalReference: item.legal_reference || '',
          isViolation: Boolean(item.is_violation),
          violationDetails: item.violation_details,
          visualStatus: item.visual_status
        }));
    }

    // Priority 2: Cross-reference raw boundingBoxes with violations list
    return (boundingBoxes || []).map((b, idx) => {
      const box = b.box || [];
      const text = b.text || '';
      const conf = b.confidence || 0;

      // Check if this box matches any violation by text or evidence_reference
      let matchedViolation = null;
      for (const v of violations) {
        const evRef = v.evidence_reference || {};
        if (evRef.raw_text && text && evRef.raw_text.toLowerCase().includes(text.toLowerCase())) {
          matchedViolation = v;
          break;
        }
        if (v.field && text && text.toLowerCase().includes(v.field.toLowerCase())) {
          matchedViolation = v;
          break;
        }
      }

      return {
        id: `box_${idx}`,
        box,
        text,
        confidence: conf,
        declaration: matchedViolation ? matchedViolation.field : (b.declaration || 'Detected Text'),
        rule: matchedViolation ? matchedViolation.rule_id : (b.rule || null),
        legalReference: matchedViolation ? matchedViolation.rule_reference : null,
        isViolation: Boolean(matchedViolation),
        violationDetails: matchedViolation,
        visualStatus: matchedViolation ? 'VIOLATION' : 'DETECTED_ON_IMAGE'
      };
    });
  }, [evidence, boundingBoxes, violations]);

  // Synchronize when selectedViolation prop changes externally
  useEffect(() => {
    if (!selectedViolation) {
      return;
    }

    const targetRule = (selectedViolation.rule_id || '').toLowerCase().trim();
    const targetField = (selectedViolation.field || '').toLowerCase().trim();

    // Find corresponding visual region
    const matchedRegion = visualRegions.find(r => 
      (r.rule && r.rule.toLowerCase().trim() === targetRule) ||
      (r.declaration && r.declaration.toLowerCase().trim() === targetField)
    );

    if (matchedRegion) {
      setSelectedItem(matchedRegion);
    } else {
      // Missing field violation: set a synthetic missing evidence item for inspection
      setSelectedItem({
        id: `missing_${selectedViolation.rule_id}`,
        box: null,
        text: 'Visual evidence region not detected on label',
        confidence: 0,
        declaration: selectedViolation.field,
        rule: selectedViolation.rule_id,
        legalReference: selectedViolation.rule_reference,
        isViolation: true,
        violationDetails: selectedViolation,
        visualStatus: 'MISSING_FROM_IMAGE'
      });
    }
  }, [selectedViolation, visualRegions]);

  const handleSelectRegion = (region) => {
    setSelectedItem(region);
    if (region.isViolation && region.violationDetails) {
      onSelectViolation(region.violationDetails);
    }
  };

  const totalViolationsCount = visualRegions.filter(r => r.isViolation).length;

  return (
    <div id="evidence-viewer" className="card" style={{ padding: '22px', backgroundColor: '#070D19', border: '1px solid var(--border-subtle)' }}>
      {/* Controls & Mode Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            backgroundColor: 'rgba(56, 189, 248, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid rgba(56, 189, 248, 0.3)'
          }}>
            <Layers size={18} color="#38BDF8" />
          </div>
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: '800', color: '#FFFFFF', letterSpacing: '-0.01em' }}>
              Photographic Label Visual Evidence
            </h4>
            <span style={{ fontSize: '0.74rem', color: '#94A3B8' }}>
              {visualRegions.length} OCR regions mapped • {totalViolationsCount} violation zones highlighted
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {/* Overlay Filter Toggle */}
          <div style={{ display: 'flex', backgroundColor: '#0F1D36', borderRadius: 'var(--radius-md)', padding: '3px', border: '1px solid var(--border-subtle)' }}>
            <button
              onClick={() => setFilterMode('ALL')}
              style={{
                padding: '5px 10px',
                fontSize: '0.75rem',
                fontWeight: '600',
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: filterMode === 'ALL' ? '#1E2E4E' : 'transparent',
                color: filterMode === 'ALL' ? '#38BDF8' : '#94A3B8'
              }}
            >
              All Regions ({visualRegions.length})
            </button>
            <button
              onClick={() => setFilterMode('VIOLATIONS_ONLY')}
              style={{
                padding: '5px 10px',
                fontSize: '0.75rem',
                fontWeight: '600',
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: filterMode === 'VIOLATIONS_ONLY' ? 'rgba(239, 68, 68, 0.25)' : 'transparent',
                color: filterMode === 'VIOLATIONS_ONLY' ? '#F87171' : '#94A3B8'
              }}
            >
              Violations Only ({totalViolationsCount})
            </button>
            <button
              onClick={() => setFilterMode('NONE')}
              style={{
                padding: '5px 10px',
                fontSize: '0.75rem',
                fontWeight: '600',
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: filterMode === 'NONE' ? '#1E2E4E' : 'transparent',
                color: filterMode === 'NONE' ? '#E2E8F0' : '#94A3B8'
              }}
            >
              Hide
            </button>
          </div>

          {/* Zoom controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: '#0F1D36', borderRadius: 'var(--radius-md)', padding: '2px 4px', border: '1px solid var(--border-subtle)' }}>
            <button onClick={handleZoomOut} className="btn-secondary" style={{ padding: '5px 8px', border: 'none', backgroundColor: 'transparent' }} title="Zoom Out">
              <ZoomOut size={14} />
            </button>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#94A3B8', minWidth: '38px', textAlign: 'center' }}>
              {Math.round(zoom * 100)}%
            </span>
            <button onClick={handleZoomIn} className="btn-secondary" style={{ padding: '5px 8px', border: 'none', backgroundColor: 'transparent' }} title="Zoom In">
              <ZoomIn size={14} />
            </button>
            <button onClick={handleReset} className="btn-secondary" style={{ padding: '5px 8px', border: 'none', backgroundColor: 'transparent' }} title="Reset Zoom">
              <RotateCcw size={14} />
            </button>
          </div>

          <a
            href={imageUrl}
            download={`SafeMetric_Evidence_${productName.replace(/\s+/g, '_')}.png`}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
            style={{ padding: '7px 11px', fontSize: '0.78rem' }}
            title="Download Original Photographic Ground Truth"
          >
            <Download size={14} /> Download Image
          </a>
        </div>
      </div>

      {/* Main Evidence Layout: Canvas on Left, Inspector Drawer on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '16px', alignItems: 'stretch' }}>
        {/* Canvas Area */}
        <div 
          ref={containerRef}
          style={{
            position: 'relative',
            height: '490px',
            backgroundColor: '#030712',
            borderRadius: 'var(--radius-md)',
            overflow: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid var(--border-subtle)',
            padding: '16px'
          }}
        >
          <div style={{
            position: 'relative',
            display: 'inline-block',
            transform: `scale(${zoom})`,
            transformOrigin: 'center center',
            transition: 'transform 0.15s ease'
          }}>
            {/* Original Unmodified Photographic Image */}
            <img
              src={imageUrl}
              alt={productName}
              onLoad={handleImageLoad}
              style={{
                maxWidth: '100%',
                maxHeight: '440px',
                objectFit: 'contain',
                borderRadius: '6px',
                boxShadow: '0 10px 30px rgba(0,0,0,0.7)',
                display: 'block',
                userSelect: 'none'
              }}
            />

            {/* Bounding Box Overlays */}
            {filterMode !== 'NONE' && visualRegions.length > 0 && (
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: 'none'
              }}>
                {visualRegions.map((region, idx) => {
                  if (filterMode === 'VIOLATIONS_ONLY' && !region.isViolation) {
                    return null;
                  }

                  const box = region.box;
                  if (!box || box.length < 4) return null;

                  const imgW = naturalSize.width || 800;
                  const imgH = naturalSize.height || 1000;
                  const xs = box.map(pt => pt[0]);
                  const ys = box.map(pt => pt[1]);
                  const minX = Math.min(...xs);
                  const maxX = Math.max(...xs);
                  const minY = Math.min(...ys);
                  const maxY = Math.max(...ys);
                  const left = (minX / imgW) * 100;
                  const top = (minY / imgH) * 100;
                  const width = ((maxX - minX) / imgW) * 100;
                  const height = ((maxY - minY) / imgH) * 100;

                  const isHovered = activeBoxIndex === idx;
                  const isSelected = selectedItem && selectedItem.id === region.id;
                  const isViol = region.isViolation;

                  // Highlighting styles
                  let borderColor = 'rgba(56, 189, 248, 0.7)';
                  let bgColor = 'rgba(37, 99, 235, 0.12)';
                  let boxShadow = 'none';

                  if (isViol) {
                    borderColor = isSelected ? '#EF4444' : 'rgba(239, 68, 68, 0.85)';
                    bgColor = isSelected ? 'rgba(239, 68, 68, 0.4)' : 'rgba(239, 68, 68, 0.2)';
                    boxShadow = isSelected ? '0 0 14px rgba(239, 68, 68, 0.8)' : '0 0 6px rgba(239, 68, 68, 0.3)';
                  } else if (isSelected) {
                    borderColor = '#38BDF8';
                    bgColor = 'rgba(56, 189, 248, 0.35)';
                    boxShadow = '0 0 12px rgba(56, 189, 248, 0.7)';
                  } else if (isHovered) {
                    borderColor = '#60A5FA';
                    bgColor = 'rgba(56, 189, 248, 0.25)';
                  }

                  return (
                    <div
                      key={region.id || idx}
                      onClick={() => handleSelectRegion(region)}
                      onMouseEnter={() => setActiveBoxIndex(idx)}
                      onMouseLeave={() => setActiveBoxIndex(null)}
                      style={{
                        position: 'absolute',
                        left: `${left}%`,
                        top: `${top}%`,
                        width: `${Math.max(width, 3)}%`,
                        height: `${Math.max(height, 2)}%`,
                        border: isSelected ? `2.5px solid ${borderColor}` : `1.5px solid ${borderColor}`,
                        backgroundColor: bgColor,
                        boxShadow: boxShadow,
                        pointerEvents: 'auto',
                        cursor: 'pointer',
                        borderRadius: '3px',
                        transition: 'all 0.15s ease',
                        zIndex: isSelected ? 20 : (isViol ? 10 : 5)
                      }}
                      title={`${region.declaration || 'Text'}: "${region.text}" (${region.confidence}%)`}
                    >
                      {/* Violation Marker Badge */}
                      {isViol && (
                        <div style={{
                          position: 'absolute',
                          top: '-10px',
                          left: '-10px',
                          width: '18px',
                          height: '18px',
                          borderRadius: '50%',
                          backgroundColor: '#EF4444',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: '0 2px 6px rgba(0,0,0,0.8)',
                          color: '#FFFFFF',
                          fontSize: '10px',
                          fontWeight: 'bold'
                        }}>
                          !
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Evidence Inspector Side Panel */}
        <div style={{
          backgroundColor: '#0A1324',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '18px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '14px'
        }}>
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid var(--border-subtle)',
              paddingBottom: '10px',
              marginBottom: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Crosshair size={16} color="#38BDF8" />
                <h5 style={{ fontSize: '0.88rem', fontWeight: '800', color: '#FFFFFF' }}>
                  Visual Inspector
                </h5>
              </div>
              <span className={`badge ${selectedItem?.isViolation ? 'badge-noncompliant' : (selectedItem ? 'badge-compliant' : 'badge-subtle')}`} style={{ fontSize: '0.68rem' }}>
                {selectedItem ? (selectedItem.isViolation ? 'VIOLATION ZONE' : 'COMPLIANT REGION') : 'STANDBY'}
              </span>
            </div>

            {selectedItem ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* Visual Status Banner */}
                {selectedItem.visualStatus === 'MISSING_FROM_IMAGE' ? (
                  <div style={{
                    padding: '10px 12px',
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '8px'
                  }}>
                    <AlertOctagon size={16} color="#EF4444" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div style={{ fontSize: '0.75rem', color: '#FCA5A5', lineHeight: 1.3 }}>
                      <b>Visual Evidence Region Not Detected on Label:</b> Mandatory declaration was not detected on this scanned packaging substrate.
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '8px 12px',
                    backgroundColor: selectedItem.isViolation ? 'rgba(239, 68, 68, 0.15)' : 'rgba(56, 189, 248, 0.1)',
                    border: `1px solid ${selectedItem.isViolation ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.25)'}`,
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase' }}>
                      Optical Confidence
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: '800', color: selectedItem.confidence >= 80 ? '#10B981' : '#EF4444' }}>
                      {selectedItem.confidence}%
                    </span>
                  </div>
                )}

                {/* Associated Declaration Name */}
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Associated Statutory Declaration
                  </div>
                  <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#FFFFFF', marginTop: '2px' }}>
                    {selectedItem.declaration ? selectedItem.declaration.replace(/_/g, ' ').toUpperCase() : 'General Declaration'}
                  </div>
                </div>

                {/* Verbatim OCR Text */}
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Extracted Verbatim Text (OCR)
                  </div>
                  <div style={{
                    fontSize: '0.84rem',
                    color: '#CBD5E1',
                    marginTop: '4px',
                    padding: '10px 12px',
                    backgroundColor: '#030712',
                    borderRadius: '6px',
                    border: '1px solid var(--border-subtle)',
                    fontFamily: 'monospace',
                    lineHeight: 1.35,
                    maxHeight: '85px',
                    overflowY: 'auto',
                    wordBreak: 'break-word'
                  }}>
                    {selectedItem.text || '— No textual content —'}
                  </div>
                </div>

                {/* Associated Statutory Rule */}
                {selectedItem.rule && (
                  <div>
                    <div style={{ fontSize: '0.7rem', fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Statutory Rule Reference
                    </div>
                    <div style={{ fontSize: '0.78rem', fontWeight: '700', color: '#38BDF8', marginTop: '2px' }}>
                      {selectedItem.rule}
                    </div>
                    {selectedItem.legalReference && (
                      <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '2px' }}>
                        {selectedItem.legalReference}
                      </div>
                    )}
                  </div>
                )}

                {/* Violation Details if applicable */}
                {selectedItem.isViolation && selectedItem.violationDetails && (
                  <div style={{
                    padding: '10px 12px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '6px'
                  }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#EF4444', textTransform: 'uppercase' }}>
                      Statutory Non-Compliance Issue
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#FCA5A5', marginTop: '4px', lineHeight: 1.35 }}>
                      {selectedItem.violationDetails.issue || 'Non-compliance detected against statutory labeling rules.'}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '36px 12px',
                color: '#64748B',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px'
              }}>
                <FileSearch size={32} color="#334155" />
                <span style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
                  Select a violation card or click any highlighted bounding box on the package image to inspect OCR text & optical confidence.
                </span>
              </div>
            )}
          </div>

          {/* Bottom Footnote */}
          <div style={{
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '10px',
            fontSize: '0.7rem',
            color: '#64748B',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span>Visual Evidence ID: #EVD-{productName ? productName.slice(0, 8).toUpperCase() : 'PKG'}</span>
            <span>Unmodified Image</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvidenceViewer;
