import React, { useEffect, useState } from 'react';
import { PunctualityBadge } from '../components/PunctualityBadge';

export default function Reports() {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const [report, setReport] = useState({ events: [], college_start: '09:00 AM', college_end: '04:10 PM' });
  const [showLateOnly, setShowLateOnly] = useState(true);
  const [isClearing, setIsClearing] = useState(false);
  const [searchReports, setSearchReports] = useState('');

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/reports/events?limit=100`);
        if (res.ok) {
          setReport(await res.json());
        }
      } catch (err) {
        console.error('Error fetching report:', err);
      }
    };

    fetchReport();
  }, []);

  const handleReset = async () => {
    const confirmed = window.confirm('Clear all report entries? This cannot be undone.');
    if (!confirmed) return;
    try {
      setIsClearing(true);
      const res = await fetch(`${apiUrl}/api/events/clear`, { method: 'DELETE' });
      if (res.ok) {
        setReport((prev) => ({ ...prev, events: [] }));
      }
    } catch (err) {
      console.error('Error clearing report entries:', err);
    } finally {
      setIsClearing(false);
    }
  };

  const delayedEvents = report.events.filter((event) => event.status === 'Delayed');
  const baseEvents = showLateOnly ? delayedEvents : report.events;
  const normalizedSearch = String(searchReports || '').toUpperCase();
  const visibleEvents = normalizedSearch
    ? baseEvents.filter((event) => {
        const plate = String(event.plate_number || '').toUpperCase();
        const bus = String(event.bus_number || '').toUpperCase();
        const driver = String(event.driver_name || '').toUpperCase();
        return (
          plate.includes(normalizedSearch) ||
          bus.includes(normalizedSearch) ||
          driver.includes(normalizedSearch)
        );
      })
    : baseEvents;

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="eyebrow">Automated Insights</p>
          <h2 className="page-title">Reports & Compliance</h2>
          <p className="page-subtitle">
            College timing rules: Enter before {report.college_start}, Delayed after {report.college_start}, Exit after {report.college_end}.
          </p>
        </div>
        <div className="header-actions">
          <button
            onClick={() => setShowLateOnly((prev) => !prev)}
            className={`btn btn-outline ${showLateOnly ? 'is-active' : ''}`}
          >
            {showLateOnly ? 'Showing Late Buses' : 'Showing All Buses'}
          </button>
          <button onClick={handleReset} disabled={isClearing} className="btn btn-outline">
            {isClearing ? 'Clearing...' : 'Reset Reports'}
          </button>
          <span className="pill">Late buses: {delayedEvents.length}</span>
        </div>
      </div>

      <div className="table-toolbar">
        <div className="table-meta">Showing {visibleEvents.length} entries</div>
        <input
          type="text"
          value={searchReports}
          onChange={(e) => setSearchReports(e.target.value)}
          placeholder="Search plate, bus, or driver"
          className="search-input"
        />
      </div>
      <div className="card table-card">
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Day</th>
              <th>Time</th>
              <th>Status</th>
              <th>Score</th>
              <th>Plate</th>
              <th>Bus</th>
              <th>Driver</th>
            </tr>
          </thead>
          <tbody>
            {visibleEvents.map((event) => (
              <tr key={event.event_id}>
                <td>{event.date}</td>
                <td>{event.day}</td>
                <td>{event.time}</td>
                <td>
                  <PunctualityBadge status={event.status} />
                </td>
                <td>{event.score}</td>
                <td style={{ fontWeight: 700 }}>{event.plate_number}</td>
                <td>{event.bus_number}</td>
                <td>{event.driver_name}</td>
              </tr>
            ))}
            {visibleEvents.length === 0 && (
              <tr>
                <td colSpan="8" className="empty-state">
                  {normalizedSearch ? 'No matching report entries' : showLateOnly ? 'No late bus entries yet.' : 'No report entries yet.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
