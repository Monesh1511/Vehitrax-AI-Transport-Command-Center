import React from 'react';
import { Bus, Clock } from 'lucide-react';
import { PunctualityBadge } from './PunctualityBadge';

export function BusCard({ bus }) {
  const lastSeen = new Date(bus.last_seen).toLocaleTimeString();
  
  return (
    <div className="card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Bus size={24} color="var(--primary)" />
          <h3 className="card-title">{bus.plate_number}</h3>
        </div>
        <PunctualityBadge status={bus.current_status} />
      </div>
      
      {bus.bus_name && bus.bus_name !== 'UNKNOWN' && (
        <div style={{ padding: '0.75rem 0', fontSize: '0.9rem' }}>
          <strong>{bus.bus_name}</strong> - <em>{bus.route}</em><br/>
          <span style={{ color: 'var(--text-muted)' }}>Driver: {bus.driver_name}</span>
        </div>
      )}

      <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
        <Clock size={16} />
        <span>Last seen: {lastSeen}</span>
      </div>
    </div>
  );
}
