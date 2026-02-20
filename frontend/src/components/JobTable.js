import React from 'react';
import { Table, Badge, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';

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

function JobTable({ jobs, loading }) {
  if (loading) {
    return (
      <div className="text-center py-4">
        <Spinner animation="border" variant="light" />
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-4 text-muted">
        <p>No jobs yet. Upload a video to get started.</p>
      </div>
    );
  }

  return (
    <Table variant="dark" hover responsive className="mb-0">
      <thead>
        <tr>
          <th>File</th>
          <th>Status</th>
          <th>Pipeline</th>
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((job) => {
          const isProcessing = !['completed', 'failed', 'pending'].includes(job.status);
          return (
            <tr key={job.id}>
              <td>
                <Link to={`/jobs/${job.id}`} className="text-light text-decoration-none">
                  {job.filename}
                </Link>
              </td>
              <td>
                <Badge bg={STATUS_COLORS[job.status] || 'secondary'}>
                  {isProcessing && (
                    <Spinner animation="border" size="sm" className="me-1" />
                  )}
                  {job.status.replace(/_/g, ' ')}
                </Badge>
              </td>
              <td>
                <Badge bg="outline-light" className="text-capitalize">
                  {job.pipeline_type}
                </Badge>
              </td>
              <td className="text-muted">
                {new Date(job.created_at).toLocaleString()}
              </td>
              <td>
                <Link to={`/jobs/${job.id}`} className="btn btn-sm btn-outline-light">
                  View
                </Link>
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}

export default JobTable;
