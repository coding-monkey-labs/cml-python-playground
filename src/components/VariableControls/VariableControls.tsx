import { useAppSelector, useAppDispatch } from '../../store';
import { setVariableValue } from '../../store/dashboardSlice';
import './VariableControls.css';

export function VariableControls() {
  const dispatch = useAppDispatch();
  const variables = useAppSelector(state => state.dashboard.dashboard.variables);

  return (
    <div className="variable-controls">
      {variables.map(variable => (
        <div key={variable.id} className="variable-item">
          <label className="variable-label">{variable.label || variable.name}</label>
          {variable.type === 'textbox' ? (
            <input
              className="variable-input"
              type="text"
              value={variable.current}
              onChange={e => dispatch(setVariableValue({ id: variable.id, value: e.target.value }))}
              placeholder={variable.name}
            />
          ) : (
            <select
              className="variable-select"
              value={variable.current}
              onChange={e => dispatch(setVariableValue({ id: variable.id, value: e.target.value }))}
            >
              {variable.includeAll && <option value="__all__">All</option>}
              {variable.options.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          )}
        </div>
      ))}
    </div>
  );
}
