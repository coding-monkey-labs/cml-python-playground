/**
 * Format a number with appropriate units (K, M, B)
 */
export function formatNumber(value: number, decimals: number = 1): string {
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(decimals)}B`;
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(decimals)}M`;
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(decimals)}K`;
  if (Number.isInteger(value)) return value.toString();
  return value.toFixed(decimals);
}

/**
 * Format a percentage value
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format a duration in milliseconds to human readable
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
  return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`;
}

/**
 * Format bytes to human readable
 */
export function formatBytes(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(decimals)} ${sizes[i]}`;
}

/**
 * Format a timestamp to locale string
 */
export function formatTimestamp(ts: string | number): string {
  const date = new Date(ts);
  return date.toLocaleString();
}

/**
 * Format a relative time string (e.g., "2 minutes ago")
 */
export function formatRelativeTime(ts: string | number): string {
  const now = Date.now();
  const then = new Date(ts).getTime();
  const diff = now - then;

  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
}

/**
 * Get color for a value based on thresholds
 */
export function getThresholdColor(
  value: number,
  thresholds: Array<{ value: number; color: string }>
): string {
  const sorted = [...thresholds].sort((a, b) => b.value - a.value);
  for (const threshold of sorted) {
    if (value >= threshold.value) return threshold.color;
  }
  return thresholds[0]?.color || '#73BF69';
}

/**
 * Generate a unique ID
 */
export function generateId(prefix: string = 'id'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
