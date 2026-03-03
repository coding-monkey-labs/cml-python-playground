import { Dashboard, DataSource, Alert } from '../types';

// Simulated API service - would connect to real backends in production

const DEMO_DATASOURCES: DataSource[] = [
  { id: 'demo', name: 'Demo Data', type: 'demo', isDefault: true },
  { id: 'prometheus', name: 'Prometheus', type: 'prometheus', url: 'http://localhost:9090', isDefault: false },
  { id: 'influxdb', name: 'InfluxDB', type: 'influxdb', url: 'http://localhost:8086', isDefault: false },
];

const DEMO_ALERTS: Alert[] = [
  {
    id: 'alert-1',
    name: 'High CPU Usage',
    state: 'alerting',
    severity: 'critical',
    message: 'CPU usage above 90% for 5 minutes on worker-2',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    labels: { instance: 'worker-2', env: 'production' },
  },
  {
    id: 'alert-2',
    name: 'High Error Rate',
    state: 'pending',
    severity: 'warning',
    message: 'Error rate approaching 5% threshold on api-gateway',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    labels: { service: 'api-gateway', env: 'production' },
  },
  {
    id: 'alert-3',
    name: 'Disk Space Low',
    state: 'alerting',
    severity: 'warning',
    message: 'Disk usage at 87% on database-primary',
    timestamp: new Date(Date.now() - 1200000).toISOString(),
    labels: { instance: 'database-primary', env: 'production' },
  },
  {
    id: 'alert-4',
    name: 'Memory Pressure',
    state: 'ok',
    severity: 'info',
    message: 'Memory usage returned to normal on cache-cluster',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    labels: { instance: 'cache-cluster', env: 'production' },
  },
  {
    id: 'alert-5',
    name: 'SSL Certificate Expiry',
    state: 'pending',
    severity: 'warning',
    message: 'SSL certificate expires in 14 days for api.example.com',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    labels: { domain: 'api.example.com' },
  },
];

export const apiService = {
  async getDatasources(): Promise<DataSource[]> {
    await new Promise(r => setTimeout(r, 100));
    return DEMO_DATASOURCES;
  },

  async getAlerts(): Promise<Alert[]> {
    await new Promise(r => setTimeout(r, 150));
    return DEMO_ALERTS;
  },

  async saveDashboard(dashboard: Dashboard): Promise<{ success: boolean; version: number }> {
    await new Promise(r => setTimeout(r, 200));
    console.log('[API] Dashboard saved:', dashboard.title);
    return { success: true, version: dashboard.version + 1 };
  },

  async loadDashboard(uid: string): Promise<Dashboard | null> {
    await new Promise(r => setTimeout(r, 200));
    console.log('[API] Loading dashboard:', uid);
    return null; // Would load from backend
  },

  async deleteDashboard(uid: string): Promise<boolean> {
    await new Promise(r => setTimeout(r, 150));
    console.log('[API] Dashboard deleted:', uid);
    return true;
  },

  async testDatasource(datasource: DataSource): Promise<{ success: boolean; message: string }> {
    await new Promise(r => setTimeout(r, 500));
    if (datasource.type === 'demo') {
      return { success: true, message: 'Demo datasource is always available' };
    }
    return { success: true, message: `Successfully connected to ${datasource.name}` };
  },
};
