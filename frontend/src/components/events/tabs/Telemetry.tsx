import { ThermalEvent, Metadata } from '../../../types';

interface TelemetryProps {
  event: ThermalEvent;
  metadata?: Metadata | null;
}

export function Telemetry({ event, metadata }: TelemetryProps) {
  return (
    <div className="tab-content">
      {/* Sensor Telemetry */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>🛰️ Multi-Source Satellite Telemetry</h4>
          <span className="card-badge-accent">VIIRS 375M I-BAND</span>
        </div>
        <div className="telemetry-grid">
          <div className="telemetry-box">
            <span className="telemetry-k">Fire Radiative Power</span>
            <strong className="telemetry-v frp-val">{event.frp} MW</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Anomaly Persistence</span>
            <strong className="telemetry-v">{event.persistence_days} Days</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Detection Recency</span>
            <strong className="telemetry-v">{event.detection_age_days <= 1.0 ? 'Active (<24h)' : `${event.detection_age_days}d ago`}</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Distance to Forest</span>
            <strong className="telemetry-v">{event.dist_to_forest} km</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Distance to Industrial Area</span>
            <strong className="telemetry-v">{event.dist_to_industry} km</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Distance to Cropland</span>
            <strong className="telemetry-v">{event.dist_to_cropland} km</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Plume Toxic Buffer</span>
            <strong className="telemetry-v">{event.toxic_radius_km} km</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Population in Perimeter</span>
            <strong className="telemetry-v highlight-val">{event.lives_impacted?.toLocaleString() || 'N/A'}</strong>
          </div>
        </div>
      </div>

      {/* Geospatial Coordinates */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>📍 Precise Geospatial Positioning</h4>
          <span className="card-badge-muted">WGS84 EPSG:4326</span>
        </div>
        <div className="telemetry-grid">
          <div className="telemetry-box">
            <span className="telemetry-k">Latitude Coordinate</span>
            <strong className="telemetry-v font-mono">{event.lat.toFixed(5)}°N</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Longitude Coordinate</span>
            <strong className="telemetry-v font-mono">{event.lng.toFixed(5)}°E</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Geographic Classification</span>
            <strong className="telemetry-v uppercase">{event.impact?.zone_type || 'Unclassified'}</strong>
          </div>
          <div className="telemetry-box">
            <span className="telemetry-k">Calculated Impact Area</span>
            <strong className="telemetry-v">{event.impact?.danger_area_sq_km || 0} km²</strong>
          </div>
        </div>
      </div>

      {/* Composite Risk Factor Breakdown */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>📊 Multi-Factor Risk Index Scoring</h4>
          <span className="card-badge-accent">{event.composite_risk}/100</span>
        </div>
        <div className="risk-breakdown-list">
          {event.impact?.risk_breakdown && Object.entries(event.impact.risk_breakdown).map(([factor, score]) => (
            <div className="risk-factor-row" key={factor}>
              <span className="risk-factor-name">{factor.replace(/_/g, ' ')}</span>
              <div className="risk-factor-bar">
                <div
                  className="risk-factor-fill"
                  style={{
                    width: `${Math.min(100, (score / 30) * 100)}%`,
                    backgroundColor: score > 20 ? '#f87171' : score > 10 ? '#fb923c' : '#4ade80'
                  }}
                ></div>
              </div>
              <span className="risk-factor-score font-mono">{score}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Multi-Method Pipeline Benchmarks */}
      {metadata?.method_performance && (
        <div className="section-card">
          <div className="section-card-header">
            <h4>🤖 AI Ensemble System Benchmark Accuracies</h4>
            <span className="card-badge-muted">VALIDATION</span>
          </div>
          <div className="method-benchmark-grid">
            {Object.entries(metadata.method_performance).map(([name, score]) => (
              <div className="benchmark-card" key={name}>
                <div className="benchmark-header">
                  <span className="benchmark-name">{name}</span>
                  <span className="benchmark-score font-mono">{score}%</span>
                </div>
                <div className="benchmark-bar">
                  <div
                    className="benchmark-fill"
                    style={{
                      width: `${score}%`,
                      backgroundColor: score > 90 ? '#4ade80' : score > 75 ? '#38bdf8' : '#fb923c'
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
