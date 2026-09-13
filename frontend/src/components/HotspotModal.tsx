import { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Satellite, Wind, Thermometer, Users, ShieldAlert, DollarSign, Activity, ZoomIn, ZoomOut } from 'lucide-react';
import { theme } from '../theme';

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

const shimmer = keyframes`
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
`;

const spin = keyframes`
  to { transform: rotate(360deg); }
`;

const Overlay = styled(motion.div)`
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
  backdrop-filter: blur(2px);
`;

const Panel = styled(motion.div)`
  width: 480px;
  height: 100%;
  background: rgba(10, 14, 23, 0.92);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(56, 189, 248, 0.15);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  scrollbar-width: thin;
`;

const HeaderRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
`;

const Title = styled.h2`
  margin: 0;
  font-size: 1.4rem;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const CloseBtn = styled.button`
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: 50%;
  width: 32px; height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { background: rgba(255,255,255,0.2); color: #fff; }
`;

const Body = styled.div`
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const Section = styled.div``;

const SectionLabel = styled.div`
  font-size: 0.8rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
`;

const Grid = styled.div<{ cols?: number }>`
  display: grid;
  grid-template-columns: repeat(${p => p.cols || 2}, 1fr);
  gap: 12px;
`;

const Card = styled.div`
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
`;

const CardIcon = styled.div`
  color: #38bdf8;
  margin-bottom: 8px;
`;

const CardLabel = styled.div`
  font-size: 0.75rem;
  color: #cbd5e1;
  margin-bottom: 4px;
`;

const CardValue = styled.div<{ $color?: string }>`
  font-size: 1.15rem;
  font-weight: 600;
  color: ${p => p.$color || '#fff'};
`;

const CardSub = styled.div`
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 4px;
`;

const ClassBadge = styled.div<{ $color: string }>`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  background: ${p => p.$color}15;
  border: 1px solid ${p => p.$color}30;
  color: ${p => p.$color};
  font-weight: 600;
  font-size: 0.9rem;
`;

const Skeleton = styled.div<{ width?: number }>`
  height: 20px;
  width: ${p => p.width ? `${p.width}px` : '100%'};
  background: #1e293b;
  background-image: linear-gradient(to right, #1e293b 0%, #334155 20%, #1e293b 40%, #1e293b 100%);
  background-repeat: no-repeat;
  background-size: 800px 100%;
  animation: ${shimmer} 1.5s infinite linear;
  border-radius: 4px;
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

// Removed ShapRow as it's no longer used

const getClassColor = (cls: string | null) => {
  if (!cls) return '#facc15';
  const c = cls.toLowerCase();
  if (c.includes('wildfire') || c.includes('forest')) return '#ef4444';
  if (c.includes('crop') || c.includes('agricultural')) return '#f97316';
  if (c.includes('industrial') || c.includes('flare')) return '#a855f7';
  return '#facc15';
};

const fmt = (v: number | null | undefined, unit = '', digits = 1) =>
  v != null ? `${v.toFixed(digits)}${unit}` : null;

const fmtLarge = (v: number | null | undefined) =>
  v != null ? new Intl.NumberFormat('en-US').format(v) : null;

export const HotspotModal = ({ hotspotId, onClose }: { hotspotId: number | null, onClose: () => void }) => {
  const [data, setData] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(false);
  
  const [imagery, setImagery] = useState<ImageryData | null>(null);
  const [imageryLoading, setImageryLoading] = useState(false);
  const [activeBand, setActiveBand] = useState<BandKey>('true_color');
  const [imgLoaded, setImgLoaded] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    if (!hotspotId) return;
    setDataLoading(true);
    setData(null);
    setImagery(null);
    setImgLoaded(false);

    fetch(`${BACKEND}/api/hotspots/${hotspotId}/`)
      .then(r => r.json())
      .then(json => { setData(json); setDataLoading(false); })
      .catch(err => { console.error('Hotspot detail error', err); setDataLoading(false); });
  }, [hotspotId]);

  useEffect(() => {
    if (!hotspotId) return;
    setImageryLoading(true);
    setImgLoaded(false);

    fetch(`${BACKEND}/api/hotspots/${hotspotId}/imagery/`)
      .then(r => r.json())
      .then((json: ImageryData) => { setImagery(json); setImageryLoading(false); })
      .catch(err => { console.error('Imagery error', err); setImageryLoading(false); });
  }, [hotspotId]);

  if (!hotspotId) return null;

  const color = getClassColor(data?.predicted_class);
  const lat = data?.lat;
  const lng = data?.lng;
  const frp = data?.frp;
  const confPct = data?.confidence_score != null ? `${(data.confidence_score * 100).toFixed(1)}%` : null;
  const aq = data?.air_quality;
  const wx = data?.weather;
  const ee = data?.economic_exposure;
  const pe = data?.population_exposure;
  const sr = data?.safe_route;

  // Construct image URL, handling absolute URLs from backend fallback
  const imagePath = imagery && imagery[activeBand];
  const currentImageUrl = imagePath
    ? imagePath.startsWith('http') ? imagePath : `${BACKEND}${imagePath}`
    : null;

  const evidenceList: string[] = data?.shap_values?.evidence || [];
  const aqiColor = aq?.aqi != null ? (aq.aqi > 150 ? '#ef4444' : aq.aqi > 100 ? '#facc15' : '#4ade80') : '#e2e8f0';

  return (
    <AnimatePresence>
      <Overlay
        key="overlay"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      >
        <Panel
          key="panel"
          initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
          transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
        >
          <HeaderRow>
            <div>
              <Title>
                <Activity size={20} color={color} />
                Hotspot Dossier
              </Title>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
                ID: {hotspotId}
                {data?.acquisition_date && ` • ${new Date(data.acquisition_date).toLocaleString()}`}
              </div>
            </div>
            <CloseBtn onClick={onClose}><X size={20} /></CloseBtn>
          </HeaderRow>

          <Body>
            {/* ── Classification badge ── */}
            <Section>
              <SectionLabel>AI Classification</SectionLabel>
              {dataLoading
                ? <Skeleton style={{ width: '60%', height: '36px', borderRadius: '24px' }} />
                : <ClassBadge $color={color}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
                    {data?.predicted_class ?? 'Unknown Thermal Anomaly'}
                  </ClassBadge>
              }
            </Section>

            <Section>
              <SectionLabel>Observation Data</SectionLabel>
              <Grid>
                <Card>
                  <CardIcon><Activity size={14} /></CardIcon>
                  <CardLabel>Fire Radiative Power</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue $color={(frp && frp > 500) ? '#ef4444' : (frp && frp > 100) ? '#f97316' : '#e2e8f0'}>{fmt(frp, ' MW', 1) ?? '—'}</CardValue>}
                  <CardSub>FIRMS / VIIRS</CardSub>
                </Card>
                <Card>
                  <CardIcon><ShieldAlert size={14} /></CardIcon>
                  <CardLabel>Rule Confidence</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue $color="#4ade80">{confPct ?? '—'}</CardValue>}
                  <CardSub>Strict Evidence Engine</CardSub>
                </Card>
                <Card>
                  <CardIcon><Activity size={14} /></CardIcon>
                  <CardLabel>Brightness (K)</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmt(data?.brightness, ' K') ?? '—'}</CardValue>}
                  <CardSub>VIIRS I-Band</CardSub>
                </Card>
                <Card>
                  <CardIcon><Users size={14} /></CardIcon>
                  <CardLabel>Population Exposed</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmtLarge(pe?.population_count) ?? '—'}</CardValue>}
                  <CardSub>Spatial Query</CardSub>
                </Card>
              </Grid>
            </Section>

            {/* ── Live weather ── */}
            <Section>
              <SectionLabel>Live Weather <span style={{ color: '#4ade80', fontSize: '0.62rem' }}>· Open-Meteo</span></SectionLabel>
              <Grid cols={3}>
                <Card>
                  <CardIcon><Thermometer size={14} /></CardIcon>
                  <CardLabel>Temperature</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmt(wx?.temperature_c, '°C') ?? '—'}</CardValue>}
                </Card>
                <Card>
                  <CardIcon><Wind size={14} /></CardIcon>
                  <CardLabel>Wind Speed</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmt(wx?.wind_speed_ms, 'm/s') ?? '—'}</CardValue>}
                </Card>
                <Card>
                  <CardIcon><Thermometer size={14} /></CardIcon>
                  <CardLabel>Humidity</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmt(wx?.humidity, '%') ?? '—'}</CardValue>}
                </Card>
              </Grid>
            </Section>

            {/* ── Air quality ── */}
            <Section>
              <SectionLabel>Air Quality <span style={{ color: '#4ade80', fontSize: '0.62rem' }}>· Open-Meteo AQ</span></SectionLabel>
              <Grid cols={3}>
                <Card>
                  <CardLabel>US AQI</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue $color={aqiColor}>{aq?.aqi ?? '—'}</CardValue>}
                  <CardSub>{aq?.aqi != null ? (aq.aqi > 150 ? 'Unhealthy' : aq.aqi > 100 ? 'Sensitive' : 'Good') : ''}</CardSub>
                </Card>
                <Card>
                  <CardLabel>PM₂.₅</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmt(aq?.pm25, ' µg/m³', 1) ?? '—'}</CardValue>}
                </Card>
                <Card>
                  <CardLabel>NO₂</CardLabel>
                  {dataLoading ? <Skeleton /> : <CardValue>{fmt(aq?.no2, ' µg/m³', 1) ?? '—'}</CardValue>}
                </Card>
              </Grid>
            </Section>

            {/* ── Satellite Imagery ── */}
            {(imagery && (imagery.true_color || imagery.false_color || imagery.ndvi || imagery.nbr)) && (
              <Section>
                <SectionLabel><Satellite size={12} /> Sentinel-2 Satellite Imagery <span style={{ color: '#4ade80', fontSize: '0.62rem' }}>· Copernicus CDSE</span></SectionLabel>

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
                
                {/* Zoom controls */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
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
                </div>

                <div style={{ fontSize: '0.72rem', color: '#475569', marginBottom: '10px' }}>
                  {BandLegend[activeBand].desc}
                </div>

                <ImageBox style={{ overflow: 'hidden' }}>
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
                        <span style={{ fontSize: '0.65rem', color: '#334155', maxWidth: '240px', textAlign: 'center' }}>
                          {imagery.error}
                        </span>
                      )}
                    </ImagerySpinner>
                  )}

                  {!imageryLoading && currentImageUrl && (
                    <>
                      {!imgLoaded && (
                        <ImagerySpinner>
                          <Spinner />
                          <span>Loading image…</span>
                        </ImagerySpinner>
                      )}
                      <SatImage
                        src={currentImageUrl}
                        alt={`${BandLegend[activeBand].label} for hotspot ${hotspotId}`}
                        onLoad={() => setImgLoaded(true)}
                        style={{ 
                          opacity: imgLoaded ? 1 : 0, 
                          transform: `scale(${zoomLevel})`,
                          transformOrigin: 'center',
                          transition: 'opacity 0.4s ease, transform 0.2s' 
                        }}
                      />
                    </>
                  )}

                  {/* Band label overlay */}
                  {!imageryLoading && currentImageUrl && imgLoaded && (
                    <div style={{
                      position: 'absolute', bottom: 10, left: 10,
                      background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
                      borderRadius: '8px', padding: '4px 10px',
                      fontSize: '0.7rem', color: '#e2e8f0',
                      border: '1px solid rgba(255,255,255,0.08)',
                    }}>
                      🛰 {BandLegend[activeBand].label} · 1024×1024px · Sentinel-2 L2A
                    </div>
                  )}

                  {/* Coord overlay */}
                  {!imageryLoading && currentImageUrl && imgLoaded && lat != null && (
                    <div style={{
                      position: 'absolute', top: 10, right: 10,
                      background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
                      borderRadius: '8px', padding: '4px 10px',
                      fontSize: '0.68rem', color: '#94a3b8', fontFamily: 'monospace',
                      border: '1px solid rgba(255,255,255,0.08)',
                    }}>
                      {lat.toFixed(4)}°, {lng.toFixed(4)}°
                    </div>
                  )}
                </ImageBox>
              </Section>
            )}

            {/* ── Classification Evidence ── */}
            {(evidenceList.length > 0 || !dataLoading) && (
              <Section>
                <SectionLabel>Classification Evidence</SectionLabel>
                {dataLoading
                  ? [1, 2, 3].map(i => <Skeleton key={i} style={{ marginBottom: 10, height: 8 }} />)
                  : evidenceList.length > 0
                    ? (
                      <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.82rem', color: '#cbd5e1' }}>
                        {evidenceList.map((ev, i) => (
                          <li key={i} style={{ marginBottom: 6 }}>{ev}</li>
                        ))}
                      </ul>
                    )
                    : (
                      <div style={{ fontSize: '0.82rem', color: '#475569' }}>
                        No geographic evidence rules matched. Classification defaulted to Unknown.
                      </div>
                    )
                }
              </Section>
            )}

          </Body>
        </Panel>
      </Overlay>
    </AnimatePresence>
  );
};
