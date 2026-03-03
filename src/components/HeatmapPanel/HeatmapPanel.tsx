import { Panel, DataFrame } from '../../types';
import './HeatmapPanel.css';

interface HeatmapPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

export function HeatmapPanel({ data, width, height }: HeatmapPanelProps) {
  if (data.length === 0) return <div className="heatmap-empty">No data</div>;

  // Generate a simple heatmap visualization
  const cols = 24;
  const rows = 10;
  const cellWidth = (width - 40) / cols;
  const cellHeight = (height - 30) / rows;
  const gap = 1;

  const getColor = (value: number) => {
    const intensity = Math.min(1, value / 100);
    if (intensity < 0.25) return `rgba(115, 191, 105, ${intensity * 4})`;
    if (intensity < 0.5) return `rgba(255, 152, 48, ${(intensity - 0.25) * 4})`;
    if (intensity < 0.75) return `rgba(255, 120, 10, ${(intensity - 0.5) * 4 * 0.5 + 0.5})`;
    return `rgba(242, 73, 92, ${(intensity - 0.75) * 4 * 0.3 + 0.7})`;
  };

  // Generate heat values from data or random
  const values: number[][] = [];
  for (let r = 0; r < rows; r++) {
    values[r] = [];
    for (let c = 0; c < cols; c++) {
      const idx = r * cols + c;
      const countField = data[0]?.fields.find(f => f.name === 'Count');
      values[r][c] = countField ? (countField.values[idx % countField.values.length] as number) : Math.random() * 100;
    }
  }

  return (
    <div className="heatmap-panel">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Y-axis labels */}
        {Array.from({ length: rows }, (_, r) => (
          <text
            key={`y-${r}`}
            x={30}
            y={r * cellHeight + cellHeight / 2 + 4}
            textAnchor="end"
            fontSize={9}
            fill="var(--text-secondary)"
          >
            {(rows - r) * 50}ms
          </text>
        ))}
        {/* Cells */}
        {values.map((row, r) =>
          row.map((val, c) => (
            <rect
              key={`${r}-${c}`}
              x={35 + c * (cellWidth + gap)}
              y={r * (cellHeight + gap)}
              width={cellWidth - gap}
              height={cellHeight - gap}
              fill={getColor(val)}
              rx={1}
            >
              <title>{`${val.toFixed(0)} requests at ${(rows - r) * 50}ms, hour ${c}`}</title>
            </rect>
          ))
        )}
        {/* X-axis labels */}
        {Array.from({ length: cols }, (_, c) => (
          c % 4 === 0 ? (
            <text
              key={`x-${c}`}
              x={35 + c * (cellWidth + gap) + cellWidth / 2}
              y={height - 2}
              textAnchor="middle"
              fontSize={9}
              fill="var(--text-secondary)"
            >
              {`${c}:00`}
            </text>
          ) : null
        ))}
      </svg>
    </div>
  );
}
