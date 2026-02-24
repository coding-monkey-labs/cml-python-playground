import React from 'react'
import { Table, Badge } from 'react-bootstrap'

function DynamicTable({ component, onRowSelect }) {
  const { columns = [], data = [], label } = component

  if (!data || data.length === 0) {
    return (
      <div className="mb-3">
        {label && <h6>{label}</h6>}
        <p className="text-muted">No data available.</p>
      </div>
    )
  }

  return (
    <div className="mb-3">
      {label && <h6>{label}</h6>}
      <Table striped bordered hover responsive size="sm">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{formatColumnHeader(col)}</th>
            ))}
            {onRowSelect && <th>Action</th>}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col}>{formatCellValue(row[col])}</td>
              ))}
              {onRowSelect && (
                <td>
                  <Badge
                    bg="primary"
                    role="button"
                    onClick={() => onRowSelect(row)}
                    style={{ cursor: 'pointer' }}
                  >
                    Select
                  </Badge>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </Table>
      <small className="text-muted">{data.length} item(s)</small>
    </div>
  )
}

function formatColumnHeader(col) {
  return col
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatCellValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export default DynamicTable
