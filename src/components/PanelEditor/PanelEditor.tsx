import { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { setEditingPanel, updatePanel } from '../../store/dashboardSlice';
import { Panel, PanelType } from '../../types';
import { QueryEditor } from '../QueryEditor/QueryEditor';
import './PanelEditor.css';

const PANEL_TYPES: { value: PanelType; label: string }[] = [
  { value: 'stat', label: 'Stat' },
  { value: 'gauge', label: 'Gauge' },
  { value: 'timeseries', label: 'Time Series' },
  { value: 'graph', label: 'Graph' },
  { value: 'table', label: 'Table' },
  { value: 'barchart', label: 'Bar Chart' },
  { value: 'piechart', label: 'Pie Chart' },
  { value: 'heatmap', label: 'Heatmap' },
  { value: 'logs', label: 'Logs' },
  { value: 'alertlist', label: 'Alert List' },
  { value: 'text', label: 'Text' },
];

export function PanelEditor() {
  const dispatch = useAppDispatch();
  const editingPanelId = useAppSelector(state => state.dashboard.editingPanelId);
  const panels = useAppSelector(state => state.dashboard.dashboard.panels);
  const panel = panels.find(p => p.id === editingPanelId);

  const [draft, setDraft] = useState<Panel | null>(null);
  const [activeTab, setActiveTab] = useState<'queries' | 'options' | 'thresholds'>('queries');

  useEffect(() => {
    if (panel) {
      setDraft({ ...panel });
    }
  }, [panel]);

  if (!draft) return null;

  const handleSave = () => {
    dispatch(updatePanel(draft));
    dispatch(setEditingPanel(null));
  };

  const handleCancel = () => {
    dispatch(setEditingPanel(null));
  };

  const updateDraft = (updates: Partial<Panel>) => {
    setDraft(prev => prev ? { ...prev, ...updates } : prev);
  };

  const updateOptions = (updates: Record<string, unknown>) => {
    setDraft(prev => prev ? { ...prev, options: { ...prev.options, ...updates } } : prev);
  };

  return (
    <div className="panel-editor-overlay">
      <div className="panel-editor">
        <div className="editor-header">
          <h3>Edit Panel</h3>
          <div className="editor-actions">
            <button className="btn-secondary" onClick={handleCancel}>Cancel</button>
            <button className="btn-primary" onClick={handleSave}>Apply</button>
          </div>
        </div>

        <div className="editor-body">
          {/* General settings */}
          <div className="editor-section">
            <div className="field-group">
              <label>Title</label>
              <input
                type="text"
                value={draft.title}
                onChange={e => updateDraft({ title: e.target.value })}
              />
            </div>
            <div className="field-group">
              <label>Description</label>
              <textarea
                value={draft.description}
                onChange={e => updateDraft({ description: e.target.value })}
                rows={2}
              />
            </div>
            <div className="field-group">
              <label>Panel Type</label>
              <select
                value={draft.type}
                onChange={e => updateDraft({ type: e.target.value as PanelType })}
              >
                {PANEL_TYPES.map(pt => (
                  <option key={pt.value} value={pt.value}>{pt.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Tabs */}
          <div className="editor-tabs">
            <button
              className={`tab ${activeTab === 'queries' ? 'active' : ''}`}
              onClick={() => setActiveTab('queries')}
            >
              Queries
            </button>
            <button
              className={`tab ${activeTab === 'options' ? 'active' : ''}`}
              onClick={() => setActiveTab('options')}
            >
              Options
            </button>
            <button
              className={`tab ${activeTab === 'thresholds' ? 'active' : ''}`}
              onClick={() => setActiveTab('thresholds')}
            >
              Thresholds
            </button>
          </div>

          {/* Tab content */}
          <div className="tab-content">
            {activeTab === 'queries' && (
              <QueryEditor
                queries={draft.queries}
                onChange={queries => updateDraft({ queries })}
              />
            )}

            {activeTab === 'options' && (
              <div className="options-section">
                {(draft.type === 'gauge') && (
                  <>
                    <div className="field-group">
                      <label>Min Value</label>
                      <input type="number" value={draft.options.minValue ?? 0} onChange={e => updateOptions({ minValue: Number(e.target.value) })} />
                    </div>
                    <div className="field-group">
                      <label>Max Value</label>
                      <input type="number" value={draft.options.maxValue ?? 100} onChange={e => updateOptions({ maxValue: Number(e.target.value) })} />
                    </div>
                    <div className="field-group checkbox">
                      <label><input type="checkbox" checked={draft.options.showThresholdLabels ?? false} onChange={e => updateOptions({ showThresholdLabels: e.target.checked })} /> Show threshold labels</label>
                    </div>
                    <div className="field-group checkbox">
                      <label><input type="checkbox" checked={draft.options.showThresholdMarkers ?? false} onChange={e => updateOptions({ showThresholdMarkers: e.target.checked })} /> Show threshold markers</label>
                    </div>
                  </>
                )}
                {(draft.type === 'timeseries' || draft.type === 'graph') && (
                  <>
                    <div className="field-group">
                      <label>Draw Style</label>
                      <select value={draft.options.drawStyle ?? 'line'} onChange={e => updateOptions({ drawStyle: e.target.value })}>
                        <option value="line">Line</option>
                        <option value="bars">Bars</option>
                        <option value="points">Points</option>
                      </select>
                    </div>
                    <div className="field-group">
                      <label>Line Width</label>
                      <input type="number" min={1} max={10} value={draft.options.lineWidth ?? 2} onChange={e => updateOptions({ lineWidth: Number(e.target.value) })} />
                    </div>
                    <div className="field-group">
                      <label>Fill Opacity (%)</label>
                      <input type="number" min={0} max={100} value={draft.options.fillOpacity ?? 20} onChange={e => updateOptions({ fillOpacity: Number(e.target.value) })} />
                    </div>
                  </>
                )}
                {draft.type === 'stat' && (
                  <>
                    <div className="field-group">
                      <label>Color Mode</label>
                      <select value={draft.options.colorMode ?? 'value'} onChange={e => updateOptions({ colorMode: e.target.value })}>
                        <option value="value">Value</option>
                        <option value="background">Background gradient</option>
                        <option value="background_solid">Background solid</option>
                        <option value="none">None</option>
                      </select>
                    </div>
                    <div className="field-group">
                      <label>Graph Mode</label>
                      <select value={draft.options.graphMode ?? 'area'} onChange={e => updateOptions({ graphMode: e.target.value })}>
                        <option value="area">Area</option>
                        <option value="line">Line</option>
                        <option value="none">None</option>
                      </select>
                    </div>
                  </>
                )}
                {draft.type === 'text' && (
                  <>
                    <div className="field-group">
                      <label>Mode</label>
                      <select value={draft.options.mode ?? 'markdown'} onChange={e => updateOptions({ mode: e.target.value })}>
                        <option value="markdown">Markdown</option>
                        <option value="html">HTML</option>
                        <option value="code">Code</option>
                      </select>
                    </div>
                    <div className="field-group">
                      <label>Content</label>
                      <textarea rows={8} value={draft.options.content ?? ''} onChange={e => updateOptions({ content: e.target.value })} />
                    </div>
                  </>
                )}
                {draft.type === 'barchart' && (
                  <>
                    <div className="field-group">
                      <label>Orientation</label>
                      <select value={draft.options.orientation ?? 'vertical'} onChange={e => updateOptions({ orientation: e.target.value })}>
                        <option value="vertical">Vertical</option>
                        <option value="horizontal">Horizontal</option>
                      </select>
                    </div>
                  </>
                )}
                {draft.type === 'piechart' && (
                  <>
                    <div className="field-group">
                      <label>Pie Type</label>
                      <select value={draft.options.pieType ?? 'pie'} onChange={e => updateOptions({ pieType: e.target.value })}>
                        <option value="pie">Pie</option>
                        <option value="donut">Donut</option>
                      </select>
                    </div>
                  </>
                )}
              </div>
            )}

            {activeTab === 'thresholds' && (
              <div className="thresholds-section">
                {draft.thresholds.map((threshold, i) => (
                  <div key={i} className="threshold-row">
                    <input
                      type="color"
                      value={threshold.color}
                      onChange={e => {
                        const updated = [...draft.thresholds];
                        updated[i] = { ...updated[i], color: e.target.value };
                        updateDraft({ thresholds: updated });
                      }}
                    />
                    <input
                      type="number"
                      value={threshold.value}
                      onChange={e => {
                        const updated = [...draft.thresholds];
                        updated[i] = { ...updated[i], value: Number(e.target.value) };
                        updateDraft({ thresholds: updated });
                      }}
                    />
                    <button
                      className="remove-threshold"
                      onClick={() => {
                        updateDraft({ thresholds: draft.thresholds.filter((_, idx) => idx !== i) });
                      }}
                    >
                      x
                    </button>
                  </div>
                ))}
                <button
                  className="add-threshold-btn"
                  onClick={() => {
                    updateDraft({
                      thresholds: [...draft.thresholds, { value: 0, color: '#73BF69' }],
                    });
                  }}
                >
                  + Add Threshold
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
