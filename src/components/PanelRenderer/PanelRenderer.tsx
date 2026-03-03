import { Panel, DataFrame } from '../../types';
import { GaugePanel } from '../GaugePanel/GaugePanel';
import { GraphPanel } from '../GraphPanel/GraphPanel';
import { TablePanel } from '../TablePanel/TablePanel';
import { StatPanel } from '../StatPanel/StatPanel';
import { TextPanel } from '../TextPanel/TextPanel';
import { TimeSeriesPanel } from '../TimeSeriesPanel/TimeSeriesPanel';
import { BarChartPanel } from '../BarChartPanel/BarChartPanel';
import { PieChartPanel } from '../PieChartPanel/PieChartPanel';
import { HeatmapPanel } from '../HeatmapPanel/HeatmapPanel';
import { LogsPanel } from '../LogsPanel/LogsPanel';
import { AlertListPanel } from '../AlertListPanel/AlertListPanel';

interface PanelRendererProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

export function PanelRenderer({ panel, data, width, height }: PanelRendererProps) {
  const props = { panel, data, width, height };

  switch (panel.type) {
    case 'gauge':
      return <GaugePanel {...props} />;
    case 'graph':
      return <GraphPanel {...props} />;
    case 'table':
      return <TablePanel {...props} />;
    case 'stat':
      return <StatPanel {...props} />;
    case 'text':
      return <TextPanel {...props} />;
    case 'timeseries':
      return <TimeSeriesPanel {...props} />;
    case 'barchart':
      return <BarChartPanel {...props} />;
    case 'piechart':
      return <PieChartPanel {...props} />;
    case 'heatmap':
      return <HeatmapPanel {...props} />;
    case 'logs':
      return <LogsPanel {...props} />;
    case 'alertlist':
      return <AlertListPanel {...props} />;
    default:
      return (
        <div className="panel-unsupported">
          <p>Unsupported panel type: <strong>{panel.type}</strong></p>
        </div>
      );
  }
}
