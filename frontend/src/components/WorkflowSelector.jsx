import React from 'react'
import { Card, Row, Col, Button } from 'react-bootstrap'
import { startWorkflow } from '../services/api'

function WorkflowSelector({ workflows, onStarted, onError }) {
  const handleStart = async (workflowId) => {
    try {
      const session = await startWorkflow(workflowId)
      onStarted(session)
    } catch (err) {
      onError(err.response?.data?.detail || 'Failed to start workflow')
    }
  }

  const categories = {
    'List & Browse': workflows.filter((w) =>
      w.id.startsWith('list_') || w.id.startsWith('get_')
    ),
    'Create': workflows.filter((w) => w.id.startsWith('create_')),
    'Update': workflows.filter((w) => w.id.startsWith('update_')),
    'Delete': workflows.filter((w) => w.id.startsWith('delete_')),
    'Inspect': workflows.filter((w) => w.id === 'inspect_bucket'),
    'Bulk Operations': workflows.filter((w) => w.id.startsWith('bulk_')),
  }

  return (
    <>
      <h2 className="mb-4">Available Workflows</h2>
      {Object.entries(categories).map(([category, wfs]) =>
        wfs.length > 0 ? (
          <div key={category} className="mb-4">
            <h5 className="text-muted mb-3">{category}</h5>
            <Row xs={1} md={2} lg={3} className="g-3">
              {wfs.map((wf) => (
                <Col key={wf.id}>
                  <Card className="h-100">
                    <Card.Body className="d-flex flex-column">
                      <Card.Title>{wf.name}</Card.Title>
                      <Card.Text className="text-muted flex-grow-1">
                        {wf.description}
                      </Card.Text>
                      <Button
                        variant="primary"
                        onClick={() => handleStart(wf.id)}
                      >
                        Start
                      </Button>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        ) : null
      )}
    </>
  )
}

export default WorkflowSelector
