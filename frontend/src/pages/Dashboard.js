import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card } from 'react-bootstrap';
import VideoUploader from '../components/VideoUploader';
import JobTable from '../components/JobTable';
import { listJobs } from '../api/client';

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await listJobs(0, 50);
      setJobs(data.jobs);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const handleUploadComplete = () => {
    fetchJobs();
  };

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2 className="text-light mb-0">Dashboard</h2>
          <p className="text-muted">Upload videos and monitor processing jobs</p>
        </Col>
      </Row>

      {/* Stats Row */}
      <Row className="mb-4">
        <Col md={3}>
          <Card bg="dark" text="white" className="stat-card">
            <Card.Body>
              <Card.Title className="text-muted small">Total Jobs</Card.Title>
              <h3>{total}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="dark" text="white" className="stat-card">
            <Card.Body>
              <Card.Title className="text-muted small">Processing</Card.Title>
              <h3 className="text-warning">
                {jobs.filter(j => !['completed', 'failed', 'pending'].includes(j.status)).length}
              </h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="dark" text="white" className="stat-card">
            <Card.Body>
              <Card.Title className="text-muted small">Completed</Card.Title>
              <h3 className="text-success">
                {jobs.filter(j => j.status === 'completed').length}
              </h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="dark" text="white" className="stat-card">
            <Card.Body>
              <Card.Title className="text-muted small">Failed</Card.Title>
              <h3 className="text-danger">
                {jobs.filter(j => j.status === 'failed').length}
              </h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Upload Section */}
      <Row className="mb-4">
        <Col lg={8}>
          <Card bg="dark" text="white">
            <Card.Header>
              <h5 className="mb-0">Upload Video</h5>
            </Card.Header>
            <Card.Body>
              <VideoUploader onUploadComplete={handleUploadComplete} />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Jobs Table */}
      <Row>
        <Col>
          <Card bg="dark" text="white">
            <Card.Header>
              <h5 className="mb-0">Processing Jobs</h5>
            </Card.Header>
            <Card.Body className="p-0">
              <JobTable jobs={jobs} loading={loading} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;
