import { ThermalEvent } from '../../../types';

export function AIAnalysis({ event }: { event: ThermalEvent }) {
  return (
    <div className="tab-content">
      {/* 8-Method Classification Section */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>🧠 8-Method Multi-AI Classification Pipeline</h4>
          <span className="card-badge-accent">ENSEMBLE</span>
        </div>
        <div className="method-scores-grid">
          {Object.entries(event.method_scores || {}).map(([method, score]) => (
            <div className="method-card-mini" key={method}>
              <div className="method-header-mini">
                <span className="method-name">{method}</span>
                <span className="method-score">{score}%</span>
              </div>
              <div className="method-bar">
                <div
                  className="method-fill"
                  style={{
                    width: `${score}%`,
                    backgroundColor: score > 80 ? '#4ade80' : score > 50 ? '#fbbf24' : '#f87171'
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Recommendation Box */}
      {event.advisory?.ai_recommendation && (
        <div className={`section-card ai-rec ai-rec-${event.advisory.ai_recommendation.urgency?.replace(/ /g, '_').toLowerCase()}`}>
          <div className="section-card-header">
            <h4>🎯 Tactical AI Recommendation</h4>
            <span className="rec-urgency-badge">{event.advisory.ai_recommendation.urgency}</span>
          </div>
          <p className="rec-text">{event.advisory.ai_recommendation.recommendation}</p>
          <div className="rec-footer">
            <span className="rec-icon">⚡</span>
            <span className="rec-note">{event.advisory.ai_recommendation.confidence_note}</span>
          </div>
        </div>
      )}

      {/* Spectral Band Analysis */}
      {event.spectral && (
        <div className="section-card">
          <div className="section-card-header">
            <h4>📊 Multispectral Band Radiometry</h4>
            <span className="card-badge-muted">SENSOR CHANNELS</span>
          </div>
          <div className="spectral-grid">
            <div className="spectral-tile">
              <span className="spectral-key">NBR (Burn Ratio)</span>
              <strong className="spectral-val">{event.spectral.nbr}</strong>
            </div>
            <div className="spectral-tile">
              <span className="spectral-key">NDVI (Vegetation)</span>
              <strong className="spectral-val">{event.spectral.ndvi}</strong>
            </div>
            <div className="spectral-tile">
              <span className="spectral-key">SWIR Anomaly</span>
              <strong className="spectral-val highlight-val">{event.spectral.swir_anomaly}</strong>
            </div>
            <div className="spectral-tile">
              <span className="spectral-key">MIR/TIR Ratio</span>
              <strong className="spectral-val">{event.spectral.mir_tir_ratio}</strong>
            </div>
            <div className="spectral-tile">
              <span className="spectral-key">Est. Core Temp</span>
              <strong className="spectral-val temp-val">{event.spectral.est_temperature} K</strong>
            </div>
          </div>
        </div>
      )}

      {/* Fire Spread Prediction */}
      {event.spread && (
        <div className="section-card">
          <div className="section-card-header">
            <h4>🌬️ Dynamic Fire Spread Modeling</h4>
            <span className={`spread-badge-${event.spread.spread_risk?.toLowerCase()}`}>
              {event.spread.is_spreading ? `RISK: ${event.spread.spread_risk}` : 'STATIONARY'}
            </span>
          </div>

          {event.spread.is_spreading ? (
            <>
              <div className="spread-meta-grid">
                <div className="spread-stat-box">
                  <span>Surface Wind</span>
                  <strong>{event.spread.wind_speed_kmh} km/h ({event.spread.wind_direction_deg}°)</strong>
                </div>
                <div className="spread-stat-box">
                  <span>Fuel Bed</span>
                  <strong>{event.spread.vegetation_type}</strong>
                </div>
                <div className="spread-stat-box">
                  <span>Expansion Rate</span>
                  <strong className="spread-rate-val">{event.spread.spread_rate_kmh} km/h</strong>
                </div>
              </div>

              <div className="spread-timeline-container">
                <div className="timeline-title">Forecasted Growth Horizons:</div>
                <div className="spread-timeline-grid">
                  {Object.entries(event.spread.predictions || {}).map(([key, pred]) => (
                    <div className="spread-step-card" key={key}>
                      <span className="spread-label">{key.replace('t_plus_', 'T+')}</span>
                      <div className="spread-data-row">
                        <span className="spread-rad">R: {pred.radius_km} km</span>
                        <span className="spread-ar">{pred.area_sq_km} km²</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="no-spread-box">
              <span>📍</span>
              <p>Stationary industrial thermal anomaly — zero wildland fire perimeter expansion modeled.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
