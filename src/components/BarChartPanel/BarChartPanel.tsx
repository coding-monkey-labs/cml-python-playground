import { Panel, DataFrame } from '../../types';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import './BarChartPanel.css';

interface BarChartPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

const COLORS = ['#7B61FF', '#FF6B6B', '#4ECB71', '#FFB020', '#36A2EB'];

export function BarChartPanel({ panel, data, height }: BarChartPanelProps) {
  if (data.length === 0) return <div className="barchart-empty">No data</div>;

  const frame = data[0];
  const categoryField = frame.fields.find(f => f.type === 'string');
  const valueFields = frame.fields.filter(f => f.type === 'number');

  if (!categoryField || valueFields.length === 0) {
    return <div className="barchart-empty">Invalid data format</div>;
  }

  const chartData = categoryField.values.map((cat, i) => {
    const point: Record<string, unknown> = { name: cat };
    valueFields.forEach(vf => {
      point[vf.name] = vf.values[i];
    });
    return point;
  });

  const isHorizontal = panel.options.orientation === 'horizontal';

  return (
    <div className="barchart-panel">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout={isHorizontal ? 'vertical' : 'horizontal'}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          {isHorizontal ? (
            <>
              <XAxis type="number" stroke="var(--text-secondary)" fontSize={11} tick={{ fill: 'var(--text-secondary)' }} />
              <YAxis type="category" dataKey="name" stroke="var(--text-secondary)" fontSize={11} tick={{ fill: 'var(--text-secondary)' }} width={80} />
            </>
          ) : (
            <>
              <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={11} tick={{ fill: 'var(--text-secondary)' }} />
              <YAxis stroke="var(--text-secondary)" fontSize={11} tick={{ fill: 'var(--text-secondary)' }} />
            </>
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
            }}
          />
          {valueFields.map((vf, i) => (
            <Bar
              key={vf.name}
              dataKey={vf.name}
              fill={COLORS[i % COLORS.length]}
              radius={[4, 4, 0, 0]}
              barSize={panel.options.barWidth ? panel.options.barWidth * 40 : undefined}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
