import { useMemo, useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Popup, CircleMarker, useMap, Polygon, useMapEvents } from 'react-leaflet';
import { ThermalEvent } from '../../types';

// Controls smooth camera flyTo ONLY when user explicitly changes selected event or clicks overview
function MapViewController({
  selectedEvent,
  overviewTrigger,
  isSidebarOpen
}: {
  selectedEvent: ThermalEvent | null;
  overviewTrigger: number;
  isSidebarOpen?: boolean;
}) {
  const map = useMap();
  const lastFlownIdRef = useRef<string | null>(null);
  const isInitialMount = useRef(true);

  // Auto-resize Leaflet canvas whenever sidebar opens or closes
  useEffect(() => {
    map.invalidateSize();
    const t1 = setTimeout(() => map.invalidateSize(), 100);
    const t2 = setTimeout(() => map.invalidateSize(), 300);
    const t3 = setTimeout(() => map.invalidateSize(), 500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [isSidebarOpen, map]);

  // Window resize observer
  useEffect(() => {
    const handleResize = () => {
      map.invalidateSize();
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [map]);

  // Moderate comfortable zoom (zoom 7 instead of extreme zoom 9)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return; // Keep wide whole map view on initial load
    }
    if (selectedEvent && selectedEvent.id !== lastFlownIdRef.current) {
      lastFlownIdRef.current = selectedEvent.id;
      map.flyTo([selectedEvent.lat, selectedEvent.lng], 7, { duration: 1.0 });
    }
  }, [selectedEvent?.id, selectedEvent?.lat, selectedEvent?.lng, map]);

  // Fly to whole map overview when overview button is pressed
  useEffect(() => {
    if (overviewTrigger > 0) {
      lastFlownIdRef.current = null;
      map.flyTo([21.8, 79.0], 4.5, { duration: 1.0 });
    }
  }, [overviewTrigger, map]);

  return null;
}

// Map event listener for real-time cursor coordinate readout
function MapCoordinatesHUD({ onCoordsChange }: { onCoordsChange: (coords: { lat: number; lng: number; zoom: number }) => void }) {
  const map = useMapEvents({
    mousemove: (e) => {
      onCoordsChange({
        lat: e.latlng.lat,
        lng: e.latlng.lng,
        zoom: Math.round(map.getZoom() * 10) / 10
      });
    },
    zoomend: () => {
      onCoordsChange({
        lat: map.getCenter().lat,
        lng: map.getCenter().lng,
        zoom: Math.round(map.getZoom() * 10) / 10
      });
    }
  });
  return null;
}

interface IntelligenceMapProps {
  mapStyle: string;
  filteredEvents: ThermalEvent[];
  selectedEvent: ThermalEvent | null;
  setSelectedEvent: (evt: ThermalEvent) => void;
  showSpreadOverlay: boolean;
  onOpenReport?: (evt: ThermalEvent) => void;
  satelliteFilter?: string;
  setSatelliteFilter?: (val: string) => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function IntelligenceMap({
  mapStyle = 'green',
  filteredEvents,
  selectedEvent,
  setSelectedEvent,
  showSpreadOverlay,
  onOpenReport,
  satelliteFilter = 'ALL',
  setSatelliteFilter,
  isSidebarOpen,
  onToggleSidebar
}: IntelligenceMapProps) {
  const [mapCoords, setMapCoords] = useState<{ lat: number; lng: number; zoom: number }>({ lat: 21.8, lng: 79.0, zoom: 4.5 });
  const [searchQuery, setSearchQuery] = useState('');
  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);
  const [showFRPGlow, setShowFRPGlow] = useState(true);
  const [showWindVectors, setShowWindVectors] = useState(true);
  const [showFacilityBuffers, setShowFacilityBuffers] = useState(true);
  const [activePreset, setActivePreset] = useState<string>('ALL');
  const [overviewTrigger, setOverviewTrigger] = useState(0);

  const getIcon = (type: string) => {
    const icons: { [k: string]: string } = {
      'Wildfire': '🔥', 'Industrial Fire': '🏭', 'Gas Flare': '🛢️',
      'Agriculture Burning': '🌾', 'Mining Activity': '⛏️', 'Volcanic Anomaly': '🌋',
    };
    return icons[type] || '📍';
  };

  // Custom High-Contrast Anomaly Palette
  const getEventColor = (event: ThermalEvent) => {
    const typeColors: { [k: string]: string } = {
      'Wildfire': '#e63946',
      'Industrial Fire': '#f97316',
      'Gas Flare': '#27c016',
      'Agriculture Burning': '#b0c64d',
      'Mining Activity': '#2e1e18',
      'Volcanic Anomaly': '#ef4444'
    };
    return typeColors[event.type] || '#f97316';
  };

  // Precision GIS radius scaling (crisp, sleek, non-bloated)
  const getMarkerRadius = (event: ThermalEvent) => {
    const frp = event.frp || 1;
    if (frp > 40) return 5.5;
    if (frp > 15) return 4.5;
    return 3.8;
  };

  // Fire Spread Multi-horizon polygons
  const spreadPolygons = useMemo(() => {
    if (!showSpreadOverlay || !selectedEvent?.spread?.is_spreading) return [];
    const { lat, lng } = selectedEvent;
    const predictions = selectedEvent.spread.predictions;
    const polygons: { positions: [number, number][]; color: string; label: string; stroke: string }[] = [];

    const horizons = [
      { key: 't_plus_12h', color: 'rgba(239, 68, 68, 0.08)', stroke: '#ef4444' },
      { key: 't_plus_6h', color: 'rgba(249, 115, 22, 0.12)', stroke: '#f97316' },
      { key: 't_plus_3h', color: 'rgba(234, 179, 8, 0.16)', stroke: '#eab308' },
      { key: 't_plus_1h', color: 'rgba(239, 68, 68, 0.25)', stroke: '#ff2222' }
    ];

    horizons.forEach((h) => {
      const pred = predictions[h.key];
      if (!pred || pred.radius_km <= 0) return;
      const r = pred.radius_km;
      const points: [number, number][] = [];
      for (let angle = 0; angle < 360; angle += 15) {
        const rad = (angle * Math.PI) / 180;
        const dLat = (r * Math.cos(rad)) / 111.32;
        const dLng = (r * Math.sin(rad)) / (111.32 * Math.cos((lat * Math.PI) / 180));
        points.push([lat + dLat, lng + dLng]);
      }
      points.push(points[0]);
      polygons.push({ positions: points, color: h.color, label: h.key.replace('t_plus_', 'T+'), stroke: h.stroke });
    });
    return polygons;
  }, [selectedEvent, showSpreadOverlay]);

  // Quick jump presets
  const handleQuickJump = (type: 'max_frp' | 'critical' | 'overview') => {
    if (type === 'max_frp') {
      const topFRP = [...filteredEvents].sort((a, b) => (b.frp || 0) - (a.frp || 0))[0];
      if (topFRP) {
        setSelectedEvent(topFRP);
        setActivePreset('MAX_FRP');
      }
    } else if (type === 'critical') {
      const critical = filteredEvents.find(e => e.risk_score === 'CRITICAL' && e.spread?.is_spreading) ||
                       filteredEvents.find(e => e.risk_score === 'CRITICAL');
      if (critical) {
        setSelectedEvent(critical);
        setActivePreset('CRITICAL');
      }
    } else if (type === 'overview') {
      setActivePreset('OVERVIEW');
      setOverviewTrigger(prev => prev + 1);
    }
  };

  // Search anomaly by ID or type
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const query = searchQuery.trim().toLowerCase();
    const match = filteredEvents.find(
      e => e.id.toLowerCase().includes(query) ||
           e.type.toLowerCase().includes(query) ||
           e.risk_score.toLowerCase() === query
    );
    if (match) {
      setSelectedEvent(match);
    }
  };

  return (
    <div className="map-wrapper">
      {/* ═══ NASA FIRMS FLOATING COMMAND HUD ═══ */}
      <div className="firms-floating-toolbar">
        {onToggleSidebar && (
          <button
            type="button"
            className={`preset-btn ${isSidebarOpen ? 'active' : ''}`}
            onClick={onToggleSidebar}
            title={isSidebarOpen ? "Collapse Left Features Panel" : "Open Left Features Panel"}
          >
            <span>{isSidebarOpen ? "◂ Features" : "▸ Features"}</span>
          </button>
        )}

        {/* Search Anomaly Quick Jump */}
        <form className="firms-search-box" onSubmit={handleSearchSubmit}>
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Jump to ID or classification..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button type="button" className="search-clear-btn" onClick={() => setSearchQuery('')}>✕</button>
          )}
        </form>

        {/* Satellite Sensor Constellation Badges */}
        <div className="firms-sensor-group">
          {['ALL', 'VIIRS 375m', 'MODIS 1km', 'LANDSAT 30m'].map((sensor) => (
            <button
              key={sensor}
              className={`sensor-tag ${satelliteFilter === sensor ? 'active' : ''}`}
              onClick={() => setSatelliteFilter && setSatelliteFilter(sensor)}
            >
              {sensor}
            </button>
          ))}
        </div>

        {/* Preset Quick Focus */}
        <div className="firms-preset-buttons">
          <button
            className={`preset-btn ${activePreset === 'OVERVIEW' ? 'active' : ''}`}
            onClick={() => handleQuickJump('overview')}
            title="Wide whole country map overview"
          >
            🌍 Whole Map
          </button>
          <button
            className={`preset-btn ${activePreset === 'MAX_FRP' ? 'active' : ''}`}
            onClick={() => handleQuickJump('max_frp')}
            title="Focus on hotspot with maximum Fire Radiative Power (MW)"
          >
            🔥 Top FRP
          </button>
          <button
            className={`preset-btn ${activePreset === 'CRITICAL' ? 'active' : ''}`}
            onClick={() => handleQuickJump('critical')}
            title="Focus on critical active spreading fire"
          >
            🚨 Critical Fire
          </button>
        </div>

        {/* Layer Visibility Toggle Menu */}
        <div className="firms-layer-toggle-wrapper">
          <button
            className={`firms-hud-btn ${isLayerMenuOpen ? 'active' : ''}`}
            onClick={() => setIsLayerMenuOpen(!isLayerMenuOpen)}
            title="Configure Map Overlays"
          >
            <span>🗺️ Layers</span>
            <span className="caret">▾</span>
          </button>

          {isLayerMenuOpen && (
            <div className="firms-layer-dropdown">
              <div className="layer-dropdown-header">NASA FIRMS Overlays</div>
              <label className="layer-check-row">
                <input
                  type="checkbox"
                  checked={showFRPGlow}
                  onChange={(e) => setShowFRPGlow(e.target.checked)}
                />
                <span>Thermal Energy Halos</span>
              </label>
              <label className="layer-check-row">
                <input
                  type="checkbox"
                  checked={showWindVectors}
                  onChange={(e) => setShowWindVectors(e.target.checked)}
                />
                <span>Wind Vector Direction Barbs</span>
              </label>
              <label className="layer-check-row">
                <input
                  type="checkbox"
                  checked={showFacilityBuffers}
                  onChange={(e) => setShowFacilityBuffers(e.target.checked)}
                />
                <span>Hazard Buffer (2.5 km)</span>
              </label>
            </div>
          )}
        </div>
      </div>

      <MapContainer
        center={[21.8, 79.0]}
        zoom={4.5}
        minZoom={3}
        maxZoom={18}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <MapCoordinatesHUD onCoordsChange={setMapCoords} />
        <MapViewController
          selectedEvent={selectedEvent}
          overviewTrigger={overviewTrigger}
          isSidebarOpen={isSidebarOpen}
        />

        {/* Basemap Tile Layers - Default is Topographic Relief */}
        {mapStyle === 'green' && (
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri World Topo</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
          />
        )}
        {mapStyle === 'dark' && (
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri Canvas Dark</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          />
        )}
        {mapStyle === 'osm' && (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}
        {mapStyle === 'satellite' && (
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri World Imagery</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
        )}

        {/* Fire Spread Polygons */}
        {spreadPolygons.map((poly, i) => (
          <Polygon
            key={`spread-${i}`}
            positions={poly.positions}
            pathOptions={{
              color: poly.stroke,
              fillColor: poly.color,
              fillOpacity: 0.65,
              weight: 1.5,
              dashArray: '4 4',
            }}
          />
        ))}

        {/* Hazard & Toxic Radius Exclusion Zone Buffer */}
        {showFacilityBuffers && selectedEvent && (
          <CircleMarker
            center={[selectedEvent.lat, selectedEvent.lng]}
            radius={24}
            pathOptions={{
              color: '#ef4444',
              fillColor: 'rgba(239, 68, 68, 0.08)',
              fillOpacity: 0.5,
              weight: 1.2,
              dashArray: '3 4'
            }}
          />
        )}

        {/* ═══ REFINED PRECISION NASA FIRMS HOTSPOT DOTS ═══ */}
        {filteredEvents.map(event => {
          const isSelected = event.id === selectedEvent?.id;
          const isCritical = event.risk_score === 'CRITICAL';
          const isSpreading = !!event.spread?.is_spreading;
          const dotColor = getEventColor(event);
          const baseRadius = getMarkerRadius(event);

          return (
            <div key={event.id}>
              {/* Layer 1: Selected Targeting Reticle & Radiant Halo */}
              {isSelected && (
                <>
                  <CircleMarker
                    center={[event.lat, event.lng]}
                    radius={16}
                    pathOptions={{
                      color: 'transparent',
                      fillColor: dotColor,
                      fillOpacity: 0.28,
                      weight: 0,
                    }}
                    interactive={false}
                  />
                  <CircleMarker
                    center={[event.lat, event.lng]}
                    radius={12}
                    pathOptions={{
                      color: '#ffffff',
                      fillColor: 'transparent',
                      fillOpacity: 0,
                      weight: 1.8,
                      dashArray: '3 3',
                    }}
                    interactive={false}
                  />
                </>
              )}

              {/* Layer 2: Tight alert indicator ring for spreading critical fires */}
              {!isSelected && isCritical && isSpreading && (
                <CircleMarker
                  center={[event.lat, event.lng]}
                  radius={baseRadius + 3.5}
                  pathOptions={{
                    color: '#ff2a44',
                    fillColor: 'transparent',
                    fillOpacity: 0,
                    weight: 1.2,
                    dashArray: '2 3',
                  }}
                  interactive={false}
                />
              )}

              {/* Layer 3: Subtle high-intensity thermal aura (for FRP > 30 MW) */}
              {!isSelected && showFRPGlow && (event.frp || 0) > 30 && (
                <CircleMarker
                  center={[event.lat, event.lng]}
                  radius={baseRadius + 3.0}
                  pathOptions={{
                    color: 'transparent',
                    fillColor: dotColor,
                    fillOpacity: 0.22,
                    weight: 0,
                  }}
                  interactive={false}
                />
              )}

              {/* Layer 4: Razor-Sharp Core Vector Pip */}
              <CircleMarker
                center={[event.lat, event.lng]}
                radius={isSelected ? 6.5 : baseRadius}
                pathOptions={{
                  color: isSelected ? '#ffffff' : '#080c14',
                  fillColor: dotColor,
                  fillOpacity: 0.98,
                  weight: isSelected ? 2.5 : 1.2,
                }}
                eventHandlers={{
                  click: () => {
                    setSelectedEvent(event);
                  }
                }}
              >
                <Popup className="firms-map-popup" autoPan={true}>
                  <div className="popup-card">
                    <div className="popup-header">
                      <span className="popup-icon">{getIcon(event.type)}</span>
                      <div className="popup-title-group">
                        <div className="popup-id-row">
                          <span className="popup-id">{event.id}</span>
                          <span className="sensor-tag-mini">VIIRS 375m</span>
                        </div>
                        <span className="popup-coords">{event.lat.toFixed(4)}°N, {event.lng.toFixed(4)}°E</span>
                      </div>
                      <span className={`popup-risk-badge risk-badge-${event.risk_score?.toLowerCase()}`}>
                        {event.risk_score}
                      </span>
                    </div>

                    <div className="popup-grid">
                      <div className="popup-field">
                        <span className="popup-label">Classification</span>
                        <span className="popup-val" style={{ color: dotColor }}>{event.type}</span>
                      </div>
                      <div className="popup-field">
                        <span className="popup-label">AI Confidence</span>
                        <span className="popup-val highlight-val">{event.confidence}%</span>
                      </div>
                      <div className="popup-field">
                        <span className="popup-label">Persistence</span>
                        <span className="popup-val">{event.persistence_days}d ({event.detection_age_days <= 1 ? '<24h' : `${event.detection_age_days}d`})</span>
                      </div>
                      <div className="popup-field">
                        <span className="popup-label">Radiative Power</span>
                        <span className="popup-val frp-val">{event.frp} MW</span>
                      </div>
                    </div>

                    {event.spread?.is_spreading && (
                      <div className="popup-spread-mini">
                        <span>💨 Wind: {event.spread.wind_speed_kmh} km/h ({event.spread.wind_direction_deg}°)</span>
                        <span>📈 Spread: {event.spread.spread_rate_kmh} km/h</span>
                      </div>
                    )}

                    <button
                      className="popup-action-btn"
                      onClick={() => {
                        setSelectedEvent(event);
                        if (onOpenReport) {
                          onOpenReport(event);
                        }
                      }}
                    >
                      <span>View full report</span>
                      <span className="btn-arrow">→</span>
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            </div>
          );
        })}
      </MapContainer>

      {/* ═══ LIVE MISSION SPREAD TELEMETRY OVERLAY ═══ */}
      {selectedEvent?.spread?.is_spreading && showSpreadOverlay && (
        <div className="map-overlay-badge">
          <span className="badge-pulse">🔥</span>
          <div className="overlay-text-block">
            <span className="overlay-title">ACTIVE SPREAD MODELING: <strong>{selectedEvent.id}</strong> ({selectedEvent.type})</span>
            <div className="overlay-telemetry-row">
              <span>💨 Wind: <strong>{selectedEvent.spread.wind_speed_kmh} km/h</strong> at <strong>{selectedEvent.spread.wind_direction_deg}°</strong></span>
              <span>📈 Rate: <strong>{selectedEvent.spread.spread_rate_kmh} km/h</strong></span>
              <span>🌿 Fuel: <strong>{selectedEvent.spread.vegetation_type}</strong></span>
              <span>⚠️ Risk: <strong className={`spread-risk-${selectedEvent.spread.spread_risk?.toLowerCase()}`}>{selectedEvent.spread.spread_risk}</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* ═══ NASA FIRMS BOTTOM COORDINATES & STATUS BAR ═══ */}
      <div className="map-bottom-status-bar">
        <div className="status-item">
          <span className="status-k">CURSOR:</span>
          <span className="status-v">{mapCoords.lat.toFixed(4)}°N, {mapCoords.lng.toFixed(4)}°E</span>
        </div>
        <div className="status-item">
          <span className="status-k">ZOOM:</span>
          <span className="status-v">L{mapCoords.zoom}</span>
        </div>
        <div className="status-item">
          <span className="status-k">HOTSPOTS DISPLAYED:</span>
          <span className="status-v highlight-val">{filteredEvents.length}</span>
        </div>
        <div className="status-item hide-mobile">
          <span className="status-k">BASEMAP:</span>
          <span className="status-v">{mapStyle.toUpperCase()} (TOPO RELIEF)</span>
        </div>
        <div className="status-item hide-mobile">
          <span className="status-k">PROJECTION:</span>
          <span className="status-v">EPSG:4326 (WGS84)</span>
        </div>
      </div>
    </div>
  );
}
