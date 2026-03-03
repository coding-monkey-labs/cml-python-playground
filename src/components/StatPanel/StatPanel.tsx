import { Panel, DataFrame } from '../../types';
import { formatNumber, getThresholdColor } from '../../utils/formatting';
import './StatPanel.css';

interface StatPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

export function StatPanel({ panel, data, width, height }: StatPanelProps) {
  const value = data[0]?.fields[0]?.values[0] as number ?? 0;
  const color = getThresholdColor(value, panel.thresholds);
  const colorMode = panel.options.colorMode || 'value';
  const graphMode = panel.options.graphMode || 'area';
  const textMode = panel.options.textMode || 'value_and_name';

  const isBackgroundColor = colorMode === 'background' || colorMode === 'background_solid';

  // Generate sparkline data
  const sparklinePoints = Array.from({ length: 20 }, (_, i) => {
    const noise = Math.sin(i * 0.5) * 20 + Math.random() * 10;
    return value * 0.7 + noise;
  });

  const maxVal = Math.max(...sparklinePoints);
  const minVal = Math.min(...sparklinePoints);
  const sparkHeight = height * 0.3;
  const sparkWidth = width;

  const getSparklinePath = () => {
    const points = sparklinePoints.map((v, i) => {
      const x = (i / (sparklinePoints.length - 1)) * sparkWidth;
      const y = sparkHeight - ((v - minVal) / (maxVal - minVal || 1)) * sparkHeight;
      return `${x},${y}`;
    });
    return `M ${points.join(' L ')}`;
  };

  const getAreaPath = () => {
    const line = getSparklinePath();
    return `${line} L ${sparkWidth},${sparkHeight} L 0,${sparkHeight} Z`;
  };

  return (
    <div
      className={`stat-panel ${isBackgroundColor ? 'bg-colored' : ''}`}
      style={isBackgroundColor ? { backgroundColor: color } : undefined}
    >
      <div className="stat-content">
        {(textMode === 'value_and_name' || textMode === 'name') && (
          <span className="stat-name">{panel.title}</span>
        )}
        {(textMode === 'value_and_name' || textMode === 'value' || textMode === 'auto') && (
          <span
            className="stat-value"
            style={!isBackgroundColor ? { color } : undefined}
          >
            {panel.queries[0]?.expr.includes('error_rate')
              ? `${value.toFixed(2)}%`
              : formatNumber(value)}
          </span>
        )}
      </div>
      {graphMode !== 'none' && (
        <div className="stat-sparkline">
          <svg width={sparkWidth} height={sparkHeight} viewBox={`0 0 ${sparkWidth} ${sparkHeight}`}>
            {graphMode === 'area' && (
              <path
                d={getAreaPath()}
                fill={isBackgroundColor ? 'rgba(255,255,255,0.15)' : `${color}20`}
              />
            )}
            <path
              d={getSparklinePath()}
              fill="none"
              stroke={isBackgroundColor ? 'rgba(255,255,255,0.5)' : color}
              strokeWidth={1.5}
            />
          </svg>
        </div>
      )}
    </div>
  );
}
