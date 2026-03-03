import { useAppSelector, useAppDispatch } from '../../store';
import {
  updateDashboardTitle,
  updateDashboardDescription,
  setSettingsOpen,
  addTag,
  removeTag,
  addNotification,
} from '../../store/dashboardSlice';
import { useState } from 'react';
import './DashboardSettings.css';

export function DashboardSettings() {
  const dispatch = useAppDispatch();
  const dashboard = useAppSelector(state => state.dashboard.dashboard);
  const [newTag, setNewTag] = useState('');

  const handleAddTag = () => {
    if (newTag.trim()) {
      dispatch(addTag(newTag.trim()));
      setNewTag('');
    }
  };

  const handleSave = () => {
    dispatch(addNotification({ type: 'success', message: 'Dashboard settings updated' }));
    dispatch(setSettingsOpen(false));
  };

  return (
    <div className="settings-overlay">
      <div className="settings-modal">
        <div className="settings-header">
          <h3>Dashboard Settings</h3>
          <button className="close-btn" onClick={() => dispatch(setSettingsOpen(false))}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="settings-body">
          <div className="settings-section">
            <h4>General</h4>
            <div className="field-group">
              <label>Title</label>
              <input
                type="text"
                value={dashboard.title}
                onChange={e => dispatch(updateDashboardTitle(e.target.value))}
              />
            </div>
            <div className="field-group">
              <label>Description</label>
              <textarea
                value={dashboard.description}
                onChange={e => dispatch(updateDashboardDescription(e.target.value))}
                rows={3}
              />
            </div>
          </div>

          <div className="settings-section">
            <h4>Tags</h4>
            <div className="tags-list">
              {dashboard.tags.map(tag => (
                <span key={tag} className="tag-item">
                  {tag}
                  <button onClick={() => dispatch(removeTag(tag))}>x</button>
                </span>
              ))}
            </div>
            <div className="tag-input-group">
              <input
                type="text"
                value={newTag}
                onChange={e => setNewTag(e.target.value)}
                placeholder="Add tag..."
                onKeyDown={e => e.key === 'Enter' && handleAddTag()}
              />
              <button onClick={handleAddTag}>Add</button>
            </div>
          </div>

          <div className="settings-section">
            <h4>Info</h4>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">UID</span>
                <span className="info-value">{dashboard.uid}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Version</span>
                <span className="info-value">{dashboard.version}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Panels</span>
                <span className="info-value">{dashboard.panels.length}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Variables</span>
                <span className="info-value">{dashboard.variables.length}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-footer">
          <button className="btn-secondary" onClick={() => dispatch(setSettingsOpen(false))}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>Save</button>
        </div>
      </div>
    </div>
  );
}
