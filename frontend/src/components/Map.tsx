import { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import styled from 'styled-components';
import { theme } from '../theme';

import L from 'leaflet';

// Fix missing default leaflet marker icons in Vite/Webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const getClassColor = (predictedClass: string, status?: string) => {
  if (!predictedClass) return '#475569'; // Grey for Pending/Unknown
  const cls = predictedClass.toLowerCase();
  if (cls.includes('wildland') || cls.includes('forest')) return '#ef4444'; // Red
  if (cls.includes('agri') || cls.includes('crop')) return '#f97316'; // Orange
  if (cls.includes('industrial') || cls.includes('flare')) {
    if (status && status.toLowerCase().includes('suspected')) return '#e11d48'; // Bright Red/Rose for Incident
    return '#a855f7';  // Purple / Routine Industrial
  }
  if (cls.includes('other') || cls.includes('uncertain')) return '#475569';   // Grey
  return '#facc15'; // Default Yellow
};

const Legend = styled.div`
  position: absolute;
  bottom: 24px;
  left: 24px;
  z-index: 500;
  ${theme.effects.glassmorphism}
  background: rgba(11, 15, 25, 0.85);
  border: 1px solid ${theme.colors.glassBorder};
  border-radius: 12px;
  padding: 12px 16px;
  overflow: auto;
  font-size: 0.8rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);

  .legend-title {
    font-weight: 700;
    margin-bottom: 8px;
    color: ${theme.colors.primary};
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 1px solid white;
  }
`;

const MapWrapper = styled.div`
  height: 100vh;
  width: 100vw;
  position: relative;
  
  @keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 8px rgba(255, 69, 0, 0.6); }
    50% { transform: scale(1.15); box-shadow: 0 0 20px rgba(255, 69, 0, 0.9); }
    100% { transform: scale(0.95); box-shadow: 0 0 8px rgba(255, 69, 0, 0.6); }
  }

  .leaflet-container {
    height: 100%;
    width: 100%;
    background-color: ${theme.colors.background};
  }
  
  .leaflet-popup-content-wrapper {
    background: ${theme.colors.surface};
    backdrop-filter: blur(12px);
    border: 1px solid ${theme.colors.glassBorder};
    color: ${theme.colors.text};
    border-radius: 12px;
  }
  
  .leaflet-popup-tip {
    background: ${theme.colors.surface};
  }

  /* Style the layers control for dark mode */
  .leaflet-control-layers {
    background: ${theme.colors.surface};
    backdrop-filter: blur(12px);
    border: 1px solid ${theme.colors.glassBorder};
    color: ${theme.colors.text};
    border-radius: 8px;
  }
`;

interface MapComponentProps {
  onHotspotClick: (id: number) => void;
  onDataLoaded?: (count: number) => void;
}

export const MapComponent: React.FC<MapComponentProps> = ({ onHotspotClick, onDataLoaded }) => {
  const mapRef = useRef<L.Map | null>(null);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const zoomLevel = 4;

  useEffect(() => {
    // Fetch all hotspot map markers from the lightweight endpoint
    const fetchHotspots = async () => {
      try {
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
        // Add cache-busting timestamp to prevent browser from serving stale map data
        const timestamp = new Date().getTime();
        const response = await fetch(`${backendUrl}/api/hotspots/map-points/?t=${timestamp}`, { cache: 'no-store' });
        const data = await response.json();

        const transformed = data
          .filter((h: any) =>
            typeof h.lat === 'number' && !isNaN(h.lat) &&
            typeof h.lng === 'number' && !isNaN(h.lng)
          )
          .map((h: any) => ({
            id: h.id,
            lat: h.lat,
            lng: h.lng,
            predicted_class: h.source_type || h.predicted_class || 'Other / uncertain thermal anomaly',
            industrial_status: h.industrial_anomaly_status,
            frp: h.frp,
            confidence_score: h.confidence_score,
          }));

        // Z-Index Fix: Render Unknown hotspots first, so classified hotspots render on top of them
        transformed.sort((a: any, b: any) => {
          const aUnknown = !a.predicted_class || a.predicted_class.includes('uncertain') || a.predicted_class.includes('Unknown');
          const bUnknown = !b.predicted_class || b.predicted_class.includes('uncertain') || b.predicted_class.includes('Unknown');
          if (aUnknown && !bUnknown) return -1;
          if (!aUnknown && bUnknown) return 1;
          return 0;
        });

        setHotspots(transformed);
        if (onDataLoaded) {
          onDataLoaded(transformed.length);
        }
      } catch (err) {
        console.error('Failed to load hotspots', err);
      }
    };
    fetchHotspots();
  }, []);

  return (
    <MapWrapper>
      <MapContainer ref={mapRef} 
        center={[20.5937, 78.9629]} 
        zoom={zoomLevel} 
        minZoom={4}
        maxZoom={18}
        preferCanvas={true}
        scrollWheelZoom={true}
        maxBounds={[[6.0, 68.0], [38.0, 98.0]]}
        maxBoundsViscosity={1.0}
        style={{ height: '100%', width: '100%' }}
        worldCopyJump={false}
      >
        <LayersControl position="topright">

          {/* Default: OpenStreetMap – free, no API key required */}
          <LayersControl.BaseLayer name="Street Map (OpenStreetMap)">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
              noWrap={true}
              bounds={[[-85, -180], [85, 180]]}
            />
          </LayersControl.BaseLayer>

          {/* OpenTopoMap – free topographic alternative */}
          <LayersControl.BaseLayer name="Topographic (OpenTopoMap)">
            <TileLayer
              attribution='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
              url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
              maxZoom={17}
              noWrap={true}
              bounds={[[-85, -180], [85, 180]]}
            />
          </LayersControl.BaseLayer>

          {/* Esri Satellite – may not load without auth in all environments */}
          <LayersControl.BaseLayer checked name="Satellite Imagery (Esri)">
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri</a>, Earthstar Geographics'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              maxZoom={19}
              noWrap={true}
              bounds={[[-85, -180], [85, 180]]}
            />
          </LayersControl.BaseLayer>

        </LayersControl>

        {hotspots.map((h) => {
          const markerColor = getClassColor(h.predicted_class, h.industrial_status);
          const isUnknown = markerColor === '#475569';
          return (
            <CircleMarker
              key={h.id}
              center={[h.lat, h.lng]}
              radius={isUnknown ? 4 : (h.frp > 50 ? 7 : 5)}
              pathOptions={{
                color: isUnknown ? '#94a3b8' : '#ffffff',
                weight: isUnknown ? 1.5 : 1.2,
                fillColor: isUnknown ? 'transparent' : markerColor,
                fillOpacity: isUnknown ? 0 : 1.0,
                dashArray: isUnknown ? '2, 4' : undefined,
              }}
              eventHandlers={{
                click: () => {
                  mapRef.current?.setView([h.lat, h.lng], 12);
                  onHotspotClick(h.id);
                },
              }}
            >
              <Popup>
                <div style={{ padding: '6px' }}>
                  <strong style={{ color: isUnknown ? '#94a3b8' : markerColor }}>
                    {h.predicted_class}
                  </strong>
                  <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                    FRP: {h.frp} MW
                  </div>
                  <div style={{ fontSize: '0.8rem' }}>
                    Evidence Strength: {h.confidence_score ? h.confidence_score : 'Low'}
                  </div>
                  {isUnknown && (
                    <div style={{ fontSize: '0.75rem', marginTop: '4px', color: '#facc15' }}>
                      ⚠ Insufficient evidence — not source-confirmed
                    </div>
                  )}
                  {!isUnknown && (
                    <div style={{ fontSize: '0.75rem', marginTop: '4px', color: '#cbd5e1' }}>
                      Supported by Evidence (Not Independently Verified)
                    </div>
                  )}
                  <button onClick={() => onHotspotClick(h.id)} style={{ fontSize: '0.75rem', marginTop: '6px', color: '#38bdf8', cursor: 'pointer', background: 'none', border: 'none', padding: 0 }}>
                    Click to view detailed dossier &rarr;
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <Legend>
        <div className="legend-title">⚡ AI Classification Legend</div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ef4444' }} />
          <span>Wildfire / Forest Fire</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#06b6d4' }} />
          <span>Mining & Smelter Thermal</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#a855f7' }} />
          <span>Industrial Flare / Refinery</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#f97316' }} />
          <span>Crop Residue / Agricultural</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#475569', opacity: 0.5 }} />
          <span>Unclassified / API Rate Limited</span>
        </div>
      </Legend>
    </MapWrapper>
  );
};
