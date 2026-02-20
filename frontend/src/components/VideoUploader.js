import React, { useState, useRef } from 'react';
import { Button, ProgressBar, Alert, Form } from 'react-bootstrap';
import { FiUploadCloud, FiFile } from 'react-icons/fi';
import { uploadVideo } from '../api/client';

const ALLOWED_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
const MAX_SIZE = 2 * 1024 * 1024 * 1024; // 2 GB

function VideoUploader({ onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (selectedFile) => {
    setError(null);

    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      setError('Unsupported file type. Please upload MP4, MOV, AVI, MKV, or WebM.');
      return;
    }

    if (selectedFile.size > MAX_SIZE) {
      setError('File too large. Maximum size is 2 GB.');
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      await uploadVideo(file, 'cleaner', setProgress);
      setFile(null);
      setProgress(0);
      if (onUploadComplete) onUploadComplete();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      {error && <Alert variant="danger" dismissible onClose={() => setError(null)}>{error}</Alert>}

      {/* Drop Zone */}
      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          className="d-none"
          onChange={(e) => e.target.files[0] && handleFileSelect(e.target.files[0])}
        />

        {file ? (
          <div className="text-center">
            <FiFile size={40} className="text-success mb-2" />
            <p className="mb-1 fw-bold">{file.name}</p>
            <small className="text-muted">
              {(file.size / (1024 * 1024)).toFixed(1)} MB
            </small>
          </div>
        ) : (
          <div className="text-center">
            <FiUploadCloud size={48} className="text-muted mb-2" />
            <p className="mb-1">Drag & drop a video file here</p>
            <small className="text-muted">or click to browse (MP4, MOV, AVI, MKV, WebM - max 2 GB)</small>
          </div>
        )}
      </div>

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
          disabled={!file || uploading}
          size="lg"
        >
          {uploading ? 'Uploading...' : 'Upload & Process'}
        </Button>
      </div>
    </div>
  );
}

export default VideoUploader;
