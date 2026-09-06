import { useState, useEffect, useMemo } from 'react';
import { ThermalEvent, Metadata } from '../types';

export function useThermalData() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [filteredEvents, setFilteredEvents] = useState<ThermalEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  
  const [typeFilter, setTypeFilter] = useState('All Types');
  const [riskFilter, setRiskFilter] = useState('All Risks');
  const [timeFilter, setTimeFilter] = useState('All Time');
  const [mapStyle, setMapStyle] = useState('green');
  const [showSpreadOverlay, setShowSpreadOverlay] = useState(true);

  // ── Data Loading ──────────────────────────────────────────────
  useEffect(() => {
    fetch('/firms_enhanced_data.json')
      .then(res => res.json())
      .then(data => {
        if (data.events && data.metadata) {
          setEvents(data.events);
          setMetadata(data.metadata);
          setFilteredEvents(data.events);
          if (data.events.length > 0) setSelectedEvent(data.events[0]);
        } else if (Array.isArray(data)) {
          setEvents(data);
          setFilteredEvents(data);
          if (data.length > 0) setSelectedEvent(data[0]);
        }
      })
      .catch(err => console.error("Error loading data", err));
  }, []);

  // ── Filtering ─────────────────────────────────────────────────
  useEffect(() => {
    let result = events;
    if (typeFilter !== 'All Types') result = result.filter(e => e.type === typeFilter);
    if (riskFilter !== 'All Risks') result = result.filter(e => e.risk_score === riskFilter);
    
    if (timeFilter === 'Last 24 Hours') result = result.filter(e => e.detection_age_days <= 1.0);
    if (timeFilter === 'Last 7 Days') result = result.filter(e => e.detection_age_days <= 7.0);
    if (timeFilter === 'Last 28 Days') result = result.filter(e => e.detection_age_days <= 28.0);
    
    setFilteredEvents(result);
  }, [typeFilter, riskFilter, timeFilter, events]);

  // ── Computed Stats ────────────────────────────────────────────
  const totalLives = useMemo(() => events.reduce((a, e) => a + (e.lives_impacted || 0), 0), [events]);
  const criticalCount = useMemo(() => events.filter(e => e.risk_score === 'CRITICAL').length, [events]);
  const spreadingCount = useMemo(() => events.filter(e => e.spread?.is_spreading).length, [events]);

  return {
    events,
    metadata,
    filteredEvents,
    selectedEvent,
    setSelectedEvent,
    typeFilter,
    setTypeFilter,
    riskFilter,
    setRiskFilter,
    timeFilter,
    setTimeFilter,
    mapStyle,
    setMapStyle,
    showSpreadOverlay,
    setShowSpreadOverlay,
    totalLives,
    criticalCount,
    spreadingCount,
  };
}
