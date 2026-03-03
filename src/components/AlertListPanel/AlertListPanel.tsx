import { useState, useEffect } from 'react';
import { Panel, Alert } from '../../types';
import { apiService } from '../../services/apiService';
import { formatRelativeTime } from '../../utils/formatting';
import './AlertListPanel.css';

interface AlertListPanelProps {
  panel: Panel;
  data: unknown[];
  width: number;
  height: number;
}

export function AlertListPanel({ panel }: AlertListPanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const allAlerts = await apiService.getAlerts();
        const filtered = panel.options.alertStates?.length
          ? allAlerts.filter(a => panel.options.alertStates!.includes(a.state))
          : allAlerts;
        const limited = panel.options.maxItems
          ? filtered.slice(0, panel.options.maxItems)
          : filtered;
        setAlerts(limited);
      } finally {
        setLoading(false);
      }
    };
    fetchAlerts();
  }, [panel.options.alertStates, panel.options.maxItems]);

  if (loading) return <div className="alertlist-loading">Loading alerts...</div>;
  if (alerts.length === 0) return <div className="alertlist-empty">No active alerts</div>;

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'alerting': return '!';
      case 'pending': return '?';
      case 'ok': return '\u2713';
      case 'nodata': return '-';
      case 'paused': return '||';
      default: return '?';
    }
  };

  return (
    <div className="alertlist-panel">
      {alerts.map(alert => (
        <div key={alert.id} className={`alert-item alert-${alert.state}`}>
          <div className={`alert-state-icon state-${alert.state}`}>
            {getStateIcon(alert.state)}
          </div>
          <div className="alert-content">
            <div className="alert-header">
              <span className="alert-name">{alert.name}</span>
              <span className={`alert-severity severity-${alert.severity}`}>
                {alert.severity}
              </span>
            </div>
            <div className="alert-message">{alert.message}</div>
            <div className="alert-meta">
              <span className="alert-time">{formatRelativeTime(alert.timestamp)}</span>
              {Object.entries(alert.labels).map(([k, v]) => (
                <span key={k} className="alert-label">{k}={v}</span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
