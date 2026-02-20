import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Row, Col, Card, Badge, Button, Tabs, Tab } from 'react-bootstrap';
import { FiArrowLeft, FiRefreshCw } from 'react-icons/fi';
import { getVideoJob, getTranscript, getEditPlan, getMediaUrl } from '../api/client';
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

  if (loading || !job) {
    return (
      <div className="text-center text-muted py-5">
        <div className="spinner-border" role="status" />
        <p className="mt-3">Loading job details...</p>
      </div>
    );
  }

  const isProcessing = !['completed', 'failed', 'pending'].includes(job.status);

  return (
    <div>
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
        <Col xs="auto">
          <Button variant="outline-light" size="sm" onClick={fetchData}>
            <FiRefreshCw className="me-1" /> Refresh
          </Button>
        </Col>
      </Row>

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

      {/* Video Comparison (only when completed) */}
      {job.status === 'completed' && (
        <Row className="mb-4">
          <Col>
            <Card bg="dark" text="white">
              <Card.Header>
                <h5 className="mb-0">Video Comparison</h5>
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
                <Tabs defaultActiveKey="timeline" className="mb-3" variant="pills">
                  <Tab eventKey="timeline" title="Timeline">
                    <TimelineVisualization
                      transcript={transcript}
                      editPlan={editPlan}
                      duration={job.duration_seconds}
                    />
                  </Tab>
                  <Tab eventKey="transcript" title="Transcript">
                    <div className="transcript-viewer">
                      {transcript.map((chunk, idx) => {
                        const isRemoved = editPlan.some(
                          e => e.action === 'remove' &&
                               e.start_time <= chunk.start_time &&
                               e.end_time >= chunk.end_time
                        );
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
                              <Badge bg="warning" className="ms-2" size="sm">filler</Badge>
                            )}
                            {isRemoved && (
                              <Badge bg="danger" className="ms-2" size="sm">removed</Badge>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </Tab>
                  <Tab eventKey="scores" title="Segment Scores">
                    <SegmentScoring segments={transcript} />
                  </Tab>
                  <Tab eventKey="editplan" title="Edit Plan">
                    <div className="edit-plan-viewer">
                      {editPlan.length === 0 ? (
                        <p className="text-muted">No edits generated yet.</p>
                      ) : (
                        editPlan.map((edit, idx) => (
                          <div key={idx} className="edit-item p-2 mb-2 rounded bg-black">
                            <div className="d-flex justify-content-between">
                              <span>
                                <Badge bg={edit.action === 'remove' ? 'danger' : 'warning'} className="me-2">
                                  {edit.action}
                                </Badge>
                                {edit.start_time.toFixed(1)}s - {edit.end_time.toFixed(1)}s
                              </span>
                              <Badge bg="outline-light">
                                {(edit.confidence * 100).toFixed(0)}% confidence
                              </Badge>
                            </div>
                            <small className="text-muted">{edit.reason}</small>
                            <div>
                              <Badge bg="secondary" className="mt-1">{edit.source}</Badge>
                            </div>
                          </div>
                        ))
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
