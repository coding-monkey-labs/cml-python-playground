import React from 'react'
import { Form } from 'react-bootstrap'

function DynamicForm({ components, formData, onChange }) {
  return (
    <Form>
      {components.map((comp) => {
        switch (comp.type) {
          case 'text':
            return (
              <Form.Group key={comp.key} className="mb-3">
                <Form.Label>{comp.label}</Form.Label>
                <Form.Control
                  type="text"
                  placeholder={comp.placeholder || ''}
                  value={formData[comp.key] ?? comp.value ?? ''}
                  onChange={(e) => onChange(comp.key, e.target.value)}
                  required={comp.required}
                  readOnly={comp.read_only}
                />
              </Form.Group>
            )

          case 'select':
            return (
              <Form.Group key={comp.key} className="mb-3">
                <Form.Label>{comp.label}</Form.Label>
                <Form.Select
                  value={formData[comp.key] ?? comp.value ?? ''}
                  onChange={(e) => onChange(comp.key, e.target.value)}
                >
                  <option value="">Select...</option>
                  {(comp.options || []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            )

          case 'checkbox':
            return (
              <Form.Group key={comp.key} className="mb-3">
                <Form.Check
                  type="checkbox"
                  label={comp.label}
                  checked={formData[comp.key] ?? comp.value ?? false}
                  onChange={(e) => onChange(comp.key, e.target.checked)}
                />
              </Form.Group>
            )

          default:
            return null
        }
      })}
    </Form>
  )
}

export default DynamicForm
