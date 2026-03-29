import React, { useEffect, useState } from 'react';
import { PunctualityBadge } from '../components/PunctualityBadge';

export default function History() {
  const [events, setEvents] = useState([]);
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const [isClearing, setIsClearing] = useState(false);
  const [searchHistory, setSearchHistory] = useState('');

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/reports/events?limit=100`);
        if (res.ok) {
          const data = await res.json();
          setEvents(data.events || []);
        }
      } catch (err) {
        console.error("Error fetching events:", err);
      }
    };
    fetchEvents();
  }, []);

  const handleReset = async () => {
    const confirmed = window.confirm('Clear all history entries? This cannot be undone.');
    if (!confirmed) return;
    try {
      setIsClearing(true);
      const res = await fetch(`${apiUrl}/api/events/clear`, { method: 'DELETE' });
      if (res.ok) {
        setEvents([]);
      }
    } catch (err) {
      console.error('Error clearing events:', err);
    } finally {
      setIsClearing(false);
    }
  };

  const normalizedSearch = String(searchHistory || '').toUpperCase();
  const filteredEvents = normalizedSearch
    ? events.filter((event) => {
        const plate = String(event.plate_number || '').toUpperCase();
        const bus = String(event.bus_number || '').toUpperCase();
        const driver = String(event.driver_name || '').toUpperCase();
        return (
          plate.includes(normalizedSearch) ||
          bus.includes(normalizedSearch) ||
          driver.includes(normalizedSearch)
        );
      })
    : events;

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="eyebrow">Operational Archive</p>
          <h2 className="page-title">Detection History</h2>
          <p className="page-subtitle">Latest 100 entries captured by the system.</p>
        </div>
        <div className="header-actions">
          <button onClick={handleReset} disabled={isClearing} className="btn btn-outline">
            {isClearing ? 'Clearing...' : 'Reset History'}
          </button>
        </div>
      </div>
      <div className="table-toolbar">
        <div className="table-meta">Showing {filteredEvents.length} entries</div>
        <input
          type="text"
          value={searchHistory}
          onChange={(e) => setSearchHistory(e.target.value)}
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
            {filteredEvents.map(event => (
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
            {filteredEvents.length === 0 && (
              <tr><td colSpan="8" className="empty-state">No matching history entries</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
