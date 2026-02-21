import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Row, Col, Card, Badge, Button, Tabs, Tab, Alert, Form } from 'react-bootstrap';
import {
  FiArrowLeft, FiRefreshCw, FiDownload, FiPlay, FiRotateCcw,
  FiCheck, FiX, FiCheckCircle, FiXCircle,
} from 'react-icons/fi';
import {
  getVideoJob, getTranscript, getEditPlan, getMediaUrl, getDownloadUrl,
  approveEdits, approveAllEdits, retryPipeline,
  triggerIngestion, triggerAnalysis, triggerEditing,
} from '../api/client';
import ProgressIndicator from '../components/ProgressIndicator';
import SegmentScoring from '../components/SegmentScoring';
import TimelineVisualization from '../components/TimelineVisualization';
import VideoComparison from '../components/VideoComparison';

const STATUS_COLORS = {
  pending: 'secondary',
  uploading: 'info',
  extracting_audio: 'info',
  transcribing: 'info',
  analyzing: 'warning',
  generating_edit_plan: 'warning',
  editing: 'primary',
  rendering: 'primary',
  completed: 'success',
  failed: 'danger',
};

function JobDetail() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [editPlan, setEditPlan] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const jobData = await getVideoJob(jobId);
      setJob(jobData);

      if (['analyzing', 'generating_edit_plan', 'editing', 'rendering', 'completed'].includes(jobData.status)) {
        const [transcriptData, editPlanData] = await Promise.all([
          getTranscript(jobId),
          getEditPlan(jobId),
        ]);
        setTranscript(transcriptData);
        setEditPlan(editPlanData);
      }
    } catch (err) {
      console.error('Failed to fetch job data:', err);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // ── Action handlers ──────────────────────────

  const handleRetry = async (fromStep = 'auto') => {
    setActionLoading('retry');
    try {
      const result = await retryPipeline(jobId, fromStep);
      setActionMessage({ type: 'success', text: `Retrying from: ${result.from_step}` });

      // Trigger the appropriate pipeline step
      if (result.from_step === 'ingest') await triggerIngestion(jobId);
      else if (result.from_step === 'analyze') await triggerAnalysis(jobId);
      else if (result.from_step === 'edit') await triggerEditing(jobId);

      fetchData();
    } catch (err) {
      setActionMessage({ type: 'danger', text: err.response?.data?.detail || 'Retry failed' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleApproveEdit = async (editId, approved) => {
    try {
      await approveEdits(jobId, [editId], approved);
      fetchData();
    } catch (err) {
      console.error('Failed to update edit approval:', err);
    }
  };

  const handleApproveAll = async (approved) => {
    setActionLoading('approve');
    try {
      await approveAllEdits(jobId, approved);
      fetchData();
    } catch (err) {
      setActionMessage({ type: 'danger', text: 'Failed to update approvals' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRenderApproved = async () => {
    setActionLoading('render');
    try {
      await triggerEditing(jobId);
      setActionMessage({ type: 'success', text: 'Rendering with approved edits...' });
      fetchData();
    } catch (err) {
      setActionMessage({ type: 'danger', text: err.response?.data?.detail || 'Render failed' });
    } finally {
      setActionLoading(null);
    }
  };

  // ── Render ───────────────────────────────────

  if (loading || !job) {
    return (
      <div className="text-center text-muted py-5">
        <div className="spinner-border" role="status" />
        <p className="mt-3">Loading job details...</p>
      </div>
    );
  }

  const isProcessing = !['completed', 'failed', 'pending'].includes(job.status);
  const hasEditPlan = editPlan.length > 0;
  const approvedCount = editPlan.filter(e => e.approved).length;
  const rejectedCount = editPlan.filter(e => !e.approved).length;

  return (
    <div>
      {/* Action messages */}
      {actionMessage && (
        <Alert
          variant={actionMessage.type}
          dismissible
          onClose={() => setActionMessage(null)}
          className="mb-3"
        >
          {actionMessage.text}
        </Alert>
      )}

      {/* Header */}
      <Row className="mb-4 align-items-center">
        <Col>
          <Link to="/" className="text-decoration-none text-muted mb-2 d-inline-block">
            <FiArrowLeft className="me-1" /> Back to Dashboard
          </Link>
          <h2 className="text-light mb-1">{job.filename}</h2>
          <Badge bg={STATUS_COLORS[job.status] || 'secondary'} className="me-2">
            {job.status.replace(/_/g, ' ').toUpperCase()}
          </Badge>
          <span className="text-muted small">
            Created {new Date(job.created_at).toLocaleString()}
          </span>
        </Col>
        <Col xs="auto" className="d-flex gap-2">
          {/* Download button */}
          {job.status === 'completed' && job.output_path && (
            <a
              href={getDownloadUrl(job.output_path)}
              className="btn btn-success btn-sm"
              download
            >
              <FiDownload className="me-1" /> Download Cleaned
            </a>
          )}
          {/* Retry button */}
          {(job.status === 'failed' || job.status === 'pending') && (
            <Button
              variant="warning"
              size="sm"
              onClick={() => handleRetry('auto')}
              disabled={actionLoading === 'retry'}
            >
              <FiRotateCcw className="me-1" />
              {actionLoading === 'retry' ? 'Retrying...' : 'Retry'}
            </Button>
          )}
          {/* Manual step triggers for pending/failed */}
          {job.status === 'failed' && (
            <div className="dropdown">
              <Button
                variant="outline-warning"
                size="sm"
                className="dropdown-toggle"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                Retry From...
              </Button>
              <ul className="dropdown-menu dropdown-menu-dark">
                <li>
                  <button className="dropdown-item" onClick={() => handleRetry('ingest')}>
                    From Ingestion
                  </button>
                </li>
                <li>
                  <button className="dropdown-item" onClick={() => handleRetry('analyze')}>
                    From Analysis
                  </button>
                </li>
                <li>
                  <button className="dropdown-item" onClick={() => handleRetry('edit')}>
                    From Editing
                  </button>
                </li>
              </ul>
            </div>
          )}
          <Button variant="outline-light" size="sm" onClick={fetchData}>
            <FiRefreshCw className="me-1" /> Refresh
          </Button>
        </Col>
      </Row>

      {/* Video Preview (always show the original if available) */}
      {job.input_path && !isProcessing && job.status !== 'completed' && (
        <Row className="mb-4">
          <Col lg={8}>
            <Card bg="dark" text="white">
              <Card.Header>
                <h5 className="mb-0">Video Preview</h5>
              </Card.Header>
              <Card.Body>
                <video
                  src={getMediaUrl(job.input_path)}
                  controls
                  className="w-100 rounded"
                  style={{ maxHeight: '400px', objectFit: 'contain', background: '#000' }}
                />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Progress */}
      {isProcessing && (
        <Row className="mb-4">
          <Col>
            <Card bg="dark" text="white">
              <Card.Body>
                <ProgressIndicator status={job.status} />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Error Display */}
      {job.status === 'failed' && job.error_message && (
        <Row className="mb-4">
          <Col>
            <Card bg="dark" border="danger" text="white">
              <Card.Header className="text-danger">Error</Card.Header>
              <Card.Body>
                <code className="text-danger">{job.error_message}</code>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Video Comparison + Download (completed) */}
      {job.status === 'completed' && (
        <Row className="mb-4">
          <Col>
            <Card bg="dark" text="white">
              <Card.Header className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Video Comparison</h5>
                {job.output_path && (
                  <a
                    href={getDownloadUrl(job.output_path)}
                    className="btn btn-success btn-sm"
                    download
                  >
                    <FiDownload className="me-1" /> Download Cleaned Video
                  </a>
                )}
              </Card.Header>
              <Card.Body>
                <VideoComparison
                  originalUrl={getMediaUrl(job.input_path)}
                  cleanedUrl={getMediaUrl(job.output_path)}
                />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Tabs: Timeline, Transcript, Edit Plan */}
      {transcript.length > 0 && (
        <Row>
          <Col>
            <Card bg="dark" text="white">
              <Card.Body>
                <Tabs defaultActiveKey={hasEditPlan ? 'editplan' : 'timeline'} className="mb-3" variant="pills">
                  <Tab eventKey="timeline" title="Timeline">
                    <TimelineVisualization
                      transcript={transcript}
                      editPlan={editPlan.filter(e => e.approved)}
                      duration={job.duration_seconds}
                    />
                  </Tab>
                  <Tab eventKey="transcript" title="Transcript">
                    <div className="transcript-viewer">
                      {transcript.map((chunk, idx) => {
                        const matchingEdit = editPlan.find(
                          e => e.approved && e.action === 'remove' &&
                               e.start_time <= chunk.start_time &&
                               e.end_time >= chunk.end_time
                        );
                        const isRemoved = !!matchingEdit;
                        return (
                          <div
                            key={idx}
                            className={`transcript-chunk p-2 mb-1 rounded ${
                              isRemoved ? 'removed-segment' : ''
                            } ${chunk.is_filler ? 'filler-segment' : ''}`}
                          >
                            <span className="text-muted small me-2">
                              [{chunk.start_time.toFixed(1)}s - {chunk.end_time.toFixed(1)}s]
                            </span>
                            <span className={isRemoved ? 'text-decoration-line-through text-muted' : ''}>
                              {chunk.text}
                            </span>
                            {chunk.is_filler && (
                              <Badge bg="warning" className="ms-2">filler</Badge>
                            )}
                            {isRemoved && (
                              <Badge bg="danger" className="ms-2">removed</Badge>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </Tab>
                  <Tab eventKey="scores" title="Segment Scores">
                    <SegmentScoring segments={transcript} />
                  </Tab>
                  <Tab eventKey="editplan" title={`Edit Plan (${approvedCount}/${editPlan.length})`}>
                    <div className="edit-plan-viewer">
                      {editPlan.length === 0 ? (
                        <p className="text-muted">No edits generated yet.</p>
                      ) : (
                        <>
                          {/* Bulk actions */}
                          <div className="d-flex gap-2 mb-3 align-items-center">
                            <Button
                              variant="outline-success"
                              size="sm"
                              onClick={() => handleApproveAll(true)}
                              disabled={actionLoading === 'approve'}
                            >
                              <FiCheckCircle className="me-1" /> Approve All
                            </Button>
                            <Button
                              variant="outline-danger"
                              size="sm"
                              onClick={() => handleApproveAll(false)}
                              disabled={actionLoading === 'approve'}
                            >
                              <FiXCircle className="me-1" /> Reject All
                            </Button>
                            <div className="flex-grow-1" />
                            <small className="text-muted">
                              {approvedCount} approved, {rejectedCount} rejected
                            </small>
                            {job.status !== 'completed' && approvedCount > 0 && (
                              <Button
                                variant="success"
                                size="sm"
                                onClick={handleRenderApproved}
                                disabled={actionLoading === 'render'}
                              >
                                <FiPlay className="me-1" />
                                {actionLoading === 'render' ? 'Rendering...' : 'Render Approved Edits'}
                              </Button>
                            )}
                          </div>

                          {/* Edit items with approve/reject */}
                          {editPlan.map((edit, idx) => (
                            <div
                              key={idx}
                              className={`edit-item p-2 mb-2 rounded ${
                                edit.approved ? 'bg-black' : 'bg-black border border-secondary'
                              }`}
                              style={{ opacity: edit.approved ? 1 : 0.6 }}
                            >
                              <div className="d-flex justify-content-between align-items-start">
                                <div className="flex-grow-1">
                                  <Badge bg={edit.action === 'remove' ? 'danger' : 'warning'} className="me-2">
                                    {edit.action}
                                  </Badge>
                                  <span className="text-light">
                                    {edit.start_time.toFixed(1)}s - {edit.end_time.toFixed(1)}s
                                  </span>
                                  <Badge bg="secondary" className="ms-2">{edit.source}</Badge>
                                  <br />
                                  <small className="text-muted">{edit.reason}</small>
                                  <br />
                                  <small className="text-muted">
                                    Confidence: {(edit.confidence * 100).toFixed(0)}%
                                  </small>
                                </div>
                                <div className="d-flex gap-1 ms-2">
                                  <Button
                                    variant={edit.approved ? 'success' : 'outline-success'}
                                    size="sm"
                                    onClick={() => handleApproveEdit(edit.id, true)}
                                    title="Approve this edit"
                                  >
                                    <FiCheck />
                                  </Button>
                                  <Button
                                    variant={!edit.approved ? 'danger' : 'outline-danger'}
                                    size="sm"
                                    onClick={() => handleApproveEdit(edit.id, false)}
                                    title="Reject this edit"
                                  >
                                    <FiX />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </>
                      )}
                    </div>
                  </Tab>
                </Tabs>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
}

export default JobDetail;
