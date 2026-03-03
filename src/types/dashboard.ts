// ============================================================
// FluxBoard Type Definitions
// ============================================================

// Panel Types
export type PanelType =
  | 'gauge'
  | 'graph'
  | 'table'
  | 'stat'
  | 'text'
  | 'timeseries'
  | 'barchart'
  | 'piechart'
  | 'heatmap'
  | 'logs'
  | 'alertlist';

// Theme
export type ThemeMode = 'dark' | 'light';

// Time Range
export interface TimeRange {
  from: string;
  to: string;
  display: string;
}

export const DEFAULT_TIME_RANGES: TimeRange[] = [
  { from: 'now-5m', to: 'now', display: 'Last 5 minutes' },
  { from: 'now-15m', to: 'now', display: 'Last 15 minutes' },
  { from: 'now-30m', to: 'now', display: 'Last 30 minutes' },
  { from: 'now-1h', to: 'now', display: 'Last 1 hour' },
  { from: 'now-3h', to: 'now', display: 'Last 3 hours' },
  { from: 'now-6h', to: 'now', display: 'Last 6 hours' },
  { from: 'now-12h', to: 'now', display: 'Last 12 hours' },
  { from: 'now-24h', to: 'now', display: 'Last 24 hours' },
  { from: 'now-7d', to: 'now', display: 'Last 7 days' },
  { from: 'now-30d', to: 'now', display: 'Last 30 days' },
];

// Variable Types
export type VariableType = 'query' | 'custom' | 'constant' | 'interval' | 'textbox';

export interface Variable {
  id: string;
  name: string;
  type: VariableType;
  label: string;
  current: string;
  options: string[];
  query?: string;
  multi: boolean;
  includeAll: boolean;
}

// Data Source
export interface DataSource {
  id: string;
  name: string;
  type: 'prometheus' | 'influxdb' | 'elasticsearch' | 'mysql' | 'postgres' | 'json' | 'csv' | 'demo';
  url?: string;
  isDefault: boolean;
}

// Query
export interface Query {
  id: string;
  datasourceId: string;
  expr: string;
  legendFormat?: string;
  refId: string;
  instant?: boolean;
  range?: boolean;
}

// Transform
export type TransformType = 'filter' | 'groupBy' | 'sortBy' | 'calculateField' | 'organize' | 'reduce';

export interface Transform {
  id: string;
  type: TransformType;
  options: Record<string, unknown>;
}

// Threshold
export interface Threshold {
  value: number;
  color: string;
  label?: string;
}

// Field Override
export interface FieldOverride {
  matcher: {
    id: string;
    options: string;
  };
  properties: Array<{
    id: string;
    value: unknown;
  }>;
}

// Panel Options (generic, extended per panel type)
export interface PanelOptions {
  title?: string;
  description?: string;
  transparent?: boolean;
  // Gauge-specific
  minValue?: number;
  maxValue?: number;
  showThresholdLabels?: boolean;
  showThresholdMarkers?: boolean;
  // Graph/TimeSeries-specific
  lineWidth?: number;
  fillOpacity?: number;
  pointSize?: number;
  showPoints?: 'auto' | 'always' | 'never';
  drawStyle?: 'line' | 'bars' | 'points';
  gradientMode?: 'none' | 'opacity' | 'hue' | 'scheme';
  // Table-specific
  showHeader?: boolean;
  sortBy?: Array<{ displayName: string; desc: boolean }>;
  // Stat-specific
  colorMode?: 'value' | 'background' | 'background_solid' | 'none';
  graphMode?: 'area' | 'line' | 'none';
  textMode?: 'auto' | 'value' | 'value_and_name' | 'name' | 'none';
  // Text-specific
  content?: string;
  mode?: 'markdown' | 'html' | 'code';
  // BarChart-specific
  orientation?: 'horizontal' | 'vertical';
  barWidth?: number;
  groupWidth?: number;
  stacking?: 'none' | 'normal' | 'percent';
  // PieChart-specific
  pieType?: 'pie' | 'donut';
  // Heatmap-specific
  yAxisReversed?: boolean;
  cellGap?: number;
  // Logs-specific
  showTime?: boolean;
  showLabels?: boolean;
  wrapLogMessage?: boolean;
  sortOrder?: 'asc' | 'desc';
  // AlertList-specific
  alertStates?: string[];
  maxItems?: number;
}

// Grid Position
export interface GridPos {
  x: number;
  y: number;
  w: number;
  h: number;
}

// Panel
export interface Panel {
  id: string;
  type: PanelType;
  title: string;
  description: string;
  gridPos: GridPos;
  queries: Query[];
  transforms: Transform[];
  thresholds: Threshold[];
  fieldOverrides: FieldOverride[];
  options: PanelOptions;
  datasource?: string;
}

// Dashboard
export interface Dashboard {
  id: string;
  uid: string;
  title: string;
  description: string;
  tags: string[];
  variables: Variable[];
  panels: Panel[];
  timeRange: TimeRange;
  refresh: string;
  version: number;
  createdAt: string;
  updatedAt: string;
}

// Data Frame (for query results)
export interface DataFrame {
  name: string;
  fields: DataField[];
  length: number;
}

export interface DataField {
  name: string;
  type: 'number' | 'string' | 'time' | 'boolean';
  values: (number | string | boolean | null)[];
  labels?: Record<string, string>;
}

// Alert
export interface Alert {
  id: string;
  name: string;
  state: 'ok' | 'pending' | 'alerting' | 'nodata' | 'paused';
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  labels: Record<string, string>;
}

// Notification
export interface AppNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
}

// App State
export interface DashboardState {
  dashboard: Dashboard;
  editingPanelId: string | null;
  isDirty: boolean;
  isLoading: boolean;
  notifications: AppNotification[];
  sidebarOpen: boolean;
  settingsOpen: boolean;
}

export interface ThemeState {
  mode: ThemeMode;
}

export interface RootState {
  dashboard: DashboardState;
  theme: ThemeState;
}
