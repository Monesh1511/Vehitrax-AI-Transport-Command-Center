import React, { useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { BusUploadForm } from '../components/BusUploadForm';

const DASHBOARD_CACHE_KEY = 'vehitrax_dashboard_detections';
const DUPLICATE_WINDOW_MS = 20000;

const normalizePlate = (plate) => {
  if (!plate) return '';
  return String(plate).toUpperCase().replace(/[^A-Z0-9]/g, '');
};

export default function Dashboard() {
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const { data: wsData, isConnected } = useWebSocket(wsUrl);
  const [detections, setDetections] = useState(() => {
    try {
      const cached = sessionStorage.getItem(DASHBOARD_CACHE_KEY);
      const parsed = cached ? JSON.parse(cached) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  });
  const [now, setNow] = useState(new Date());
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [showDatabaseCheck, setShowDatabaseCheck] = useState(false);
  const [busesInDb, setBusesInDb] = useState(null);
  const [searchPlate, setSearchPlate] = useState('');
  const [searchRegistered, setSearchRegistered] = useState('');

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const getTimingStatus = useCallback((timestamp) => {
    const dt = new Date(timestamp);
    const minutes = dt.getHours() * 60 + dt.getMinutes();
    const start = 9 * 60;
    const end = 16 * 60 + 10;

    if (minutes <= start) {
      const earlyMinutes = start - minutes;
      return {
        status: 'Enter',
        score: Math.min(100, 95 + Math.floor(earlyMinutes / 10)),
      };
    }

    if (minutes > end) {
      return { status: 'Exit', score: 100 };
    }

    const lateMinutes = minutes - start;
    return { status: 'Delayed', score: Math.max(0, 95 - lateMinutes) };
  }, []);

  const getTimeKeepUp = (timestamp) => {
    const dt = new Date(timestamp);
    const minutes = dt.getHours() * 60 + dt.getMinutes();
    const start = 9 * 60;
    const diff = start - minutes;
    if (diff <= 0) {
      return 'On time';
    }

    const hours = Math.floor(diff / 60);
    const mins = diff % 60;
    const hoursLabel = hours > 0 ? `${hours} hr${hours > 1 ? 's' : ''} ` : '';
    const minsLabel = mins > 0 ? `${mins} min` : '0 min';
    return `Arrived before ${hoursLabel}${minsLabel}`;
  };

  useEffect(() => {
    try {
      sessionStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(detections));
    } catch (err) {
      console.warn('Failed to cache dashboard detections:', err);
    }
  }, [detections]);

  const hydrateDetection = useCallback(async (eventPayload) => {
    try {
      const eventData = eventPayload?.data;
      if (!eventData) {
        console.warn('[hydrateDetection] No eventData in payload');
        return null;
      }

      let bus = null;
      if (eventData.bus_id) {
        const busRes = await fetch(`${apiUrl}/api/buses/${eventData.bus_id}`);
        if (busRes.ok) {
          bus = await busRes.json();
        } else {
          console.warn(`[hydrateDetection] Bus fetch failed with status ${busRes.status} for bus_id ${eventData.bus_id}`);
        }
      } else {
        console.warn('[hydrateDetection] No bus_id in event:', eventData);
      }

      return {
        id: eventData.id,
        timestamp: eventData.timestamp,
        confidence: eventData.confidence,
        plate_number: bus?.plate_number || normalizePlate(eventData.detected_plate) || 'UNKNOWN',
        detected_plate: normalizePlate(eventData.detected_plate),
        bus_number: bus?.bus_name || 'UNKNOWN',
        driver_name: bus?.driver_name || 'UNKNOWN',
        ...getTimingStatus(eventData.timestamp),
      };
    } catch (err) {
      console.error('Error enriching detection event:', err);
      return null;
    }
  }, [apiUrl, getTimingStatus]);

  const clearDashboard = () => {
    setDetections([]);
    sessionStorage.removeItem(DASHBOARD_CACHE_KEY);
  };

  const checkDatabase = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/buses/`);
      if (res.ok) {
        const buses = await res.json();
        setBusesInDb(buses);
        setShowDatabaseCheck(true);
      } else {
        setBusesInDb([]);
      }
    } catch (err) {
      console.error('Error fetching buses:', err);
      setBusesInDb([]);
    }
  };

  useEffect(() => {
    if (wsData && (wsData.type === 'DETECTION' || !wsData.type)) {
      hydrateDetection(wsData).then((nextDetection) => {
        if (!nextDetection) return;
        
        setDetections((current) => {
          const nextPlateKey = normalizePlate(nextDetection.plate_number || nextDetection.detected_plate);
          // Avoid duplicate detections of the same plate within cooldown window
          const isDuplicate = current.some(
            (entry) =>
              normalizePlate(entry.plate_number || entry.detected_plate) === nextPlateKey &&
              Math.abs(new Date(entry.timestamp).getTime() - new Date(nextDetection.timestamp).getTime()) <= DUPLICATE_WINDOW_MS
          );
          
          if (isDuplicate) {
            console.log(`[Dashboard] Skipping duplicate detection of plate: ${nextDetection.plate_number}`);
            return current;
          }
          
          return [nextDetection, ...current].slice(0, 50);
        });
      });
    }
  }, [wsData, hydrateDetection]);

  const normalizedSearch = String(searchPlate || '').toUpperCase();
  const filteredDetections = normalizedSearch
    ? detections.filter((entry) => {
        const plate = normalizePlate(entry.plate_number || entry.detected_plate);
        const driver = String(entry.driver_name || '').toUpperCase();
        const bus = String(entry.bus_number || '').toUpperCase();
        return (
          plate.includes(normalizedSearch) ||
          driver.includes(normalizedSearch) ||
          bus.includes(normalizedSearch)
        );
      })
    : detections;

  const normalizedRegisteredSearch = normalizePlate(searchRegistered);
  const filteredBusesInDb = busesInDb
    ? busesInDb.filter((bus) => {
        const plate = normalizePlate(bus.plate_number);
        const busName = String(bus.bus_name || '').toUpperCase();
        const driverName = String(bus.driver_name || '').toUpperCase();
        return (
          !normalizedRegisteredSearch ||
          plate.includes(normalizedRegisteredSearch) ||
          busName.includes(normalizedRegisteredSearch) ||
          driverName.includes(normalizedRegisteredSearch)
        );
      })
    : [];

  const uniquePlatesCount = new Set(
    detections.map((entry) => normalizePlate(entry.plate_number || entry.detected_plate))
  ).size;
  const delayedCount = detections.filter((entry) => entry.status === 'Delayed').length;
  const unknownCount = detections.filter((entry) => entry.bus_number === 'UNKNOWN').length;

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="eyebrow">Sri Sairam Engineering College</p>
          <h2 className="page-title">Live Transport Dashboard</h2>
          <p className="page-subtitle">
            {now.toLocaleDateString()} - {now.toLocaleTimeString()} - {now.toLocaleDateString(undefined, { weekday: 'long' })}
          </p>
        </div>
        <div className="header-actions">
          <button type="button" className="btn btn-primary" onClick={() => setShowUploadForm(true)}>
            Upload New
          </button>
          <button type="button" className="btn btn-outline" onClick={checkDatabase}>
            Registered Buses ✅
          </button>
          <button type="button" className="btn btn-ghost" onClick={clearDashboard}>
            Clear Dashboard
          </button>
          <div className={`status-pill ${isConnected ? '' : 'down'}`}>
            <span className="status-dot" />
            {isConnected ? 'Live Monitoring' : 'Disconnected'}
          </div>
        </div>
      </div>

      <div className="kpi-toolbar">
        <div className="kpi-grid">
          <div className="kpi-card">
            <p className="kpi-label">Live Detections</p>
            <p className="kpi-value">{detections.length}</p>
          </div>
          <div className="kpi-card">
            <p className="kpi-label">Unique Plates</p>
            <p className="kpi-value">{uniquePlatesCount}</p>
          </div>
          <div className="kpi-card">
            <p className="kpi-label">Delayed</p>
            <p className="kpi-value">{delayedCount}</p>
          </div>
          <div className="kpi-card">
            <p className="kpi-label">Needs Registration</p>
            <p className="kpi-value">{unknownCount}</p>
          </div>
        </div>
        <div className="search-stack">
          <label className="search-label">Quick Search</label>
          <input
            type="text"
            value={searchPlate}
            onChange={(e) => setSearchPlate(e.target.value)}
            placeholder="Search plate, bus, or driver"
            className="search-input"
          />
        </div>
      </div>

      <div className="info-strip">
        <div className="info-card">
          <p className="info-title">College Timing</p>
          <p className="info-value">09:00 AM - 04:10 PM</p>
        </div>
        <div className="info-card">
          <p className="info-title">Operational Focus</p>
          <p className="info-value">Morning arrivals and evening departures</p>
        </div>
        <div className="info-card">
          <p className="info-title">Current Session</p>
          <p className="info-value">Transport coordination - Chennai campus</p>
        </div>
      </div>

      <div className="dashboard-grid">
        {filteredDetections.map((entry) => (
          <div className="card" key={entry.id}>
            <div className="card-header">
              <h3 className="card-title">{entry.plate_number}</h3>
              <span className={`badge ${entry.status === 'Delayed' ? 'danger' : entry.status === 'Exit' ? 'warning' : 'success'}`}>
                {entry.status}
              </span>
            </div>
            <div style={{ lineHeight: '1.8', fontSize: '0.9rem' }}>
              {entry.bus_number === 'UNKNOWN' ? (
                <>
                  <div className="tag">Unknown bus detected</div>
                  <div><strong>Number Plate:</strong> {entry.plate_number}</div>
                  <div><strong>Timing:</strong> {new Date(entry.timestamp).toLocaleTimeString()}</div>
                  <div><strong>Date:</strong> {new Date(entry.timestamp).toLocaleDateString()}</div>
                  <div><strong>Status:</strong> {entry.status}</div>
                </>
              ) : (
                <>
                  <div><strong>Bus Number:</strong> {entry.bus_number}</div>
                  <div><strong>Driver:</strong> {entry.driver_name}</div>
                  <div><strong>Timing:</strong> {new Date(entry.timestamp).toLocaleString()}</div>
                  {entry.status === 'Enter' && (
                    <div><strong>Time KeepUp:</strong> {getTimeKeepUp(entry.timestamp)}</div>
                  )}
                </>
              )}
              {entry.bus_number === 'UNKNOWN' && (
                <div className="card-alert">
                  New bus detected. Use Upload New to add this bus.
                </div>
              )}
            </div>
          </div>
        ))}
        {filteredDetections.length === 0 && (
          <p className="empty-state">No matching detections. Try another number plate.</p>
        )}
      </div>

      {showUploadForm && (
        <BusUploadForm
          apiUrl={apiUrl}
          onSuccess={() => {
            setShowUploadForm(false);
          }}
          onClose={() => setShowUploadForm(false)}
        />
      )}

      {showDatabaseCheck && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h3 className="modal-title">Buses in Database</h3>
              <button className="modal-close" onClick={() => setShowDatabaseCheck(false)}>
                ✕
              </button>
            </div>
            {busesInDb && busesInDb.length > 0 ? (
              <div>
                <div className="modal-toolbar">
                  <div>
                    <p className="page-subtitle">Total buses: <strong>{busesInDb.length}</strong></p>
                  </div>
                  <input
                    type="text"
                    value={searchRegistered}
                    onChange={(e) => setSearchRegistered(e.target.value)}
                    placeholder="Search registered buses"
                    className="search-input"
                  />
                </div>
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                  {filteredBusesInDb.map((bus) => (
                    <div key={bus.id} className="info-card">
                      <div><strong>Plate:</strong> {bus.plate_number}</div>
                      <div><strong>Bus:</strong> {bus.bus_name || '-'}</div>
                      <div><strong>Driver:</strong> {bus.driver_name || '-'}</div>
                    </div>
                  ))}
                  {filteredBusesInDb.length === 0 && (
                    <div className="empty-state">No registered buses match that search.</div>
                  )}
                </div>
              </div>
            ) : (
              <p className="page-subtitle">No buses found in database. Upload a bus first.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
