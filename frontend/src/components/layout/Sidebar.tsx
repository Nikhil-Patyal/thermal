import { useState, useMemo } from 'react';
import { ThermalEvent } from '../../types';

interface SidebarProps {
  typeFilter: string;
  setTypeFilter: (val: string) => void;
  riskFilter: string;
  setRiskFilter: (val: string) => void;
  timeFilter: string;
  setTimeFilter: (val: string) => void;
  mapStyle: string;
  setMapStyle: (val: string) => void;
  showSpreadOverlay: boolean;
  setShowSpreadOverlay: (val: boolean) => void;
  filteredEvents: ThermalEvent[];
  events: ThermalEvent[];
  selectedEvent: ThermalEvent | null;
  setSelectedEvent: (evt: ThermalEvent) => void;
  onOpenDrawer?: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export function Sidebar({
  typeFilter, setTypeFilter,
  riskFilter, setRiskFilter,
  timeFilter, setTimeFilter,
  mapStyle, setMapStyle,
  showSpreadOverlay, setShowSpreadOverlay,
  filteredEvents, events,
  selectedEvent, setSelectedEvent,
  onOpenDrawer,
  isOpen,
  onToggle
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'risk' | 'frp' | 'recent' | 'lives'>('risk');

  const getIcon = (type: string) => {
    const icons: { [k: string]: string } = {
      'Wildfire': '🔥', 'Industrial Fire': '🏭', 'Gas Flare': '🛢️',
      'Agriculture Burning': '🌾', 'Mining Activity': '⛏️', 'Volcanic Anomaly': '🌋',
    };
    return icons[type] || '📍';
  };

  const getTypeColor = (type: string) => {
    const colors: { [k: string]: string } = {
      'Wildfire': '#e63946',
      'Industrial Fire': '#f97316',
      'Gas Flare': '#27c016ff',
      'Agriculture Burning': '#b0c64dff',
      'Mining Activity': '#2e1e18ff',
      'Volcanic Anomaly': '#ef4444'
    };
    return colors[type] || '#f97316';
  };

  const getRiskColor = (risk: string) => {
    const colors: { [k: string]: string } = {
      'CRITICAL': '#ef4444', 'HIGH': '#f97316', 'MODERATE': '#fb923c', 'LOW': '#10b981',
    };
    return colors[risk] || '#94a3b8';
  };

  const anomalyTypes = [
    { type: 'Wildfire', color: '#e63946' },
    { type: 'Industrial Fire', color: '#f97316' },
    { type: 'Gas Flare', color: '#27c016' },
    { type: 'Agriculture Burning', color: '#b0c64d' },
    { type: 'Mining Activity', color: '#2e1e18' },
    { type: 'Volcanic Anomaly', color: '#ef4444' },
  ];

  const riskLevels = ['CRITICAL', 'HIGH', 'MODERATE', 'LOW'];

  // Search & Sort filtered list
  const displayEvents = useMemo(() => {
    let list = filteredEvents;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(e =>
        e.id.toLowerCase().includes(q) ||
        e.type.toLowerCase().includes(q) ||
        e.risk_score.toLowerCase().includes(q) ||
        e.impact?.zone_type?.toLowerCase().includes(q)
      );
    }

    return [...list].sort((a, b) => {
      if (sortBy === 'risk') return (b.composite_risk || 0) - (a.composite_risk || 0);
      if (sortBy === 'frp') return (b.frp || 0) - (a.frp || 0);
      if (sortBy === 'recent') return (a.detection_age_days || 0) - (b.detection_age_days || 0);
      if (sortBy === 'lives') return (b.lives_impacted || 0) - (a.lives_impacted || 0);
      return 0;
    });
  }, [filteredEvents, searchQuery, sortBy]);

  const handleEventClick = (evt: ThermalEvent) => {
    setSelectedEvent(evt);
    if (onOpenDrawer) {
      onOpenDrawer();
    }
  };

  return (
    <>
      {/* Floating Toggle Tab when Sidebar is collapsed */}
      {!isOpen && (
        <button
          className="sidebar-floating-toggle"
          onClick={onToggle}
          title="Open Features & Filters Panel"
        >
          <span className="toggle-icon">▸</span>
          <span className="toggle-label">Filters & Features</span>
          <span className="toggle-badge">{filteredEvents.length}</span>
        </button>
      )}

      <aside className={`left-panel ${!isOpen ? 'collapsed' : ''}`}>
        {/* Top Header with Collapse Button */}
        <div className="panel-header-bar">
          <div className="panel-title-group">
            <span className="panel-indicator-dot"></span>
            <h3>Mission Controls</h3>
          </div>
          <button
            className="sidebar-collapse-btn"
            onClick={onToggle}
            title="Hide Features Sidebar"
          >
            <span>◂ Hide Panel</span>
          </button>
        </div>

        {/* ═══ SATELLITE ORBIT OVERPASS TICKER ═══ */}
        <div className="satellite-orbit-strip">
          <div className="orbit-title">
            <span className="orbit-pulse-dot"></span>
            <span>FIRMS ORBITAL PASS</span>
          </div>
          <div className="orbit-ticker-text">
            <span>NOAA-20 VIIRS: +14m</span>
            <span className="dot-sep">•</span>
            <span>TERRA MODIS: +42m</span>
          </div>
        </div>

        {/* Primary Filters */}
        <div className="filter-group">
          <label>Anomaly Classification</label>
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option>All Types</option>
            <option>Wildfire</option>
            <option>Industrial Fire</option>
            <option>Gas Flare</option>
            <option>Agriculture Burning</option>
            <option>Mining Activity</option>
          </select>
        </div>

        <div className="filter-grid-2col">
          <div className="filter-group">
            <label>Composite Risk</label>
            <select value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
              <option>All Risks</option>
              <option>CRITICAL</option>
              <option>HIGH</option>
              <option>MODERATE</option>
              <option>LOW</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Temporal Range</label>
            <select value={timeFilter} onChange={e => setTimeFilter(e.target.value)}>
              <option>All Time</option>
              <option>Last 24 Hours</option>
              <option>Last 7 Days</option>
              <option>Last 28 Days</option>
            </select>
          </div>
        </div>

        <div className="filter-grid-2col">
          <div className="filter-group">
            <label>Basemap Style</label>
            <select value={mapStyle} onChange={e => setMapStyle(e.target.value)}>
              <option value="dark">Dark Canvas (Esri)</option>
              <option value="osm">Standard Navigation</option>
              <option value="green">Topographic Relief</option>
              <option value="satellite">Satellite Imagery</option>
            </select>
          </div>

          <div className="filter-group toggle-group-align">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={showSpreadOverlay}
                onChange={e => setShowSpreadOverlay(e.target.checked)}
              />
              <span>Spread Buffers</span>
            </label>
          </div>
        </div>

        {/* Compact Color-Coded Legend with Density Bars */}
        <div className="compact-legend-section">
          <div className="legend-header">
            <span className="legend-title">Classification Legend & Density</span>
            <span className="legend-badge">{filteredEvents.length} Active</span>
          </div>
          <div className="legend-grid">
            {anomalyTypes.map(({ type, color }) => {
              const count = events.filter(e => e.type === type).length;
              const pct = events.length > 0 ? (count / events.length) * 100 : 0;
              return (
                <div
                  key={type}
                  className={`legend-item ${typeFilter === type ? 'legend-selected' : ''}`}
                  onClick={() => setTypeFilter(typeFilter === type ? 'All Types' : type)}
                  title={`Filter by ${type} (${count} events)`}
                >
                  <div className="legend-item-left">
                    <span className="legend-dot" style={{ backgroundColor: color }}></span>
                    <span className="legend-label">{type}</span>
                  </div>
                  <div className="legend-item-right">
                    <div className="legend-density-bar">
                      <div className="legend-density-fill" style={{ width: `${pct}%`, backgroundColor: color }}></div>
                    </div>
                    <span className="legend-count">{count}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="legend-divider"></div>

          <div className="risk-legend-row">
            {riskLevels.map(risk => {
              const count = events.filter(e => e.risk_score === risk).length;
              return (
                <div
                  key={risk}
                  className={`risk-legend-item ${riskFilter === risk ? 'legend-selected' : ''}`}
                  onClick={() => setRiskFilter(riskFilter === risk ? 'All Risks' : risk)}
                  title={`Filter by ${risk} risk (${count})`}
                >
                  <span className="risk-legend-dot" style={{ backgroundColor: getRiskColor(risk) }}></span>
                  <span className="risk-legend-name">{risk.slice(0, 4)}</span>
                  <span className="risk-legend-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ═══ ACTIVE DETECTIONS LIST WITH SORT & SEARCH ═══ */}
        <div className="event-list-container">
          <div className="event-list-header">
            <span className="event-list-title">Active Detections ({displayEvents.length})</span>
            <div className="event-sort-control">
              <span className="sort-label">Sort:</span>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
                <option value="risk">Risk</option>
                <option value="frp">FRP</option>
                <option value="recent">Recent</option>
                <option value="lives">Impact</option>
              </select>
            </div>
          </div>

          {/* Mini Search Filter */}
          <div className="list-search-bar">
            <span className="search-icon-sm">🔍</span>
            <input
              type="text"
              placeholder="Filter list by ID or zone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="search-clear-sm" onClick={() => setSearchQuery('')}>✕</button>
            )}
          </div>

          <div className="event-list-scroll">
            {displayEvents.map(evt => (
              <div
                key={evt.id}
                className={`event-list-item ${selectedEvent?.id === evt.id ? 'active' : ''}`}
                onClick={() => handleEventClick(evt)}
              >
                <span className="evt-icon">{getIcon(evt.type)}</span>
                <div className="evt-info">
                  <div className="evt-row-top">
                    <span className="evt-id">{evt.id}</span>
                    <div className="evt-badges">
                      <span className="evt-frp-pill">{evt.frp} MW</span>
                      <span className={`evt-risk risk-badge-${evt.risk_score?.toLowerCase()}`}>
                        {evt.risk_score}
                      </span>
                    </div>
                  </div>
                  <div className="evt-row-bottom">
                    <span className="evt-type" style={{ color: getTypeColor(evt.type) }}>{evt.type}</span>
                    <span className="evt-conf">{evt.confidence}% conf • {evt.persistence_days}d</span>
                  </div>
                </div>
              </div>
            ))}
            {displayEvents.length === 0 && (
              <div className="event-list-empty">No anomalies match current filter</div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
