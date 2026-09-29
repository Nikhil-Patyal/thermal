import { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { Satellite, ZoomIn, ZoomOut } from 'lucide-react';
import { ThermalEvent, Metadata } from '../../../types';

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

interface ImageryData {
  hotspot_id: number;
  true_color: string | null;
  false_color: string | null;
  ndvi: string | null;
  nbr: string | null;
  status: string;
  error: string | null;
}

const BAND_KEYS = ['true_color', 'false_color', 'ndvi', 'nbr'] as const;
type BandKey = typeof BAND_KEYS[number];
const BandLegend: Record<BandKey, { label: string, desc: string }> = {
  true_color: { label: 'True Color', desc: 'Natural visual spectrum' },
  false_color: { label: 'False Color', desc: 'Highlights active fires and burn scars' },
  ndvi: { label: 'NDVI', desc: 'Vegetation health index' },
  nbr: { label: 'NBR', desc: 'Burn severity index' }
};

const spin = keyframes`
  to { transform: rotate(360deg); }
`;

const BandTabs = styled.div`
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  background: rgba(0,0,0,0.2);
  padding: 4px;
  border-radius: 8px;
`;

const BandTab = styled.button<{ $active: boolean }>`
  flex: 1;
  background: ${p => p.$active ? 'rgba(255,255,255,0.1)' : 'transparent'};
  border: none;
  border-radius: 6px;
  padding: 6px 0;
  color: ${p => p.$active ? '#fff' : '#94a3b8'};
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  &:hover {
    background: rgba(255,255,255,0.1);
    color: #fff;
  }
`;

const ImageBox = styled.div`
  width: 100%;
  height: 280px;
  background: rgba(0,0,0,0.3);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
`;

const SatImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 11px;
`;

const ImagerySpinner = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #38bdf8;
  font-size: 0.8rem;
`;

const Spinner = styled.div`
  width: 24px;
  height: 24px;
  border: 2px solid rgba(56,189,248,0.2);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`;

interface TelemetryProps {
  event: ThermalEvent;
  metadata?: Metadata | null;
}

export function Telemetry({ event, metadata }: TelemetryProps) {
  const [imagery, setImagery] = useState<ImageryData | null>(null);
  const [imageryLoading, setImageryLoading] = useState(false);
  const [activeBand, setActiveBand] = useState<BandKey>('true_color');
  const [imgLoaded, setImgLoaded] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    if (!event?.id) return;
    setImageryLoading(true);
    setImgLoaded(false);

    fetch(`${BACKEND}/api/hotspots/${event.id}/imagery/`)
      .then(r => r.json())
      .then((json: ImageryData) => { setImagery(json); setImageryLoading(false); })
      .catch(err => { console.error('Imagery error', err); setImageryLoading(false); });
  }, [event?.id]);

  const currentImageUrl = imagery ? imagery[activeBand] : null;

  return (
    <div className="tab-content">
      {/* ── Satellite Imagery (Sentinel-2) ── */}
      <div className="section-card">
        <div className="section-card-header">
          <h4><Satellite size={16} style={{ display: 'inline', verticalAlign: 'text-bottom' }} /> Sentinel-2 Satellite Imagery</h4>
          <span className="card-badge-muted">COPERNICUS CDSE</span>
        </div>
        
        <div style={{ padding: '0 16px 16px' }}>
          <BandTabs>
            {BAND_KEYS.map(band => (
              <BandTab
                key={band}
                $active={activeBand === band}
                onClick={() => { setActiveBand(band); setImgLoaded(false); }}
              >
                {BandLegend[band].label}
              </BandTab>
            ))}
          </BandTabs>
          
          <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', alignItems: 'center' }}>
            <button onClick={() => setZoomLevel(z => Math.max(z - 0.25, 0.5))}
                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '4px', padding: '4px 6px', cursor: zoomLevel <= 0.5 ? 'not-allowed' : 'pointer', opacity: zoomLevel <= 0.5 ? 0.5 : 1 }}
                    disabled={zoomLevel <= 0.5}
            >
              <ZoomOut size={14} color="#94a3b8" />
            </button>
            <button onClick={() => setZoomLevel(z => Math.min(z + 0.25, 5))}
                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '4px', padding: '4px 6px', cursor: zoomLevel >= 5 ? 'not-allowed' : 'pointer', opacity: zoomLevel >= 5 ? 0.5 : 1 }}
                    disabled={zoomLevel >= 5}
            >
              <ZoomIn size={14} color="#94a3b8" />
            </button>
            <span style={{ fontSize: '0.72rem', color: '#475569', marginLeft: 'auto' }}>
              {BandLegend[activeBand].desc}
            </span>
          </div>

          <ImageBox>
            {imageryLoading && (
              <ImagerySpinner>
                <Spinner />
                <span>Fetching Sentinel-2 tiles…</span>
              </ImagerySpinner>
            )}

            {!imageryLoading && !currentImageUrl && (
              <ImagerySpinner style={{ color: '#475569' }}>
                <Satellite size={28} />
                <span>No cloud-free imagery available</span>
                {imagery?.error && (
                  <span style={{ fontSize: '0.65rem', color: '#334155', maxWidth: '240px', textAlign: 'center', marginTop: '8px' }}>
                    {imagery.error}
                  </span>
                )}
              </ImagerySpinner>
            )}

            {!imageryLoading && currentImageUrl && (
              <>
                {!imgLoaded && (
                  <ImagerySpinner style={{ position: 'absolute' }}>
                    <Spinner />
                  </ImagerySpinner>
                )}
                <SatImage
                  src={`${BACKEND}${currentImageUrl}`}
                  onLoad={() => setImgLoaded(true)}
                  style={{
                    opacity: imgLoaded ? 1 : 0,
                    transform: `scale(${zoomLevel})`,
                    transition: 'opacity 0.3s, transform 0.2s'
                  }}
                  alt={activeBand}
                />
              </>
            )}
          </ImageBox>
        </div>
      </div>

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
            <span className="telemetry-k">Brightness (TI4)</span>
            <strong className="telemetry-v">{event.bright_ti4 || event.brightness || 'N/A'} K</strong>
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
