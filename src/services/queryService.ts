import { Query, DataFrame, DataField, Variable } from '../types';
import { interpolateVariables } from '../utils/variableInterpolation';

// Demo data generators
function generateTimeSeriesData(points: number = 60): { time: number[]; values: number[] } {
  const now = Date.now();
  const time: number[] = [];
  const values: number[] = [];
  let value = 50 + Math.random() * 50;

  for (let i = points; i >= 0; i--) {
    time.push(now - i * 60000);
    value += (Math.random() - 0.5) * 10;
    value = Math.max(0, Math.min(100, value));
    values.push(Math.round(value * 100) / 100);
  }

  return { time, values };
}

function generateGaugeValue(min: number = 0, max: number = 100): number {
  return Math.round((min + Math.random() * (max - min)) * 10) / 10;
}

function generateTableData(): DataFrame {
  const services = ['api-gateway', 'auth-service', 'user-service', 'payment-service', 'notification-service'];
  const statuses = ['success', 'success', 'success', 'failed', 'rolling-back'];
  const versions = ['v2.3.1', 'v1.8.0', 'v3.1.2', 'v2.0.0', 'v1.5.4'];

  return {
    name: 'deployments',
    length: services.length,
    fields: [
      { name: 'Service', type: 'string', values: services },
      { name: 'Version', type: 'string', values: versions },
      { name: 'Status', type: 'string', values: statuses },
      { name: 'Timestamp', type: 'time', values: services.map((_, i) => new Date(Date.now() - i * 3600000).toISOString()) },
      { name: 'Duration', type: 'string', values: ['45s', '1m 12s', '38s', '2m 5s', '55s'] },
    ],
  };
}

function generateBarData(): DataFrame {
  return {
    name: 'endpoints',
    length: 5,
    fields: [
      { name: 'Endpoint', type: 'string', values: ['/api/users', '/api/auth', '/api/products', '/api/orders', '/api/health'] },
      { name: 'Requests', type: 'number', values: [4520, 3890, 2750, 1980, 8900] },
    ],
  };
}

function generatePieData(): DataFrame {
  return {
    name: 'regions',
    length: 4,
    fields: [
      { name: 'Region', type: 'string', values: ['US East', 'US West', 'EU West', 'AP Southeast'] },
      { name: 'Traffic', type: 'number', values: [35, 28, 22, 15] },
    ],
  };
}

function generateHeatmapData(): DataFrame {
  const hours = 24;
  const buckets = 10;
  const timeValues: number[] = [];
  const bucketValues: number[] = [];
  const countValues: number[] = [];
  const now = Date.now();

  for (let h = 0; h < hours; h++) {
    for (let b = 0; b < buckets; b++) {
      timeValues.push(now - (hours - h) * 3600000);
      bucketValues.push(b * 50);
      countValues.push(Math.floor(Math.random() * 100));
    }
  }

  return {
    name: 'heatmap',
    length: timeValues.length,
    fields: [
      { name: 'Time', type: 'time', values: timeValues },
      { name: 'Bucket', type: 'number', values: bucketValues },
      { name: 'Count', type: 'number', values: countValues },
    ],
  };
}

function generateLogData(): DataFrame {
  const levels = ['INFO', 'INFO', 'WARN', 'INFO', 'ERROR', 'INFO', 'DEBUG', 'INFO', 'WARN', 'INFO'];
  const messages = [
    'Request processed successfully',
    'User authentication completed',
    'High memory usage detected on worker-3',
    'Cache refreshed for user-service',
    'Connection timeout to database replica',
    'Health check passed',
    'Variable interpolation cache miss',
    'Rate limiter threshold updated',
    'Slow query detected: 2.3s',
    'Deployment webhook received',
  ];

  return {
    name: 'logs',
    length: levels.length,
    fields: [
      { name: 'timestamp', type: 'time', values: levels.map((_, i) => new Date(Date.now() - i * 30000).toISOString()) },
      { name: 'level', type: 'string', values: levels },
      { name: 'message', type: 'string', values: messages },
      { name: 'service', type: 'string', values: levels.map(() => ['api-gateway', 'auth-service', 'user-service'][Math.floor(Math.random() * 3)]) },
    ],
  };
}

export async function executeQuery(
  query: Query,
  variables: Variable[],
  panelType: string
): Promise<DataFrame[]> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));

  const interpolatedExpr = interpolateVariables(query.expr, variables);
  console.log(`[QueryService] Executing: ${interpolatedExpr}`);

  // Return appropriate demo data based on panel type
  switch (panelType) {
    case 'stat': {
      const value = query.expr.includes('error_rate')
        ? Math.round(Math.random() * 5 * 100) / 100
        : Math.floor(Math.random() * 10000);
      return [{
        name: query.legendFormat || 'Value',
        length: 1,
        fields: [{ name: 'Value', type: 'number', values: [value] }],
      }];
    }
    case 'gauge': {
      return [{
        name: query.legendFormat || 'Value',
        length: 1,
        fields: [{ name: 'Value', type: 'number', values: [generateGaugeValue()] }],
      }];
    }
    case 'timeseries':
    case 'graph': {
      const { time, values } = generateTimeSeriesData();
      return [{
        name: query.legendFormat || query.refId,
        length: time.length,
        fields: [
          { name: 'Time', type: 'time', values: time },
          { name: 'Value', type: 'number', values: values },
        ],
      }];
    }
    case 'table':
      return [generateTableData()];
    case 'barchart':
      return [generateBarData()];
    case 'piechart':
      return [generatePieData()];
    case 'heatmap':
      return [generateHeatmapData()];
    case 'logs':
      return [generateLogData()];
    default:
      return [{
        name: 'default',
        length: 1,
        fields: [{ name: 'Value', type: 'number', values: [generateGaugeValue()] }],
      }];
  }
}

export function executeQueries(
  queries: Query[],
  variables: Variable[],
  panelType: string
): Promise<DataFrame[]> {
  return Promise.all(
    queries.map(q => executeQuery(q, variables, panelType))
  ).then(results => results.flat());
}
