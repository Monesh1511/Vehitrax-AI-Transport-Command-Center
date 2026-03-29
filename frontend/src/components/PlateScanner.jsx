import React, { useState, useRef } from 'react';

export function PlateScanner({ onPlateDetected }) {
  const [isScanning, setIsScanning] = useState(false);
  const [detectedPlates, setDetectedPlates] = useState([]);
  const [previewImage, setPreviewImage] = useState(null);
  const fileInputRef = useRef(null);
  
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewImage(e.target.result);
    };
    reader.readAsDataURL(file);

    // Scan the image
    setIsScanning(true);
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${apiUrl}/api/scanner/scan-and-save`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setDetectedPlates(result.plates || []);
        
        // Notify parent component
        if (onPlateDetected && result.plates) {
          onPlateDetected(result.plates);
        }
      } else {
        console.error('Scan failed:', response.statusText);
      }
    } catch (error) {
      console.error('Error scanning image:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      if (fileInputRef.current) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInputRef.current.files = dataTransfer.files;
        fileInputRef.current.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  };

  return (
    <div className="plate-scanner">
      <h3>Plate Scanner</h3>
      
      <div 
        className="upload-zone"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: '2px dashed var(--border-color)',
          borderRadius: '8px',
          padding: '2rem',
          textAlign: 'center',
          cursor: 'pointer',
          marginBottom: '1rem',
          backgroundColor: 'var(--bg-secondary)'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {isScanning ? (
          <div className="scanning-indicator">
            <div className="spinner"></div>
            <p>Scanning for plates...</p>
          </div>
        ) : (
          <>
            <p style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
              Click to upload or drag & drop
            </p>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>
              PNG, JPG, GIF up to 10MB
            </p>
          </>
        )}
      </div>

      {previewImage && (
        <div className="preview-section" style={{ marginTop: '1rem' }}>
          <h4>Preview</h4>
          <img 
            src={previewImage} 
            alt="Preview" 
            style={{
              maxWidth: '100%',
              maxHeight: '300px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)'
            }}
          />
        </div>
      )}

      {detectedPlates.length > 0 && (
        <div className="detected-plates" style={{ marginTop: '1.5rem' }}>
          <h4>Detected Plates ({detectedPlates.length})</h4>
          <div className="plates-list">
            {detectedPlates.map((plate, index) => (
              <div 
                key={index}
                className="plate-item"
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  marginBottom: '0.5rem',
                  borderLeft: '4px solid var(--success)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 'bold', fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                    {plate.plate_number}
                  </span>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    {(plate.confidence * 100).toFixed(1)}% confidence
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Bus ID: {plate.bus_id} | Event ID: {plate.event_id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
