import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  DashboardState,
  Dashboard,
  Panel,
  Variable,
  TimeRange,
  AppNotification,
  GridPos,
} from '../types';

const defaultDashboard: Dashboard = {
  id: 'default',
  uid: 'fluxboard-default',
  title: 'FluxBoard Dashboard',
  description: 'Default dashboard with sample panels',
  tags: ['default', 'demo'],
  variables: [
    {
      id: 'var-env',
      name: 'environment',
      type: 'custom',
      label: 'Environment',
      current: 'production',
      options: ['production', 'staging', 'development'],
      multi: false,
      includeAll: true,
    },
    {
      id: 'var-region',
      name: 'region',
      type: 'custom',
      label: 'Region',
      current: 'us-east-1',
      options: ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
      multi: false,
      includeAll: true,
    },
    {
      id: 'var-interval',
      name: 'interval',
      type: 'interval',
      label: 'Interval',
      current: '1m',
      options: ['10s', '30s', '1m', '5m', '15m', '1h'],
      multi: false,
      includeAll: false,
    },
  ],
  panels: [
    {
      id: 'panel-1',
      type: 'stat',
      title: 'Total Requests',
      description: 'Total HTTP requests per second',
      gridPos: { x: 0, y: 0, w: 3, h: 2 },
      queries: [{ id: 'q1', datasourceId: 'demo', expr: 'http_requests_total{env="$environment"}', refId: 'A' }],
      transforms: [],
      thresholds: [
        { value: 0, color: '#73BF69' },
        { value: 1000, color: '#FF9830' },
        { value: 5000, color: '#F2495C' },
      ],
      fieldOverrides: [],
      options: { colorMode: 'background', graphMode: 'area', textMode: 'value_and_name' },
    },
    {
      id: 'panel-2',
      type: 'stat',
      title: 'Error Rate',
      description: 'Current error rate percentage',
      gridPos: { x: 3, y: 0, w: 3, h: 2 },
      queries: [{ id: 'q2', datasourceId: 'demo', expr: 'error_rate{env="$environment"}', refId: 'A' }],
      transforms: [],
      thresholds: [
        { value: 0, color: '#73BF69' },
        { value: 2, color: '#FF9830' },
        { value: 5, color: '#F2495C' },
      ],
      fieldOverrides: [],
      options: { colorMode: 'background', graphMode: 'area', textMode: 'value_and_name' },
    },
    {
      id: 'panel-3',
      type: 'gauge',
      title: 'CPU Usage',
      description: 'Current CPU utilization',
      gridPos: { x: 6, y: 0, w: 3, h: 2 },
      queries: [{ id: 'q3', datasourceId: 'demo', expr: 'cpu_usage{env="$environment", region="$region"}', refId: 'A' }],
      transforms: [],
      thresholds: [
        { value: 0, color: '#73BF69' },
        { value: 60, color: '#FF9830' },
        { value: 85, color: '#F2495C' },
      ],
      fieldOverrides: [],
      options: { minValue: 0, maxValue: 100, showThresholdLabels: true, showThresholdMarkers: true },
    },
    {
      id: 'panel-4',
      type: 'gauge',
      title: 'Memory Usage',
      description: 'Current memory utilization',
      gridPos: { x: 9, y: 0, w: 3, h: 2 },
      queries: [{ id: 'q4', datasourceId: 'demo', expr: 'memory_usage{env="$environment", region="$region"}', refId: 'A' }],
      transforms: [],
      thresholds: [
        { value: 0, color: '#73BF69' },
        { value: 70, color: '#FF9830' },
        { value: 90, color: '#F2495C' },
      ],
      fieldOverrides: [],
      options: { minValue: 0, maxValue: 100, showThresholdLabels: true, showThresholdMarkers: true },
    },
    {
      id: 'panel-5',
      type: 'timeseries',
      title: 'Request Rate Over Time',
      description: 'HTTP requests per second over time',
      gridPos: { x: 0, y: 2, w: 8, h: 3 },
      queries: [
        { id: 'q5a', datasourceId: 'demo', expr: 'rate(http_requests_total{env="$environment"}[$interval])', legendFormat: 'Requests/s', refId: 'A', range: true },
        { id: 'q5b', datasourceId: 'demo', expr: 'rate(http_errors_total{env="$environment"}[$interval])', legendFormat: 'Errors/s', refId: 'B', range: true },
      ],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { lineWidth: 2, fillOpacity: 20, pointSize: 5, showPoints: 'auto', drawStyle: 'line', gradientMode: 'opacity' },
    },
    {
      id: 'panel-6',
      type: 'barchart',
      title: 'Requests by Endpoint',
      description: 'Top endpoints by request count',
      gridPos: { x: 8, y: 2, w: 4, h: 3 },
      queries: [{ id: 'q6', datasourceId: 'demo', expr: 'topk(5, http_requests_by_endpoint{env="$environment"})', refId: 'A' }],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { orientation: 'horizontal', barWidth: 0.8, stacking: 'none' },
    },
    {
      id: 'panel-7',
      type: 'table',
      title: 'Recent Deployments',
      description: 'Deployment history with status',
      gridPos: { x: 0, y: 5, w: 6, h: 3 },
      queries: [{ id: 'q7', datasourceId: 'demo', expr: 'deployments{env="$environment"}', refId: 'A' }],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { showHeader: true },
    },
    {
      id: 'panel-8',
      type: 'piechart',
      title: 'Traffic Distribution',
      description: 'Traffic by region',
      gridPos: { x: 6, y: 5, w: 3, h: 3 },
      queries: [{ id: 'q8', datasourceId: 'demo', expr: 'traffic_by_region', refId: 'A' }],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { pieType: 'donut' },
    },
    {
      id: 'panel-9',
      type: 'logs',
      title: 'Application Logs',
      description: 'Recent application log entries',
      gridPos: { x: 9, y: 5, w: 3, h: 3 },
      queries: [{ id: 'q9', datasourceId: 'demo', expr: 'app_logs{env="$environment"}', refId: 'A' }],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { showTime: true, showLabels: true, wrapLogMessage: true, sortOrder: 'desc' },
    },
    {
      id: 'panel-10',
      type: 'heatmap',
      title: 'Response Time Heatmap',
      description: 'Request latency distribution over time',
      gridPos: { x: 0, y: 8, w: 6, h: 3 },
      queries: [{ id: 'q10', datasourceId: 'demo', expr: 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{env="$environment"}[$interval]))', refId: 'A' }],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { yAxisReversed: false, cellGap: 1 },
    },
    {
      id: 'panel-11',
      type: 'alertlist',
      title: 'Active Alerts',
      description: 'Current alert status',
      gridPos: { x: 6, y: 8, w: 3, h: 3 },
      queries: [],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: { alertStates: ['alerting', 'pending'], maxItems: 10 },
    },
    {
      id: 'panel-12',
      type: 'text',
      title: 'System Status',
      description: '',
      gridPos: { x: 9, y: 8, w: 3, h: 3 },
      queries: [],
      transforms: [],
      thresholds: [],
      fieldOverrides: [],
      options: {
        mode: 'markdown',
        content: '## System Health\n\nAll systems are **operational**.\n\n### Quick Links\n- [Runbook](https://wiki.example.com/runbook)\n- [Incidents](https://incidents.example.com)\n- [Metrics](https://metrics.example.com)\n\n> Last updated: auto-refresh enabled',
      },
    },
  ],
  timeRange: { from: 'now-1h', to: 'now', display: 'Last 1 hour' },
  refresh: '10s',
  version: 1,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

const initialState: DashboardState = {
  dashboard: defaultDashboard,
  editingPanelId: null,
  isDirty: false,
  isLoading: false,
  notifications: [],
  sidebarOpen: false,
  settingsOpen: false,
};

let notificationCounter = 0;

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setDashboard(state, action: PayloadAction<Dashboard>) {
      state.dashboard = action.payload;
      state.isDirty = false;
    },
    updateDashboardTitle(state, action: PayloadAction<string>) {
      state.dashboard.title = action.payload;
      state.isDirty = true;
    },
    updateDashboardDescription(state, action: PayloadAction<string>) {
      state.dashboard.description = action.payload;
      state.isDirty = true;
    },
    setTimeRange(state, action: PayloadAction<TimeRange>) {
      state.dashboard.timeRange = action.payload;
    },
    setRefreshInterval(state, action: PayloadAction<string>) {
      state.dashboard.refresh = action.payload;
    },
    // Panel operations
    addPanel(state, action: PayloadAction<Panel>) {
      state.dashboard.panels.push(action.payload);
      state.isDirty = true;
    },
    updatePanel(state, action: PayloadAction<Panel>) {
      const index = state.dashboard.panels.findIndex(p => p.id === action.payload.id);
      if (index !== -1) {
        state.dashboard.panels[index] = action.payload;
        state.isDirty = true;
      }
    },
    removePanel(state, action: PayloadAction<string>) {
      state.dashboard.panels = state.dashboard.panels.filter(p => p.id !== action.payload);
      state.isDirty = true;
    },
    updatePanelGridPos(state, action: PayloadAction<{ id: string; gridPos: GridPos }>) {
      const panel = state.dashboard.panels.find(p => p.id === action.payload.id);
      if (panel) {
        panel.gridPos = action.payload.gridPos;
        state.isDirty = true;
      }
    },
    duplicatePanel(state, action: PayloadAction<string>) {
      const panel = state.dashboard.panels.find(p => p.id === action.payload);
      if (panel) {
        const newPanel: Panel = {
          ...JSON.parse(JSON.stringify(panel)),
          id: `panel-${Date.now()}`,
          title: `${panel.title} (Copy)`,
          gridPos: { ...panel.gridPos, y: panel.gridPos.y + panel.gridPos.h },
        };
        state.dashboard.panels.push(newPanel);
        state.isDirty = true;
      }
    },
    // Panel editing
    setEditingPanel(state, action: PayloadAction<string | null>) {
      state.editingPanelId = action.payload;
    },
    // Variable operations
    updateVariable(state, action: PayloadAction<Variable>) {
      const index = state.dashboard.variables.findIndex(v => v.id === action.payload.id);
      if (index !== -1) {
        state.dashboard.variables[index] = action.payload;
      }
    },
    setVariableValue(state, action: PayloadAction<{ id: string; value: string }>) {
      const variable = state.dashboard.variables.find(v => v.id === action.payload.id);
      if (variable) {
        variable.current = action.payload.value;
      }
    },
    addVariable(state, action: PayloadAction<Variable>) {
      state.dashboard.variables.push(action.payload);
      state.isDirty = true;
    },
    removeVariable(state, action: PayloadAction<string>) {
      state.dashboard.variables = state.dashboard.variables.filter(v => v.id !== action.payload);
      state.isDirty = true;
    },
    // UI state
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen(state, action: PayloadAction<boolean>) {
      state.sidebarOpen = action.payload;
    },
    toggleSettings(state) {
      state.settingsOpen = !state.settingsOpen;
    },
    setSettingsOpen(state, action: PayloadAction<boolean>) {
      state.settingsOpen = action.payload;
    },
    // Notifications
    addNotification(state, action: PayloadAction<Omit<AppNotification, 'id' | 'timestamp'>>) {
      state.notifications.push({
        ...action.payload,
        id: `notif-${++notificationCounter}`,
        timestamp: Date.now(),
      });
    },
    removeNotification(state, action: PayloadAction<string>) {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications(state) {
      state.notifications = [];
    },
    // Tags
    addTag(state, action: PayloadAction<string>) {
      if (!state.dashboard.tags.includes(action.payload)) {
        state.dashboard.tags.push(action.payload);
        state.isDirty = true;
      }
    },
    removeTag(state, action: PayloadAction<string>) {
      state.dashboard.tags = state.dashboard.tags.filter(t => t !== action.payload);
      state.isDirty = true;
    },
  },
});

export const {
  setDashboard,
  updateDashboardTitle,
  updateDashboardDescription,
  setTimeRange,
  setRefreshInterval,
  addPanel,
  updatePanel,
  removePanel,
  updatePanelGridPos,
  duplicatePanel,
  setEditingPanel,
  updateVariable,
  setVariableValue,
  addVariable,
  removeVariable,
  setLoading,
  toggleSidebar,
  setSidebarOpen,
  toggleSettings,
  setSettingsOpen,
  addNotification,
  removeNotification,
  clearNotifications,
  addTag,
  removeTag,
} = dashboardSlice.actions;

export default dashboardSlice.reducer;
