import { Panel, DataFrame } from '../../types';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import './PieChartPanel.css';

interface PieChartPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

const COLORS = ['#7B61FF', '#FF6B6B', '#4ECB71', '#FFB020', '#36A2EB', '#FF9FF3', '#54A0FF', '#5F27CD'];

export function PieChartPanel({ panel, data, height }: PieChartPanelProps) {
  if (data.length === 0) return <div className="piechart-empty">No data</div>;

  const frame = data[0];
  const nameField = frame.fields.find(f => f.type === 'string');
  const valueField = frame.fields.find(f => f.type === 'number');

  if (!nameField || !valueField) {
    return <div className="piechart-empty">Invalid data format</div>;
  }

  const chartData = nameField.values.map((name, i) => ({
    name: String(name),
    value: valueField.values[i] as number,
  }));

  const isDonut = panel.options.pieType === 'donut';

  return (
    <div className="piechart-panel">
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={isDonut ? '55%' : 0}
            outerRadius="80%"
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
