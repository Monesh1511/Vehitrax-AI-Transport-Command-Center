import React from 'react';
import { Activity, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';

export function StatsBar({ summary }) {
  if (!summary) return <div className="spinner"></div>;

  return (
    <div className="stats-container">
      <div className="stat-box">
        <div className="stat-icon"><Activity size={24} /></div>
        <div className="stat-info">
          <h3>Total Buses</h3>
          <p>{summary.total_buses}</p>
        </div>
      </div>
      <div className="stat-box">
        <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)' }}>
          <CheckCircle size={24} />
        </div>
        <div className="stat-info">
          <h3>On Time</h3>
          <p>{summary.on_time}</p>
        </div>
      </div>
      <div className="stat-box">
        <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}>
          <AlertCircle size={24} />
        </div>
        <div className="stat-info">
          <h3>Delayed</h3>
          <p>{summary.delayed}</p>
        </div>
      </div>
      <div className="stat-box">
        <div className="stat-icon" style={{ backgroundColor: 'rgba(192, 132, 252, 0.1)', color: '#c084fc' }}>
          <TrendingUp size={24} />
        </div>
        <div className="stat-info">
          <h3>Total Events</h3>
          <p>{summary.total_events}</p>
        </div>
      </div>
    </div>
  );
}
