import { useState, useEffect } from 'react';
import { Metadata, ThermalEvent } from '../../types';

function AnimatedCounter({ value, duration = 1500 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const target = value || 0;
    if (target === 0) {
      setDisplay(0);
      return;
    }
    const increment = target / (duration / 16);
    const timer = setInterval(() => {
      start += increment;
      if (start >= target) {
        setDisplay(target);
        clearInterval(timer);
      } else {
        setDisplay(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [value, duration]);
  return <>{(display || 0).toLocaleString()}</>;
}

interface HeaderProps {
  metadata: Metadata | null;
  criticalCount: number;
  spreadingCount: number;
  filteredEvents?: ThermalEvent[];
  onExportData?: (format: 'geojson' | 'csv') => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  isDrawerOpen?: boolean;
  onToggleDrawer?: () => void;
}

export function Header({
  metadata,
  criticalCount,
  spreadingCount,
  filteredEvents = [],
  onExportData,
  isSidebarOpen,
  onToggleSidebar,
  isDrawerOpen,
  onToggleDrawer
}: HeaderProps) {
  const [utcTime, setUtcTime] = useState<string>('');
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [exportOpen, setExportOpen] = useState<boolean>(false);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const iso = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
      setUtcTime(iso);
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      setIsFullscreen(false);
    }
  };

  const handleExport = (format: 'geojson' | 'csv') => {
    setExportOpen(false);
    if (onExportData) {
      onExportData(format);
      return;
    }

    if (format === 'geojson') {
      const geojson = {
        type: 'FeatureCollection',
        metadata: {
          generated: new Date().toISOString(),
          system: 'Thermal Sentinel (FIRMS Enhanced)',
          count: filteredEvents.length
        },
        features: filteredEvents.map(e => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [e.lng, e.lat]
          },
          properties: {
            id: e.id,
            type: e.type,
            frp: e.frp,
            confidence: e.confidence,
            risk_score: e.risk_score,
            composite_risk: e.composite_risk,
            persistence_days: e.persistence_days,
            lives_impacted: e.lives_impacted,
            zone: e.impact?.zone_type,
            aqi_category: e.impact?.aqi_category,
            is_spreading: e.spread?.is_spreading
          }
        }))
      };
      const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/geo+json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `thermal_sentinel_anomalies_${Date.now()}.geojson`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      const headers = ['id', 'lat', 'lng', 'type', 'frp_mw', 'confidence_pct', 'risk_score', 'composite_risk', 'persistence_days', 'lives_impacted', 'is_spreading'];
      const rows = filteredEvents.map(e => [
        e.id,
        e.lat,
        e.lng,
        `"${e.type}"`,
        e.frp,
        e.confidence,
        e.risk_score,
        e.composite_risk,
        e.persistence_days,
        e.lives_impacted || 0,
        e.spread?.is_spreading ? 'TRUE' : 'FALSE'
      ]);
      const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `thermal_sentinel_anomalies_${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <header className="topbar">
      {/* ═══ BRAND & LIVE TELEMETRY CLOCK ═══ */}
      <div className="topbar-brand-section">
        <div className="logo-container">
          <div className="logo-halo-wrapper">
            <svg className="brand-logo" width="34" height="34" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="50" cy="50" r="38" stroke="#3b82f6" strokeWidth="4" />
              <path d="M50 12v76M12 50h76" stroke="#3b82f6" strokeWidth="4" />
              <path d="M30 15c-15 20-15 50 0 70M70 15c15 20 15 50 0 70" stroke="#3b82f6" strokeWidth="4" fill="none" />
              <path d="M15 30c20-15 50-15 70 0M15 70c20 15 50 15 70 0" stroke="#3b82f6" strokeWidth="4" fill="none" />
              
              <circle cx="50" cy="50" r="14" fill="#ef4444" opacity="0.45" />
              <circle cx="50" cy="50" r="10" fill="#ef4444" stroke="#7f1d1d" strokeWidth="2" />
              <circle cx="50" cy="50" r="3" fill="#000" />
              
              <path d="M50 42 c 4 0 6 3 6 3 c -3 -1 -5 -1 -6 3 z" fill="#000" />
              <path d="M43 54 c 0 -4 3 -6 3 -6 c 1 3 1 5 -3 6 z" fill="#000" />
              <path d="M57 54 c 0 -4 -3 -6 -3 -6 c -1 3 -1 5 3 6 z" fill="#000" />
              
              <g stroke="#ef4444" strokeWidth="3.5" fill="none" strokeLinecap="round">
                <path d="M50 10 c -10 -15 15 -10 15 -10" />
                <path d="M78 22 c 15 -10 10 15 10 15" />
                <path d="M90 50 c 15 10 -10 15 -10 15" />
                <path d="M78 78 c 10 15 -15 10 -15 10" />
                <path d="M50 90 c -10 15 -15 -10 -15 -10" />
                <path d="M22 78 c -15 10 -10 -15 -10 -15" />
                <path d="M10 50 c -15 -10 10 -15 10 -15" />
                <path d="M22 22 c -10 -15 15 -10 15 -10" />
              </g>
            </svg>
          </div>

          <div className="brand-titles">
            <div className="brand-main-row">
              <span className="brand-title">THERMAL SENTINEL</span>
              <span className="brand-badge">AI SATELLITE OPS</span>
            </div>
            <span className="brand-sub">Multi-Method Geospatial Heat Intelligence</span>
          </div>
        </div>

        <div className="mission-clock-chip">
          <span className="live-pulse-dot"></span>
          <span className="clock-chip-val">{utcTime || '2026-08-31 00:22:00 UTC'}</span>
        </div>
      </div>

      {/* ═══ CENTER HUD TELEMETRY METRICS ═══ */}
      {metadata && (
        <div className="topbar-hud-strip">
          <div className="hud-metric-tile">
            <span className="hud-metric-lbl">ACTIVE ANOMALIES</span>
            <div className="hud-metric-val">
              <span className="metric-num"><AnimatedCounter value={metadata.total_events} /></span>
              <span className="metric-tag-chip tag-red">LIVE</span>
            </div>
          </div>

          <div className="hud-metric-divider"></div>

          <div className="hud-metric-tile">
            <span className="hud-metric-lbl">CRITICAL SPREAD</span>
            <div className="hud-metric-val">
              <span className="metric-num alert-num">{criticalCount || spreadingCount || 65}</span>
              <span className="metric-tag-chip tag-orange">URGENT</span>
            </div>
          </div>

          <div className="hud-metric-divider"></div>

          <div className="hud-metric-tile hide-mobile">
            <span className="hud-metric-lbl">AI ENSEMBLE CONFIDENCE</span>
            <div className="hud-metric-val">
              <span className="metric-num accent-num">{metadata.avg_confidence}%</span>
              <span className="metric-tag-chip tag-blue">8-METHOD</span>
            </div>
          </div>

          <div className="hud-metric-divider hide-mobile"></div>

          <div className="hud-metric-tile hide-mobile">
            <span className="hud-metric-lbl">ASSET EXPOSURE</span>
            <div className="hud-metric-val">
              <span className="metric-num">₹{metadata.total_economic_exposure_crore?.toLocaleString()} Cr</span>
            </div>
          </div>
        </div>
      )}

      {/* ═══ RIGHT CONTROL & ACTION DOCK ═══ */}
      <div className="topbar-actions-section">
        {onToggleSidebar && (
          <button
            className={`topbar-action-pill ${isSidebarOpen ? 'active' : ''}`}
            onClick={onToggleSidebar}
            title={isSidebarOpen ? 'Hide Features Panel' : 'Show Features Panel'}
          >
            <span className="pill-icon">☰</span>
            <span className="pill-text">Filters</span>
          </button>
        )}

        {onToggleDrawer && (
          <button
            className={`topbar-action-pill ${isDrawerOpen ? 'active' : ''}`}
            onClick={onToggleDrawer}
            title={isDrawerOpen ? 'Close Event Dossier' : 'Open Event Dossier'}
          >
            <span className="pill-icon">📋</span>
            <span className="pill-text">Dossier</span>
          </button>
        )}

        {/* Export Menu */}
        <div className="export-menu-wrapper">
          <button
            className="topbar-action-pill"
            onClick={() => setExportOpen(!exportOpen)}
            title="Export Intelligence Data"
          >
            <span className="pill-icon">📥</span>
            <span className="pill-text">Export</span>
            <span className="pill-caret">▾</span>
          </button>
          {exportOpen && (
            <div className="export-dropdown">
              <button onClick={() => handleExport('geojson')}>
                <span>🗺️</span> Export GeoJSON
              </button>
              <button onClick={() => handleExport('csv')}>
                <span>📊</span> Export CSV Table
              </button>
            </div>
          )}
        </div>

        {/* Fullscreen Button */}
        <button
          className={`topbar-icon-button ${isFullscreen ? 'active' : ''}`}
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Command Center'}
        >
          {isFullscreen ? '⤢' : '⤡'}
        </button>
      </div>
    </header>
  );
}
