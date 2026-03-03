import { ReactNode, useCallback } from 'react';
import { Panel } from '../../types';
import './GridLayout.css';

interface GridLayoutProps {
  panels: Panel[];
  onLayoutChange: (layout: Array<{ i: string; x: number; y: number; w: number; h: number }>) => void;
  children: ReactNode;
}

// Simplified grid layout using CSS Grid
// In production, you'd use react-grid-layout for drag-and-drop
export function GridLayout({ panels, onLayoutChange: _onLayoutChange, children }: GridLayoutProps) {
  const cols = 12;

  const getMaxRow = useCallback(() => {
    return panels.reduce((max, p) => Math.max(max, p.gridPos.y + p.gridPos.h), 0);
  }, [panels]);

  const maxRow = getMaxRow();
  const rowHeight = 120;

  return (
    <div
      className="grid-layout"
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gridAutoRows: `${rowHeight}px`,
        gap: '8px',
        padding: '8px',
        minHeight: `${maxRow * rowHeight + maxRow * 8}px`,
      }}
    >
      {panels.map((panel, index) => {
        const child = Array.isArray(children)
          ? (children as ReactNode[])[index]
          : index === 0 ? children : null;

        return (
          <div
            key={panel.id}
            className="grid-item"
            style={{
              gridColumn: `${panel.gridPos.x + 1} / span ${panel.gridPos.w}`,
              gridRow: `${panel.gridPos.y + 1} / span ${panel.gridPos.h}`,
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
}
