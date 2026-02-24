import React, { useState, useEffect } from 'react'
import { Container, Navbar, Nav, Alert } from 'react-bootstrap'
import WorkflowRenderer from './components/WorkflowRenderer'
import WorkflowSelector from './components/WorkflowSelector'
import { listWorkflows } from './services/api'

function App() {
  const [workflows, setWorkflows] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadWorkflows()
  }, [])

  const loadWorkflows = async () => {
    try {
      const data = await listWorkflows()
      setWorkflows(data)
      setError(null)
    } catch (err) {
      setError('Failed to connect to backend. Is the server running?')
    }
  }

  const handleWorkflowStarted = (session) => {
    setActiveSession(session)
    setError(null)
  }

  const handleWorkflowEnd = () => {
    setActiveSession(null)
  }

  return (
    <>
      <Navbar bg="dark" variant="dark" className="mb-4">
        <Container>
          <Navbar.Brand>ObjectScale Workbench</Navbar.Brand>
          <Nav className="me-auto">
            {activeSession && (
              <Nav.Link onClick={handleWorkflowEnd}>
                Back to Workflows
              </Nav.Link>
            )}
          </Nav>
        </Container>
      </Navbar>

      <Container>
        {error && (
          <Alert variant="danger" dismissible onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {activeSession ? (
          <WorkflowRenderer
            session={activeSession}
            onEnd={handleWorkflowEnd}
            onError={setError}
          />
        ) : (
          <WorkflowSelector
            workflows={workflows}
            onStarted={handleWorkflowStarted}
            onError={setError}
          />
        )}
      </Container>
    </>
  )
}

export default App
