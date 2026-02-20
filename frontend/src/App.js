import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Container, Navbar, Nav } from 'react-bootstrap';
import { FiFilm, FiHome, FiList } from 'react-icons/fi';
import Dashboard from './pages/Dashboard';
import JobDetail from './pages/JobDetail';

function App() {
  return (
    <Router>
      <div className="app-wrapper">
        <Navbar bg="dark" variant="dark" expand="lg" className="mb-0">
          <Container fluid>
            <Navbar.Brand as={Link} to="/" className="d-flex align-items-center">
              <FiFilm className="me-2" size={24} />
              <span className="fw-bold">AI Video Cleaner</span>
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="main-nav" />
            <Navbar.Collapse id="main-nav">
              <Nav className="ms-auto">
                <Nav.Link as={Link} to="/">
                  <FiHome className="me-1" /> Dashboard
                </Nav.Link>
                <Nav.Link as={Link} to="/">
                  <FiList className="me-1" /> Jobs
                </Nav.Link>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Container fluid className="main-content py-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs/:jobId" element={<JobDetail />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}

export default App;
