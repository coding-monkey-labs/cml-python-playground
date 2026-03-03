import { useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { updatePanelGridPos } from '../../store/dashboardSlice';
import { GridLayout } from '../GridLayout/GridLayout';
import { PanelContainer } from '../PanelContainer/PanelContainer';
import { VariableControls } from '../VariableControls/VariableControls';
import { AddPanelWidget } from '../AddPanelWidget/AddPanelWidget';
import './Dashboard.css';

export function Dashboard() {
  const dispatch = useAppDispatch();
  const panels = useAppSelector(state => state.dashboard.dashboard.panels);
  const variables = useAppSelector(state => state.dashboard.dashboard.variables);

  const handleLayoutChange = useCallback((layout: Array<{ i: string; x: number; y: number; w: number; h: number }>) => {
    layout.forEach(item => {
      dispatch(updatePanelGridPos({
        id: item.i,
        gridPos: { x: item.x, y: item.y, w: item.w, h: item.h },
      }));
    });
  }, [dispatch]);

  return (
    <div className="dashboard">
      {variables.length > 0 && <VariableControls />}
      <GridLayout
        panels={panels}
        onLayoutChange={handleLayoutChange}
      >
        {panels.map(panel => (
          <div key={panel.id} data-grid={panel.gridPos}>
            <PanelContainer panel={panel} />
          </div>
        ))}
      </GridLayout>
      <AddPanelWidget />
    </div>
  );
}
