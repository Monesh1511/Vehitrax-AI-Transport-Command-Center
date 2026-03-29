import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Reports from './pages/Reports';

function App() {
  return (
    <Router>
      <div className="app-container">
        <nav className="navbar">
          <div className="brand">
            <div className="brand-mark">VX</div>
            <div>
              <div className="navbar-brand">Vehitrax AI</div>
              <div className="navbar-subtitle">Transport Command Center</div>
            </div>
          </div>
          <div className="nav-links">
            <NavLink to="/" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>Dashboard</NavLink>
            <NavLink to="/history" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>History</NavLink>
            <NavLink to="/reports" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>Reports</NavLink>
          </div>
          <div className="nav-meta">
            <span className="pill">Sri Sairam Engineering College - Chennai</span>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/history" element={<History />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
