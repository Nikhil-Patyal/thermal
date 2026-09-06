import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import styled from 'styled-components';
import { theme } from '../theme';

const MapWrapper = styled.div`
  height: 100vh;
  width: 100vw;
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
}

export const MapComponent: React.FC<MapComponentProps> = ({ onHotspotClick }) => {
  const [hotspots, setHotspots] = useState<any[]>([]);

  useEffect(() => {
    // Fetch live hotspots from backend API
    const fetchHotspots = async () => {
      try {
        const response = await fetch(import.meta.env.VITE_BACKEND_URL + '/api/hotspots/');
        const data = await response.json();
        // Transform GeoJSON to simple array for map
        const transformed = data.map((h:any) => ({
          id: h.id,
          lat: h.location.coordinates[1], // GeoJSON [lng, lat]
          lng: h.location.coordinates[0],
          predicted_class: h.predicted_class,
        }));
        setHotspots(transformed);
      } catch (err) {
        console.error('Failed to load hotspots', err);
      }
    };
    fetchHotspots();
  }, []);

  return (
    <MapWrapper>
      <MapContainer center={[22.9, 78.9]} zoom={5} scrollWheelZoom={true}>
        <LayersControl position="topright">
          
          <LayersControl.BaseLayer checked name="Carto Dark (Default)">
            <TileLayer
              attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="Satellite Imagery">
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="OpenStreetMap (Standard)">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="Streets Map">
            <TileLayer
              attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
          </LayersControl.BaseLayer>

        </LayersControl>

        {hotspots.map((h) => (
          <Marker 
            key={h.id} 
            position={[h.lat, h.lng]}
            eventHandlers={{
              click: () => onHotspotClick(h.id),
            }}
          >
            <Popup>
              Click to view detailed dossier.
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </MapWrapper>
  );
};
