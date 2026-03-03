import { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../store';
import { addPanel, addNotification } from '../../store/dashboardSlice';
import { PanelType, Panel } from '../../types';
import { generateId } from '../../utils/formatting';
import './AddPanelWidget.css';

const PANEL_TEMPLATES: { type: PanelType; label: string; icon: string }[] = [
  { type: 'stat', label: 'Stat', icon: '#' },
  { type: 'gauge', label: 'Gauge', icon: 'O' },
  { type: 'timeseries', label: 'Time Series', icon: '~' },
  { type: 'table', label: 'Table', icon: '=' },
  { type: 'barchart', label: 'Bar Chart', icon: '|' },
  { type: 'piechart', label: 'Pie Chart', icon: 'o' },
  { type: 'heatmap', label: 'Heatmap', icon: ':' },
  { type: 'logs', label: 'Logs', icon: '>' },
  { type: 'alertlist', label: 'Alert List', icon: '!' },
  { type: 'text', label: 'Text', icon: 'T' },
];

export function AddPanelWidget() {
  const dispatch = useAppDispatch();
  const panels = useAppSelector(state => state.dashboard.dashboard.panels);
  const [expanded, setExpanded] = useState(false);

  const getNextPosition = () => {
    const maxY = panels.reduce((max, p) => Math.max(max, p.gridPos.y + p.gridPos.h), 0);
    return { x: 0, y: maxY, w: 6, h: 3 };
  };

  const handleAdd = (type: PanelType) => {
    const gridPos = getNextPosition();
    const newPanel: Panel = {
      id: generateId('panel'),
      type,
      title: `New ${type.charAt(0).toUpperCase() + type.slice(1)} Panel`,
      description: '',
      gridPos,
      queries: type !== 'text' && type !== 'alertlist'
        ? [{ id: generateId('query'), datasourceId: 'demo', expr: '', legendFormat: '', refId: 'A' }]
        : [],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: {},
    };

    dispatch(addPanel(newPanel));
    dispatch(addNotification({ type: 'success', message: `Added new ${type} panel` }));
    setExpanded(false);
  };

  return (
    <div className="add-panel-widget">
      {!expanded ? (
        <button className="add-panel-btn" onClick={() => setExpanded(true)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Panel
        </button>
      ) : (
        <div className="add-panel-expanded">
          <div className="add-panel-header">
            <h4>Add Panel</h4>
            <button className="close-btn" onClick={() => setExpanded(false)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="panel-type-grid">
            {PANEL_TEMPLATES.map(template => (
              <button
                key={template.type}
                className="panel-type-card"
                onClick={() => handleAdd(template.type)}
              >
                <span className="panel-type-icon">{template.icon}</span>
                <span className="panel-type-label">{template.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
