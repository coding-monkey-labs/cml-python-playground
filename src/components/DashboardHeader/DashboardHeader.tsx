import { useAppSelector, useAppDispatch } from '../../store';
import {
  updateDashboardTitle,
  toggleSidebar,
  toggleSettings,
  addNotification,
} from '../../store/dashboardSlice';
import { ThemeToggle } from '../ThemeToggle/ThemeToggle';
import { TimeRangePicker } from '../TimeRangePicker/TimeRangePicker';
import { apiService } from '../../services/apiService';
import './DashboardHeader.css';

export function DashboardHeader() {
  const dispatch = useAppDispatch();
  const dashboard = useAppSelector(state => state.dashboard.dashboard);
  const isDirty = useAppSelector(state => state.dashboard.isDirty);

  const handleSave = async () => {
    try {
      await apiService.saveDashboard(dashboard);
      dispatch(addNotification({ type: 'success', message: 'Dashboard saved successfully' }));
    } catch {
      dispatch(addNotification({ type: 'error', message: 'Failed to save dashboard' }));
    }
  };

  return (
    <header className="dashboard-header">
      <div className="header-left">
        <button
          className="header-btn menu-btn"
          onClick={() => dispatch(toggleSidebar())}
          title="Toggle sidebar"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <div className="dashboard-title-area">
          <input
            className="dashboard-title-input"
            value={dashboard.title}
            onChange={e => dispatch(updateDashboardTitle(e.target.value))}
            placeholder="Dashboard title"
          />
          {isDirty && <span className="dirty-indicator" title="Unsaved changes" />}
        </div>
      </div>

      <div className="header-center">
        <div className="dashboard-tags">
          {dashboard.tags.map(tag => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>

      <div className="header-right">
        <TimeRangePicker />
        <button
          className="header-btn settings-btn"
          onClick={() => dispatch(toggleSettings())}
          title="Dashboard settings"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
        <button
          className="header-btn save-btn"
          onClick={handleSave}
          title="Save dashboard"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          Save
        </button>
        <ThemeToggle />
      </div>
    </header>
  );
}
