import React from 'react'
import { Card, ListGroup } from 'react-bootstrap'

function DynamicSummary({ component }) {
  const { label, data, value } = component
  const displayData = data || value

  if (!displayData) {
    return (
      <Card className="mb-3">
        <Card.Header>{label || 'Summary'}</Card.Header>
        <Card.Body>
          <p className="text-muted mb-0">No data available.</p>
        </Card.Body>
      </Card>
    )
  }

  // If it's a string (e.g., JSON policy), display as code
  if (typeof displayData === 'string') {
    return (
      <Card className="mb-3">
        <Card.Header>{label || 'Summary'}</Card.Header>
        <Card.Body>
          <pre className="mb-0" style={{ whiteSpace: 'pre-wrap' }}>
            {displayData}
          </pre>
        </Card.Body>
      </Card>
    )
  }

  // If it's an object, display as key-value pairs
  if (typeof displayData === 'object' && !Array.isArray(displayData)) {
    return (
      <Card className="mb-3">
        <Card.Header>{label || 'Summary'}</Card.Header>
        <ListGroup variant="flush">
          {Object.entries(displayData).map(([key, val]) => (
            <ListGroup.Item key={key} className="d-flex justify-content-between">
              <span className="fw-bold">{formatKey(key)}</span>
              <span>{formatValue(val)}</span>
            </ListGroup.Item>
          ))}
        </ListGroup>
      </Card>
    )
  }

  // Array
  if (Array.isArray(displayData)) {
    return (
      <Card className="mb-3">
        <Card.Header>{label || 'Summary'}</Card.Header>
        <ListGroup variant="flush">
          {displayData.map((item, idx) => (
            <ListGroup.Item key={idx}>
              {typeof item === 'object' ? JSON.stringify(item) : String(item)}
            </ListGroup.Item>
          ))}
        </ListGroup>
      </Card>
    )
  }

  return null
}

function formatKey(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export default DynamicSummary
