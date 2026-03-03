import { Panel, DataFrame } from '../../types';
import { formatNumber, getThresholdColor } from '../../utils/formatting';
import './GaugePanel.css';

interface GaugePanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

export function GaugePanel({ panel, data, width, height }: GaugePanelProps) {
  const min = panel.options.minValue ?? 0;
  const max = panel.options.maxValue ?? 100;
  const value = data[0]?.fields[0]?.values[0] as number ?? 0;
  const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const color = getThresholdColor(value, panel.thresholds);

  const size = Math.min(width, height) * 0.8;
  const cx = width / 2;
  const cy = height / 2 + size * 0.1;
  const radius = size * 0.4;
  const strokeWidth = size * 0.08;

  // Arc from -135deg to 135deg (270 degree sweep)
  const startAngle = -225;
  const endAngle = 45;
  const sweep = endAngle - startAngle;
  const valueAngle = startAngle + (sweep * percentage) / 100;

  const toRad = (deg: number) => (deg * Math.PI) / 180;

  const arcPath = (startDeg: number, endDeg: number) => {
    const start = {
      x: cx + radius * Math.cos(toRad(startDeg)),
      y: cy + radius * Math.sin(toRad(startDeg)),
    };
    const end = {
      x: cx + radius * Math.cos(toRad(endDeg)),
      y: cy + radius * Math.sin(toRad(endDeg)),
    };
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  };

  return (
    <div className="gauge-panel">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Background arc */}
        <path
          d={arcPath(startAngle, endAngle)}
          fill="none"
          stroke="var(--border-color)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Value arc */}
        {percentage > 0 && (
          <path
            d={arcPath(startAngle, valueAngle)}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        )}
        {/* Threshold markers */}
        {panel.options.showThresholdMarkers && panel.thresholds.map((threshold, i) => {
          const tp = ((threshold.value - min) / (max - min)) * 100;
          const angle = startAngle + (sweep * tp) / 100;
          const markerLen = strokeWidth * 0.6;
          const innerR = radius - markerLen;
          const outerR = radius + markerLen;
          return (
            <line
              key={i}
              x1={cx + innerR * Math.cos(toRad(angle))}
              y1={cy + innerR * Math.sin(toRad(angle))}
              x2={cx + outerR * Math.cos(toRad(angle))}
              y2={cy + outerR * Math.sin(toRad(angle))}
              stroke={threshold.color}
              strokeWidth={2}
            />
          );
        })}
        {/* Value text */}
        <text
          x={cx}
          y={cy - size * 0.05}
          textAnchor="middle"
          className="gauge-value"
          fill={color}
          fontSize={size * 0.18}
          fontWeight="bold"
        >
          {formatNumber(value)}
        </text>
        {/* Min/Max labels */}
        {panel.options.showThresholdLabels && (
          <>
            <text
              x={cx - radius * 0.8}
              y={cy + radius * 0.5}
              textAnchor="middle"
              className="gauge-label"
              fill="var(--text-secondary)"
              fontSize={size * 0.07}
            >
              {min}
            </text>
            <text
              x={cx + radius * 0.8}
              y={cy + radius * 0.5}
              textAnchor="middle"
              className="gauge-label"
              fill="var(--text-secondary)"
              fontSize={size * 0.07}
            >
              {max}
            </text>
          </>
        )}
      </svg>
    </div>
  );
}
