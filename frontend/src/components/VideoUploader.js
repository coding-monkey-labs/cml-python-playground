import React, { useState, useRef, useMemo } from 'react';
import { Button, ProgressBar, Alert, Badge, Row, Col } from 'react-bootstrap';
import { FiUploadCloud, FiFile, FiX, FiPlay } from 'react-icons/fi';
import { uploadVideo, uploadBatch } from '../api/client';

const ALLOWED_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
const MAX_SIZE = 2 * 1024 * 1024 * 1024; // 2 GB

function VideoUploader({ onUploadComplete }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleFilesSelect = (selectedFiles) => {
    setError(null);
    const validFiles = [];

    for (const file of selectedFiles) {
      if (!ALLOWED_TYPES.includes(file.type)) {
        setError(`Skipped "${file.name}": unsupported type.`);
        continue;
      }
      if (file.size > MAX_SIZE) {
        setError(`Skipped "${file.name}": exceeds 2 GB limit.`);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
      // Preview the first file
      if (files.length === 0 && validFiles.length > 0) {
        setPreviewUrl(URL.createObjectURL(validFiles[0]));
      }
    }
  };

  const removeFile = (index) => {
    setFiles(prev => {
      const updated = prev.filter((_, i) => i !== index);
      if (index === 0 && previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(updated.length > 0 ? URL.createObjectURL(updated[0]) : null);
      }
      return updated;
    });
  };

  const selectPreview = (index) => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(files[index]));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      handleFilesSelect(Array.from(e.dataTransfer.files));
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      if (files.length === 1) {
        await uploadVideo(files[0], 'cleaner', setProgress);
      } else {
        await uploadBatch(files, 'cleaner', setProgress);
      }
      // Cleanup
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setFiles([]);
      setPreviewUrl(null);
      setProgress(0);
      if (onUploadComplete) onUploadComplete();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const totalSize = useMemo(
    () => files.reduce((sum, f) => sum + f.size, 0),
    [files]
  );

  return (
    <div>
      {error && <Alert variant="danger" dismissible onClose={() => setError(null)}>{error}</Alert>}

      <Row>
        {/* Left: Drop zone + file list */}
        <Col md={previewUrl ? 7 : 12}>
          {/* Drop Zone */}
          <div
            className={`drop-zone ${dragOver ? 'drag-over' : ''} ${files.length > 0 ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              multiple
              className="d-none"
              onChange={(e) => e.target.files.length > 0 && handleFilesSelect(Array.from(e.target.files))}
            />

            {files.length > 0 ? (
              <div className="text-center">
                <FiFile size={32} className="text-success mb-2" />
                <p className="mb-1 fw-bold">
                  {files.length} file{files.length > 1 ? 's' : ''} selected
                </p>
                <small className="text-muted">
                  {(totalSize / (1024 * 1024)).toFixed(1)} MB total
                  {' '} | Click to add more
                </small>
              </div>
            ) : (
              <div className="text-center">
                <FiUploadCloud size={48} className="text-muted mb-2" />
                <p className="mb-1">Drag & drop video files here</p>
                <small className="text-muted">
                  or click to browse | Multiple files supported | MP4, MOV, AVI, MKV, WebM (max 2 GB each)
                </small>
              </div>
            )}
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="mt-2">
              {files.map((file, idx) => (
                <div key={idx} className="d-flex align-items-center justify-content-between p-2 mb-1 bg-black rounded">
                  <div className="d-flex align-items-center">
                    <Button
                      variant="link"
                      size="sm"
                      className="text-info p-0 me-2"
                      onClick={(e) => { e.stopPropagation(); selectPreview(idx); }}
                      title="Preview"
                    >
                      <FiPlay />
                    </Button>
                    <small className="text-light">{file.name}</small>
                    <Badge bg="secondary" className="ms-2">
                      {(file.size / (1024 * 1024)).toFixed(1)} MB
                    </Badge>
                  </div>
                  <Button
                    variant="link"
                    size="sm"
                    className="text-danger p-0"
                    onClick={(e) => { e.stopPropagation(); removeFile(idx); }}
                  >
                    <FiX />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Col>

        {/* Right: Video preview */}
        {previewUrl && (
          <Col md={5}>
            <div className="mb-2">
              <small className="text-muted text-uppercase fw-bold">Preview</small>
            </div>
            <video
              src={previewUrl}
              controls
              className="w-100 rounded"
              style={{ maxHeight: '300px', objectFit: 'contain', background: '#000' }}
            />
          </Col>
        )}
      </Row>

      {/* Progress Bar */}
      {uploading && (
        <ProgressBar
          now={progress}
          label={`${progress}%`}
          animated
          striped
          variant="success"
          className="mt-3"
        />
      )}

      {/* Upload Button */}
      <div className="mt-3 d-flex justify-content-end">
        <Button
          variant="success"
          onClick={handleUpload}
          disabled={files.length === 0 || uploading}
          size="lg"
        >
          {uploading
            ? 'Uploading...'
            : files.length > 1
              ? `Upload & Process ${files.length} Videos`
              : 'Upload & Process'
          }
        </Button>
      </div>
    </div>
  );
}

export default VideoUploader;
