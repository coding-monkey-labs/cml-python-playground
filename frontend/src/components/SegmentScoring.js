import React from 'react';
import { Table, Badge, ProgressBar } from 'react-bootstrap';

function ScoreBar({ value, variant }) {
  if (value === null || value === undefined) return <span className="text-muted">--</span>;
  const pct = Math.round(value * 100);
  return (
    <div className="d-flex align-items-center">
      <ProgressBar
        now={pct}
        variant={variant}
        style={{ width: '80px', height: '8px' }}
        className="me-2"
      />
      <small>{pct}%</small>
    </div>
  );
}

function SegmentScoring({ segments }) {
  if (!segments || segments.length === 0) {
    return <p className="text-muted">No scored segments available.</p>;
  }

  return (
    <div className="table-responsive">
      <Table variant="dark" size="sm" hover>
        <thead>
          <tr>
            <th>Time</th>
            <th>Text (preview)</th>
            <th>Clarity</th>
            <th>Engagement</th>
            <th>Filler</th>
            <th>Retention Risk</th>
            <th>Flags</th>
          </tr>
        </thead>
        <tbody>
          {segments.map((seg, idx) => (
            <tr key={idx} className={seg.is_filler ? 'table-warning' : ''}>
              <td className="text-nowrap">
                <small>{seg.start_time.toFixed(1)}s</small>
              </td>
              <td>
                <small className="text-truncate d-block" style={{ maxWidth: '300px' }}>
                  {seg.text}
                </small>
              </td>
              <td><ScoreBar value={seg.clarity_score} variant="info" /></td>
              <td><ScoreBar value={seg.engagement_score} variant="success" /></td>
              <td><ScoreBar value={seg.filler_score} variant="warning" /></td>
              <td><ScoreBar value={seg.retention_risk_score} variant="danger" /></td>
              <td>
                {seg.is_filler && <Badge bg="warning" className="me-1">Filler</Badge>}
                {seg.retention_risk_score > 0.7 && <Badge bg="danger">High Risk</Badge>}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}

export default SegmentScoring;
