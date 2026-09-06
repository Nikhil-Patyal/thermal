import { ThermalEvent } from '../../../types';

export function ImpactAssessment({ event, setAlertModalOpen }: { event: ThermalEvent; setAlertModalOpen: (open: boolean) => void }) {
  if (!event.impact) return null;

  const getRiskColor = (risk: string) => {
    const colors: { [k: string]: string } = {
      'CRITICAL': '#f87171', 'HIGH': '#fb923c', 'MODERATE': '#fbbf24', 'LOW': '#4ade80',
    };
    return colors[risk] || '#94a3b8';
  };

  return (
    <div className="tab-content">
      {/* Population & Demographics */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>👥 Population Exposure Analysis</h4>
          <span className="card-badge-accent">{event.impact.zone_type?.toUpperCase()} ZONE</span>
        </div>
        <div className="impact-stats-grid">
          <div className="impact-stat-card highlight-card">
            <span className="impact-label">Total Exposed Population</span>
            <strong className="impact-big-num">{event.impact.total_population?.toLocaleString()}</strong>
          </div>
          <div className="impact-stat-card">
            <span className="impact-label">Children Vulnerable</span>
            <strong>{event.impact.children_at_risk?.toLocaleString()}</strong>
          </div>
          <div className="impact-stat-card">
            <span className="impact-label">Elderly Vulnerable</span>
            <strong>{event.impact.elderly_at_risk?.toLocaleString()}</strong>
          </div>
          <div className="impact-stat-card">
            <span className="impact-label">Hazard Perimeter Area</span>
            <strong className="area-val">{event.impact.danger_area_sq_km} km²</strong>
          </div>
        </div>
      </div>

      {/* Air Quality & Toxic Gas Emissions */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>🌫️ Air Quality Health Index (AQHI)</h4>
          <span className="card-badge-muted">SURFACE SENSORS</span>
        </div>
        <div className="aqi-card-banner" style={{ borderLeftColor: event.impact.aqi_color }}>
          <div className="aqi-left">
            <span className="aqi-category-tag" style={{ color: event.impact.aqi_color }}>
              {event.impact.aqi_category?.replace(/_/g, ' ')}
            </span>
            <span className="aqi-pm25-text">PM2.5: <strong>{event.impact.peak_pm25} μg/m³</strong></span>
          </div>
          {event.impact.mask_recommended && (
            <span className="mask-chip">😷 N95 Respirator Required</span>
          )}
        </div>
        <p className="aqi-advisory-text">{event.impact.health_advisory}</p>

        {event.impact.toxic_gases && Object.keys(event.impact.toxic_gases).length > 0 && (
          <div className="toxic-emissions-block">
            <div className="toxic-header">Toxic Plume Concentration:</div>
            <div className="toxic-grid">
              {Object.entries(event.impact.toxic_gases).map(([gas, info]) => (
                <div className="toxic-tile" key={gas}>
                  <span className="toxic-gas-name">{gas}</span>
                  <span className={`toxic-val tg-${info.risk?.toLowerCase()}`}>
                    {info.level} {info.unit}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Psychological & Trauma Impact */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>🧠 Community Psychological Resilience Impact</h4>
          <span className={`card-badge-${event.impact.psych_level?.toLowerCase()}`}>
            {event.impact.psych_level} DISTRESS
          </span>
        </div>
        <div className="psych-score-wrapper">
          <div
            className="psych-gauge"
            style={{
              background: `conic-gradient(${getRiskColor(event.impact.psych_level)} ${event.impact.psych_score * 3.6}deg, rgba(255,255,255,0.06) 0deg)`
            }}
          >
            <div className="psych-gauge-inner">
              <span className="psych-score-num">{event.impact.psych_score}</span>
              <span className="psych-score-lbl">INDEX</span>
            </div>
          </div>
          <div className="psych-meta-block">
            <div className="psych-row">
              <span className="meta-lbl">PTSD Vulnerability Risk:</span>
              <strong className="meta-v highlight-val">{event.impact.ptsd_risk_pct}%</strong>
            </div>
            <div className="psych-row">
              <span className="meta-lbl">Crisis Response Teams:</span>
              <strong className="meta-v">{event.impact.counseling_teams_needed} Teams Needed</strong>
            </div>
            <p className="psych-desc-text">{event.impact.psych_description}</p>
          </div>
        </div>

        {event.impact.psych_factors && (
          <div className="psych-factors-grid">
            {Object.entries(event.impact.psych_factors).map(([factor, score]) => (
              <div className="psych-factor-pill" key={factor}>
                <span className="factor-name">{factor.replace(/_/g, ' ')}</span>
                <span className="factor-score">{score}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Critical Facilities at Risk */}
      {event.impact.vulnerable_facilities?.length > 0 && (
        <div className="section-card">
          <div className="section-card-header">
            <h4>🏥 Critical Infrastructure within Buffer</h4>
            <span className="card-badge-alert">{event.impact.critical_facilities_count} At Risk</span>
          </div>
          <div className="facilities-grid">
            {event.impact.vulnerable_facilities.map((fac, i) => (
              <div className={`facility-card fac-${fac.status?.replace(' ', '-').toLowerCase()}`} key={i}>
                <span className="fac-icon">{fac.icon}</span>
                <div className="fac-details">
                  <span className="fac-title">{fac.type}</span>
                  <span className="fac-sub">{fac.distance_km} km away • {fac.estimated_occupants} occupants</span>
                </div>
                <span className={`fac-badge ${fac.status === 'AT RISK' ? 'badge-danger' : 'badge-warning'}`}>
                  {fac.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Economic Damage & Water Safety */}
      <div className="impact-dual-grid">
        <div className="section-card">
          <div className="section-card-header">
            <h4>💰 Economic Exposure</h4>
          </div>
          <div className="econ-main-val">₹{event.impact.economic_damage_crore} Cr</div>
          {event.impact.economic_breakdown && (
            <div className="econ-breakdown-list">
              {Object.entries(event.impact.economic_breakdown).map(([cat, val]) => (
                <div className="econ-item" key={cat}>
                  <span>{cat}</span>
                  <strong>{val}</strong>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="section-card">
          <div className="section-card-header">
            <h4>💧 Watershed Security</h4>
          </div>
          <div className={`water-risk-chip water-${event.impact.water_risk?.toLowerCase()}`}>
            Risk: {event.impact.water_risk}
          </div>
          <p className="water-advisory-text">{event.impact.water_advisory}</p>
        </div>
      </div>

      {/* Evacuation Pathways */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>🚨 Evacuation & Transit Logistics</h4>
          <span className="card-badge-muted">TRANSIT PROTOCOL</span>
        </div>
        <div className="evac-metrics-grid">
          <div className="evac-metric-box">
            <span>Evacuation Window</span>
            <strong>{event.impact.evac_time_hours} Hours</strong>
          </div>
          <div className="evac-metric-box">
            <span>Transport Required</span>
            <strong>{event.impact.vehicles_needed} Vehicles</strong>
          </div>
          <div className="evac-metric-box hazard-box">
            <span>Critical Hazard Corridor</span>
            <strong className="avoid-text">{event.impact.evac_avoid}</strong>
          </div>
        </div>

        {event.impact.evac_directions?.length > 0 && (
          <div className="evac-routes-list">
            <div className="routes-title">Recommended Safe Escape Corridors:</div>
            {event.impact.evac_directions.map((dir, i) => (
              <div className="evac-route-chip" key={i}>
                <span className="route-dir">🧭 Corridor: {dir.direction}</span>
                <span className="route-safety">Safety Index: {(dir.safety_rating * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Multi-Channel Alert Action Button */}
      {event.risk_score === 'CRITICAL' && (
        <button className="alert-btn-full" onClick={() => setAlertModalOpen(true)}>
          <span className="btn-siren-icon">🚨</span>
          <span>DISPATCH MULTI-CHANNEL EMERGENCY ALERT</span>
        </button>
      )}
    </div>
  );
}
