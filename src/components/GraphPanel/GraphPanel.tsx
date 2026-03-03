import { Panel, DataFrame } from '../../types';
import { TimeSeriesPanel } from '../TimeSeriesPanel/TimeSeriesPanel';

interface GraphPanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

// Graph panel is an alias for TimeSeries panel
export function GraphPanel(props: GraphPanelProps) {
  return <TimeSeriesPanel {...props} />;
}
