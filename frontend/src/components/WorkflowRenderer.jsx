import React, { useState, useEffect, useCallback } from 'react'
import { Card, Button, ButtonGroup, Spinner, Alert } from 'react-bootstrap'
import { submitInput, getState } from '../services/api'
import DynamicForm from './DynamicForm'
import DynamicTable from './DynamicTable'
import DynamicSummary from './DynamicSummary'

function WorkflowRenderer({ session, onEnd, onError }) {
  const [currentState, setCurrentState] = useState(session)
  const [formData, setFormData] = useState({})
  const [loading, setLoading] = useState(false)

  // Auto-advance for states that have actions (loading states)
  useEffect(() => {
    const ui = currentState.ui
    if (!ui) return

    // Check if this is a loading/action state (has transitions but only non-interactive components)
    const hasOnlyMessages = ui.components.every(
      (c) => c.type === 'message' || c.type === 'summary'
    )
    const hasExactlyOneTransition = ui.allowed_actions.length === 1

    if (hasOnlyMessages && hasExactlyOneTransition) {
      // Auto-advance after a short delay to show loading state
      const timer = setTimeout(() => {
        handleAction(ui.allowed_actions[0])
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [currentState.ui?.state_id])

  const handleAction = useCallback(
    async (action) => {
      if (loading) return
      setLoading(true)

      try {
        const response = await submitInput(
          currentState.session_id,
          action,
          formData
        )

        if (response.completed) {
          onEnd()
          return
        }

        setCurrentState(response)
        setFormData({})
      } catch (err) {
        onError(err.response?.data?.detail || 'Action failed')
      } finally {
        setLoading(false)
      }
    },
    [currentState.session_id, formData, loading, onEnd, onError]
  )

  const handleFormChange = useCallback((key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
  }, [])

  if (!currentState.ui) {
    return <Spinner animation="border" />
  }

  const { ui } = currentState

  // Separate components by type for rendering
  const formComponents = ui.components.filter((c) =>
    ['text', 'select', 'checkbox'].includes(c.type)
  )
  const tableComponents = ui.components.filter((c) => c.type === 'table')
  const messageComponents = ui.components.filter((c) => c.type === 'message')
  const summaryComponents = ui.components.filter((c) => c.type === 'summary')

  return (
    <Card>
      <Card.Header>
        <Card.Title className="mb-0">{ui.title}</Card.Title>
      </Card.Header>
      <Card.Body>
        {ui.description && (
          <p className="text-muted mb-3">{ui.description}</p>
        )}

        {/* Messages */}
        {messageComponents.map((comp, i) => (
          <Alert key={i} variant={comp.variant || 'info'} className="mb-2">
            {comp.label}
          </Alert>
        ))}

        {/* Summary cards */}
        {summaryComponents.map((comp, i) => (
          <DynamicSummary key={i} component={comp} />
        ))}

        {/* Tables */}
        {tableComponents.map((comp, i) => (
          <DynamicTable
            key={i}
            component={comp}
            onRowSelect={(row) =>
              handleFormChange(comp.key, row)
            }
          />
        ))}

        {/* Form inputs */}
        {formComponents.length > 0 && (
          <DynamicForm
            components={formComponents}
            formData={formData}
            onChange={handleFormChange}
          />
        )}

        {/* Action buttons */}
        {ui.allowed_actions.length > 0 && (
          <div className="mt-3 d-flex gap-2 flex-wrap">
            {ui.allowed_actions.map((action) => (
              <Button
                key={action}
                variant={getButtonVariant(action)}
                onClick={() => handleAction(action)}
                disabled={loading}
              >
                {loading ? (
                  <Spinner animation="border" size="sm" className="me-1" />
                ) : null}
                {formatActionLabel(action)}
              </Button>
            ))}
          </div>
        )}
      </Card.Body>
    </Card>
  )
}

function getButtonVariant(action) {
  if (action.includes('delete') || action.includes('danger')) return 'danger'
  if (action.includes('cancel') || action === 'back') return 'secondary'
  if (action.includes('confirm') || action === 'apply') return 'warning'
  if (action === 'done') return 'outline-primary'
  return 'primary'
}

function formatActionLabel(action) {
  return action
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export default WorkflowRenderer
