import { Query } from '../../types';
import { generateId } from '../../utils/formatting';
import './QueryEditor.css';

interface QueryEditorProps {
  queries: Query[];
  onChange: (queries: Query[]) => void;
}

export function QueryEditor({ queries, onChange }: QueryEditorProps) {
  const handleQueryChange = (index: number, field: keyof Query, value: string) => {
    const updated = [...queries];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addQuery = () => {
    const refId = String.fromCharCode(65 + queries.length); // A, B, C...
    onChange([
      ...queries,
      {
        id: generateId('query'),
        datasourceId: 'demo',
        expr: '',
        legendFormat: '',
        refId,
      },
    ]);
  };

  const removeQuery = (index: number) => {
    onChange(queries.filter((_, i) => i !== index));
  };

  return (
    <div className="query-editor">
      <div className="query-editor-header">
        <h4>Queries</h4>
        <button className="add-query-btn" onClick={addQuery}>+ Add Query</button>
      </div>
      {queries.map((query, index) => (
        <div key={query.id} className="query-row">
          <span className="query-ref">{query.refId}</span>
          <div className="query-fields">
            <div className="query-field">
              <label>Expression</label>
              <input
                type="text"
                value={query.expr}
                onChange={e => handleQueryChange(index, 'expr', e.target.value)}
                placeholder="Enter query expression..."
              />
            </div>
            <div className="query-field">
              <label>Legend</label>
              <input
                type="text"
                value={query.legendFormat || ''}
                onChange={e => handleQueryChange(index, 'legendFormat', e.target.value)}
                placeholder="Legend format"
              />
            </div>
          </div>
          <button
            className="remove-query-btn"
            onClick={() => removeQuery(index)}
            title="Remove query"
          >
            x
          </button>
        </div>
      ))}
      {queries.length === 0 && (
        <div className="query-empty">
          No queries configured. Click "Add Query" to get started.
        </div>
      )}
    </div>
  );
}
