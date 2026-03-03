import { useAppSelector, useAppDispatch } from '../../store';
import { setSidebarOpen } from '../../store/dashboardSlice';
import './Sidebar.css';

export function Sidebar() {
  const dispatch = useAppDispatch();
  const isOpen = useAppSelector(state => state.dashboard.sidebarOpen);
  const dashboard = useAppSelector(state => state.dashboard.dashboard);

  if (!isOpen) return null;

  return (
    <>
      <div className="sidebar-overlay" onClick={() => dispatch(setSidebarOpen(false))} />
      <nav className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <svg width="28" height="28" viewBox="0 0 100 100">
              <defs>
                <linearGradient id="sidebarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style={{ stopColor: '#667eea', stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: '#764ba2', stopOpacity: 1 }} />
                </linearGradient>
              </defs>
              <rect width="100" height="100" rx="15" fill="url(#sidebarGrad)" />
              <text x="50" y="65" fontFamily="Arial" fontSize="45" fontWeight="bold" fill="white" textAnchor="middle">FB</text>
            </svg>
            <span className="sidebar-brand">FluxBoard</span>
          </div>
          <button className="sidebar-close" onClick={() => dispatch(setSidebarOpen(false))}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="sidebar-content">
          <div className="sidebar-section">
            <h4>Navigation</h4>
            <ul className="sidebar-nav">
              <li className="nav-item active">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
                <span>Dashboards</span>
              </li>
              <li className="nav-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                </svg>
                <span>Explore</span>
              </li>
              <li className="nav-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <span>Alerting</span>
              </li>
            </ul>
          </div>

          <div className="sidebar-section">
            <h4>Current Dashboard</h4>
            <div className="dashboard-info">
              <p className="info-title">{dashboard.title}</p>
              <p className="info-desc">{dashboard.description}</p>
              <div className="info-stats">
                <span>{dashboard.panels.length} panels</span>
                <span>{dashboard.variables.length} variables</span>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <h4>Panels</h4>
            <ul className="panel-list">
              {dashboard.panels.map(panel => (
                <li key={panel.id} className="panel-list-item">
                  <span className="panel-type-badge">{panel.type}</span>
                  <span>{panel.title}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="sidebar-footer">
          <span>FluxBoard v1.0.0</span>
        </div>
      </nav>
    </>
  );
}
