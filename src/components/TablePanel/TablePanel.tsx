import { Panel, DataFrame } from '../../types';
import './TablePanel.css';

interface TablePanelProps {
  panel: Panel;
  data: DataFrame[];
  width: number;
  height: number;
}

export function TablePanel({ panel, data }: TablePanelProps) {
  if (data.length === 0 || data[0].fields.length === 0) {
    return <div className="table-panel-empty">No data</div>;
  }

  const frame = data[0];
  const showHeader = panel.options.showHeader !== false;

  return (
    <div className="table-panel">
      <div className="table-scroll">
        <table>
          {showHeader && (
            <thead>
              <tr>
                {frame.fields.map(field => (
                  <th key={field.name}>{field.name}</th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {Array.from({ length: frame.length }, (_, rowIdx) => (
              <tr key={rowIdx}>
                {frame.fields.map(field => {
                  const val = field.values[rowIdx];
                  const cellClass = field.name === 'Status'
                    ? `status-${String(val).toLowerCase()}`
                    : '';
                  return (
                    <td key={field.name} className={cellClass}>
                      {field.type === 'time'
                        ? new Date(val as string).toLocaleString()
                        : String(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
