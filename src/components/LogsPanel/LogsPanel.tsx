import { Panel, DataFrame } from '../../types';
import { formatRelativeTime } from '../../utils/formatting';
import './LogsPanel.css';

interface LogsPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

export function LogsPanel({ panel, data }: LogsPanelProps) {
  if (data.length === 0) return <div className="logs-empty">No log data</div>;

  const frame = data[0];
  const timeField = frame.fields.find(f => f.name === 'timestamp');
  const levelField = frame.fields.find(f => f.name === 'level');
  const messageField = frame.fields.find(f => f.name === 'message');
  const serviceField = frame.fields.find(f => f.name === 'service');

  const showTime = panel.options.showTime !== false;
  const showLabels = panel.options.showLabels !== false;

  const rows = Array.from({ length: frame.length }, (_, i) => ({
    time: timeField?.values[i] as string,
    level: levelField?.values[i] as string || 'INFO',
    message: messageField?.values[i] as string || '',
    service: serviceField?.values[i] as string || '',
  }));

  const sortedRows = panel.options.sortOrder === 'asc'
    ? [...rows].reverse()
    : rows;

  return (
    <div className="logs-panel">
      <div className="logs-scroll">
        {sortedRows.map((row, i) => (
          <div key={i} className={`log-entry log-${row.level.toLowerCase()}`}>
            {showTime && (
              <span className="log-time">{formatRelativeTime(row.time)}</span>
            )}
            <span className={`log-level level-${row.level.toLowerCase()}`}>
              {row.level}
            </span>
            {showLabels && row.service && (
              <span className="log-label">{row.service}</span>
            )}
            <span className="log-message">{row.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
