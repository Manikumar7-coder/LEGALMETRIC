import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Upload, 
  Trash2, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  Image as ImageIcon,
  ArrowRight,
  Shield,
  Layers,
  FileCheck
} from 'lucide-react';
import { inspectionAPI } from '../services/api';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png'];

export const ScanPage = () => {
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageMetadata, setImageMetadata] = useState(null);
  const [productName, setProductName] = useState('');

  const [validationError, setValidationError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // File selection validator
  const validateAndSelectFile = (file) => {
    setValidationError('');
    setUploadSuccess(null);

    if (!file) return;

    // 1. Format validation (JPG, JPEG, PNG)
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError(`Unsupported file format ('.${ext}'). Only JPG, JPEG, and PNG images are allowed.`);
      return;
    }

    // 2. File size validation (Max 10MB, Min 100 bytes)
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      setValidationError(`File size (${sizeMb} MB) exceeds the maximum allowed limit of 10 MB. Please select a smaller image.`);
      return;
    }

    if (file.size < 100) {
      setValidationError('Selected file is empty or unreadable. Please choose a valid image file.');
      return;
    }

    // Create preview URL
    const url = URL.createObjectURL(file);
    setSelectedFile(file);
    setPreviewUrl(url);

    // Format display size
    const sizeFormatted = file.size < 1024 * 1024
      ? `${(file.size / 1024).toFixed(1)} KB`
      : `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

    // Load image to read resolution dimensions
    const img = new Image();
    img.onload = () => {
      setImageMetadata({
        name: file.name,
        size: sizeFormatted,
        rawBytes: file.size,
        width: img.width,
        height: img.height,
        format: ext.toUpperCase()
      });
    };
    img.onerror = () => {
      setValidationError('Unable to decode image file. Please verify that the file is not corrupted.');
      handleRemove();
    };
    img.src = url;

    // Product name is intentionally NOT derived from the filename.
    // It will be extracted from the image via OCR after inspection.
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSelectFile(file);
    }
  };

  // Remove image
  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageMetadata(null);
    setValidationError('');
    setUploadSuccess(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Replace image: open file chooser directly
  const handleReplace = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  // Drag & Drop
  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSelectFile(file);
    }
  };

  // Submit image for inspection
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      setValidationError('Please select a commodity package image before submitting.');
      return;
    }

    setValidationError('');
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (productName) {
        formData.append('product_name', productName);
      }

      // Submit uploaded image for full OCR extraction and legal compliance analysis
      const res = await inspectionAPI.analyze(formData);
      setUploadSuccess(res);
      setIsUploading(false);
    } catch (err) {
      setIsUploading(false);
      setValidationError(
        err.response?.data?.detail || 'Failed to upload product image. Please check the file and try again.'
      );
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-primary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Commodity Intake
          </span>
        </div>
        <h1 style={{ fontSize: '1.65rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>
          Upload Packaged Product Image
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Select a packaged commodity photograph (JPG, JPEG, PNG) to submit as the primary inspection input.
        </p>
      </div>

      {/* Hidden native file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />

      {/* Validation Error Alert */}
      {validationError && (
        <div className="alert alert-error">
          <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>{validationError}</div>
        </div>
      )}

      {/* Successful Upload Banner */}
      {uploadSuccess && (
        <div className="card" style={{
          borderColor: 'var(--status-compliant)',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10B981'
              }}>
                <CheckCircle2 size={24} />
              </div>
              <div>
                <span className="badge badge-compliant" style={{ fontSize: '0.68rem' }}>
                  {uploadSuccess.compliance_status || 'UPLOADED'}
                </span>
                <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px' }}>
                  {uploadSuccess.product_name}
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Record Ref: <b>#INS-{uploadSuccess.id}</b> • Primary image input registered
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={handleRemove}
                className="btn-secondary btn-sm"
              >
                Upload Another Commodity
              </button>
              <Link
                to={`/inspection/${uploadSuccess.id}`}
                className="btn-primary btn-sm"
              >
                View Record Details <ArrowRight size={14} />
              </Link>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '10px',
            backgroundColor: 'var(--bg-canvas)',
            padding: '12px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.78rem'
          }}>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>File Name: </span>
              <b style={{ color: 'var(--text-primary)' }}>{uploadSuccess.original_filename}</b>
            </div>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>File Size: </span>
              <b style={{ color: 'var(--text-primary)' }}>{uploadSuccess.size_formatted}</b>
            </div>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Dimensions: </span>
              <b style={{ color: 'var(--text-primary)' }}>{uploadSuccess.dimensions?.width} × {uploadSuccess.dimensions?.height} px</b>
            </div>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Format: </span>
              <b style={{ color: 'var(--text-primary)' }}>{uploadSuccess.format}</b>
            </div>
          </div>
        </div>
      )}

      {/* Main Upload Card */}
      {!uploadSuccess && (
        <div className="card" style={{ padding: '28px' }}>
          {/* Commodity Name Input */}
          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label className="form-label">
              Packaged Commodity Name (Optional Label Description)
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Basmati Rice, Sunflower Oil, Salted Wafers"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
            <span className="form-hint">
              Leave blank to automatically extract from the uploaded package image via OCR.
            </span>
          </div>

          {/* Upload Dropzone / Selector */}
          {!previewUrl ? (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: '2px dashed var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '50px 20px',
                textAlign: 'center',
                backgroundColor: 'var(--bg-canvas)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '12px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
                e.currentTarget.style.backgroundColor = 'rgba(2, 132, 199, 0.04)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
                e.currentTarget.style.backgroundColor = 'var(--bg-canvas)';
              }}
            >
              <div style={{
                width: '54px',
                height: '54px',
                borderRadius: '16px',
                backgroundColor: 'rgba(2, 132, 199, 0.08)',
                border: '1px solid rgba(2, 132, 199, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-primary)'
              }}>
                <Upload size={26} />
              </div>

              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                  Select an image from your device
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Drag & drop your commodity package label photo here, or browse files
                </p>
              </div>

              <div style={{
                display: 'flex',
                gap: '8px',
                marginTop: '6px',
                flexWrap: 'wrap',
                justifyContent: 'center'
              }}>
                <span className="badge badge-neutral">Formats: JPG, JPEG, PNG</span>
                <span className="badge badge-neutral">Maximum Size: 10 MB</span>
              </div>
            </div>
          ) : (
            /* Image Preview & Management View */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Preview Controls Bar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px',
                padding: '12px 16px',
                backgroundColor: 'var(--bg-canvas)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ImageIcon size={18} color="#38BDF8" />
                  <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                    Label Image Preview
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    type="button"
                    onClick={handleReplace}
                    className="btn-secondary btn-sm"
                    title="Choose a different image file"
                  >
                    <RefreshCw size={14} /> Replace Image
                  </button>
                  <button
                    type="button"
                    onClick={handleRemove}
                    className="btn-danger btn-sm"
                    title="Remove selected image"
                  >
                    <Trash2 size={14} /> Remove Image
                  </button>
                </div>
              </div>

              {/* Image Preview Container */}
              <div className={isUploading ? "scan-container" : ""} style={{
                position: 'relative',
                backgroundColor: 'var(--bg-canvas)',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                border: '1px solid var(--border-subtle)',
                maxHeight: '440px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px'
              }}>
                <img
                  src={previewUrl}
                  alt="Packaged product label preview"
                  style={{
                    maxWidth: '100%',
                    maxHeight: '400px',
                    objectFit: 'contain',
                    borderRadius: '6px',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.6)'
                  }}
                />
                
                {isUploading && (
                  <>
                    <div className="scan-line"></div>
                    <div className="scan-overlay"></div>
                    <div className="targeting-bracket targeting-tl"></div>
                    <div className="targeting-bracket targeting-tr"></div>
                    <div className="targeting-bracket targeting-bl"></div>
                    <div className="targeting-bracket targeting-br"></div>
                    
                    {/* Bounding boxes that appear during scanning for effect */}
                    <div className="bounding-box" style={{top: '30%', left: '35%', width: '30%', height: '10%', animation: 'fadeIn 0.5s 1s forwards', opacity: 0}}>
                       <span className="bounding-box-label">DETECTING...</span>
                    </div>
                    <div className="bounding-box" style={{top: '55%', left: '20%', width: '20%', height: '8%', animation: 'fadeIn 0.5s 1.5s forwards', opacity: 0}}>
                       <span className="bounding-box-label">EXTRACTING...</span>
                    </div>
                  </>
                )}
              </div>

              {/* File Metadata Details */}
              {imageMetadata && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                  gap: '10px',
                  padding: '14px',
                  backgroundColor: 'var(--bg-canvas)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.8rem'
                }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: '700' }}>
                      File Name
                    </span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: '600', wordBreak: 'break-all' }}>
                      {imageMetadata.name}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: '700' }}>
                      File Size
                    </span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>
                      {imageMetadata.size}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: '700' }}>
                      Image Resolution
                    </span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>
                      {imageMetadata.width} × {imageMetadata.height} px
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: '700' }}>
                      Image Format
                    </span>
                    <span style={{ color: 'var(--accent-primary)', fontWeight: '700' }}>
                      {imageMetadata.format}
                    </span>
                  </div>
                </div>
              )}

              {/* Submit Action */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '6px' }}>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="btn-secondary"
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="btn-primary"
                  disabled={isUploading}
                  style={{ padding: '12px 28px' }}
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid #FFFFFF', borderTopColor: 'transparent', borderRadius: '50%' }} />
                      Uploading Image...
                    </>
                  ) : (
                    <>
                      <FileCheck size={18} /> Submit Image for Inspection
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Statutory Enforcement Notice */}
      <div style={{
        padding: '16px 20px',
        backgroundColor: 'var(--bg-canvas)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px'
      }}>
        <Shield size={20} color="#38BDF8" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          <b>Legal Metrology Physical Intake:</b> In compliance with the Legal Metrology (Packaged Commodities) Rules, 2011, the uploaded product package photograph serves as the sole ground truth for regulatory verification. No pre-seeded commodity database lookups are performed.
        </div>
      </div>
    </div>
  );
};

export default ScanPage;
