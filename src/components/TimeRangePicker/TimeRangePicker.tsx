import { useState } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { setTimeRange, setRefreshInterval } from '../../store/dashboardSlice';
import { DEFAULT_TIME_RANGES } from '../../types';
import './TimeRangePicker.css';

const REFRESH_OPTIONS = [
  { label: 'Off', value: 'off' },
  { label: '5s', value: '5s' },
  { label: '10s', value: '10s' },
  { label: '30s', value: '30s' },
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
];

export function TimeRangePicker() {
  const dispatch = useAppDispatch();
  const timeRange = useAppSelector(state => state.dashboard.dashboard.timeRange);
  const refresh = useAppSelector(state => state.dashboard.dashboard.refresh);
  const [open, setOpen] = useState(false);

  return (
    <div className="time-range-picker">
      <button
        className="time-range-btn"
        onClick={() => setOpen(!open)}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <span>{timeRange.display}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="time-range-dropdown">
          <div className="dropdown-section">
            <h4>Time Range</h4>
            {DEFAULT_TIME_RANGES.map(range => (
              <button
                key={range.from}
                className={`dropdown-item ${timeRange.from === range.from ? 'active' : ''}`}
                onClick={() => {
                  dispatch(setTimeRange(range));
                  setOpen(false);
                }}
              >
                {range.display}
              </button>
            ))}
          </div>
          <div className="dropdown-section">
            <h4>Auto Refresh</h4>
            <div className="refresh-options">
              {REFRESH_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  className={`refresh-btn ${refresh === opt.value ? 'active' : ''}`}
                  onClick={() => dispatch(setRefreshInterval(opt.value))}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
