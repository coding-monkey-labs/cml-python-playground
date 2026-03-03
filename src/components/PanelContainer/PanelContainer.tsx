import { useState, useEffect, useRef, useCallback } from 'react';
import { Panel, DataFrame } from '../../types';
import { useAppSelector, useAppDispatch } from '../../store';
import { setEditingPanel, removePanel, duplicatePanel, addNotification } from '../../store/dashboardSlice';
import { executeQueries } from '../../services/queryService';
import { applyTransforms } from '../../services/dataTransformService';
import { PanelRenderer } from '../PanelRenderer/PanelRenderer';
import './PanelContainer.css';

interface PanelContainerProps {
  panel: Panel;
}

export function PanelContainer({ panel }: PanelContainerProps) {
  const dispatch = useAppDispatch();
  const variables = useAppSelector(state => state.dashboard.dashboard.variables);
  const timeRange = useAppSelector(state => state.dashboard.dashboard.timeRange);
  const refresh = useAppSelector(state => state.dashboard.dashboard.refresh);

  const [data, setData] = useState<DataFrame[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 400, height: 300 });

  const fetchData = useCallback(async () => {
    if (panel.queries.length === 0 && panel.type !== 'text' && panel.type !== 'alertlist') {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const rawData = await executeQueries(panel.queries, variables, panel.type);
      const transformed = applyTransforms(rawData, panel.transforms);
      setData(transformed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query execution failed');
    } finally {
      setLoading(false);
    }
  }, [panel.queries, panel.transforms, panel.type, variables]);

  // Fetch data on mount and when dependencies change
  useEffect(() => {
    fetchData();
  }, [fetchData, timeRange]);

  // Auto-refresh
  useEffect(() => {
    if (!refresh || refresh === 'off') return;

    const parseInterval = (str: string): number => {
      const match = str.match(/^(\d+)([smh])$/);
      if (!match) return 0;
      const [, num, unit] = match;
      switch (unit) {
        case 's': return parseInt(num) * 1000;
        case 'm': return parseInt(num) * 60000;
        case 'h': return parseInt(num) * 3600000;
        default: return 0;
      }
    };

    const interval = parseInterval(refresh);
    if (interval <= 0) return;

    const timer = setInterval(fetchData, interval);
    return () => clearInterval(timer);
  }, [refresh, fetchData]);

  // Observe container size
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({ width: Math.max(width - 16, 100), height: Math.max(height - 48, 50) });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const handleMenuAction = (action: string) => {
    setMenuOpen(false);
    switch (action) {
      case 'edit':
        dispatch(setEditingPanel(panel.id));
        break;
      case 'duplicate':
        dispatch(duplicatePanel(panel.id));
        dispatch(addNotification({ type: 'success', message: `Panel "${panel.title}" duplicated` }));
        break;
      case 'remove':
        dispatch(removePanel(panel.id));
        dispatch(addNotification({ type: 'info', message: `Panel "${panel.title}" removed` }));
        break;
      case 'refresh':
        fetchData();
        break;
    }
  };

  return (
    <div className="panel-container" ref={containerRef}>
      <div className="panel-header">
        <h3 className="panel-title" title={panel.description}>
          {panel.title}
        </h3>
        <div className="panel-actions">
          <button className="panel-action-btn" onClick={fetchData} title="Refresh">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
          </button>
          <div className="panel-menu-wrapper">
            <button
              className="panel-action-btn"
              onClick={() => setMenuOpen(!menuOpen)}
              title="Panel menu"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="5" r="1" />
                <circle cx="12" cy="12" r="1" />
                <circle cx="12" cy="19" r="1" />
              </svg>
            </button>
            {menuOpen && (
              <div className="panel-menu">
                <button onClick={() => handleMenuAction('edit')}>Edit</button>
                <button onClick={() => handleMenuAction('duplicate')}>Duplicate</button>
                <button onClick={() => handleMenuAction('refresh')}>Refresh</button>
                <hr />
                <button className="danger" onClick={() => handleMenuAction('remove')}>Remove</button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="panel-content">
        {loading && (
          <div className="panel-loading">
            <div className="spinner" />
          </div>
        )}
        {error && (
          <div className="panel-error">
            <span>Error: {error}</span>
          </div>
        )}
        {!loading && !error && (
          <PanelRenderer
            panel={panel}
            data={data}
            width={dimensions.width}
            height={dimensions.height}
          />
        )}
      </div>
    </div>
  );
}
