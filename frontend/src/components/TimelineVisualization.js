import React, { useMemo } from 'react';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

function TimelineVisualization({ transcript, editPlan, duration }) {
  const totalDuration = useMemo(() => {
    if (duration && duration > 0) return duration;
    if (transcript.length > 0) {
      return Math.max(...transcript.map(c => c.end_time));
    }
    return 100;
  }, [duration, transcript]);

  const removeRegions = useMemo(() => {
    return (editPlan || []).filter(e => e.action === 'remove');
  }, [editPlan]);

  const compressRegions = useMemo(() => {
    return (editPlan || []).filter(e => e.action === 'compress');
  }, [editPlan]);

  const toPercent = (time) => (time / totalDuration) * 100;

  return (
    <div className="timeline-container">
      <div className="d-flex justify-content-between mb-2">
        <small className="text-muted">0:00</small>
        <small className="text-muted">
          {Math.floor(totalDuration / 60)}:{String(Math.floor(totalDuration % 60)).padStart(2, '0')}
        </small>
      </div>

      {/* Main timeline bar */}
      <div className="timeline-bar">
        {/* Transcript chunks */}
        {transcript.map((chunk, idx) => {
          const left = toPercent(chunk.start_time);
          const width = toPercent(chunk.end_time - chunk.start_time);
          const isFiller = chunk.is_filler;

          return (
            <OverlayTrigger
              key={`chunk-${idx}`}
              placement="top"
              overlay={
                <Tooltip>
                  [{chunk.start_time.toFixed(1)}s - {chunk.end_time.toFixed(1)}s]
                  <br />
                  {chunk.text.substring(0, 80)}
                  {chunk.text.length > 80 ? '...' : ''}
                </Tooltip>
              }
            >
              <div
                className={`timeline-segment ${isFiller ? 'filler' : 'normal'}`}
                style={{
                  left: `${left}%`,
                  width: `${Math.max(width, 0.3)}%`,
                }}
              />
            </OverlayTrigger>
          );
        })}

        {/* Remove markers */}
        {removeRegions.map((edit, idx) => {
          const left = toPercent(edit.start_time);
          const width = toPercent(edit.end_time - edit.start_time);
          return (
            <OverlayTrigger
              key={`remove-${idx}`}
              placement="top"
              overlay={
                <Tooltip>
                  REMOVE: {edit.start_time.toFixed(1)}s - {edit.end_time.toFixed(1)}s
                  <br />
                  {edit.reason}
                </Tooltip>
              }
            >
              <div
                className="timeline-edit remove"
                style={{
                  left: `${left}%`,
                  width: `${Math.max(width, 0.3)}%`,
                }}
              />
            </OverlayTrigger>
          );
        })}

        {/* Compress markers */}
        {compressRegions.map((edit, idx) => {
          const left = toPercent(edit.start_time);
          const width = toPercent(edit.end_time - edit.start_time);
          return (
            <OverlayTrigger
              key={`compress-${idx}`}
              placement="top"
              overlay={
                <Tooltip>
                  COMPRESS: {edit.start_time.toFixed(1)}s - {edit.end_time.toFixed(1)}s
                  <br />
                  {edit.reason}
                </Tooltip>
              }
            >
              <div
                className="timeline-edit compress"
                style={{
                  left: `${left}%`,
                  width: `${Math.max(width, 0.3)}%`,
                }}
              />
            </OverlayTrigger>
          );
        })}
      </div>

      {/* Legend */}
      <div className="d-flex gap-4 mt-3">
        <div className="d-flex align-items-center">
          <div className="legend-dot bg-success me-2" />
          <small className="text-muted">Speech</small>
        </div>
        <div className="d-flex align-items-center">
          <div className="legend-dot bg-warning me-2" />
          <small className="text-muted">Filler</small>
        </div>
        <div className="d-flex align-items-center">
          <div className="legend-dot bg-danger me-2" />
          <small className="text-muted">Removed</small>
        </div>
        <div className="d-flex align-items-center">
          <div className="legend-dot bg-info me-2" />
          <small className="text-muted">Compressed</small>
        </div>
      </div>

      {/* Stats */}
      {editPlan && editPlan.length > 0 && (
        <div className="mt-3 p-2 bg-black rounded">
          <small className="text-muted">
            <strong>{removeRegions.length}</strong> segments removed |{' '}
            <strong>{compressRegions.length}</strong> pauses compressed |{' '}
            <strong>
              {removeRegions.reduce((sum, e) => sum + (e.end_time - e.start_time), 0).toFixed(1)}s
            </strong>{' '}
            total removed
          </small>
        </div>
      )}
    </div>
  );
}

export default TimelineVisualization;
