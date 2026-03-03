import { Panel, DataFrame } from '../../types';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import './TimeSeriesPanel.css';

interface TimeSeriesPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

const COLORS = ['#7B61FF', '#FF6B6B', '#4ECB71', '#FFB020', '#36A2EB', '#FF9FF3'];

export function TimeSeriesPanel({ panel, data, height }: TimeSeriesPanelProps) {
  const drawStyle = panel.options.drawStyle || 'line';
  const fillOpacity = (panel.options.fillOpacity ?? 20) / 100;
  const lineWidth = panel.options.lineWidth ?? 2;

  // Merge data frames into chart data
  const chartData: Record<string, unknown>[] = [];

  if (data.length > 0) {
    const timeField = data[0].fields.find(f => f.type === 'time');
    const timeValues = timeField?.values || [];

    timeValues.forEach((time, i) => {
      const point: Record<string, unknown> = {
        time: typeof time === 'number' ? time : new Date(time as string).getTime(),
      };
      data.forEach((frame, fi) => {
        const valueField = frame.fields.find(f => f.type === 'number');
        if (valueField) {
          point[frame.name || `Series ${fi + 1}`] = valueField.values[i];
        }
      });
      chartData.push(point);
    });
  }

  const seriesNames = data.map((frame, i) => frame.name || `Series ${i + 1}`);

  const formatTime = (ts: number) => {
    const d = new Date(ts);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  };

  const ChartComponent = drawStyle === 'line' ? LineChart : AreaChart;

  return (
    <div className="timeseries-panel">
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis
            dataKey="time"
            tickFormatter={formatTime}
            stroke="var(--text-secondary)"
            fontSize={11}
            tick={{ fill: 'var(--text-secondary)' }}
          />
          <YAxis
            stroke="var(--text-secondary)"
            fontSize={11}
            tick={{ fill: 'var(--text-secondary)' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
            }}
            labelFormatter={formatTime}
          />
          <Legend />
          {seriesNames.map((name, i) => (
            drawStyle === 'line' ? (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={lineWidth}
                dot={panel.options.showPoints === 'always'}
                activeDot={{ r: 4 }}
              />
            ) : (
              <Area
                key={name}
                type="monotone"
                dataKey={name}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={lineWidth}
                fill={COLORS[i % COLORS.length]}
                fillOpacity={fillOpacity}
              />
            )
          ))}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}
