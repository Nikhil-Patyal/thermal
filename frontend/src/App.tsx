import { useState } from 'react';
import styled from 'styled-components';
import { MapComponent } from './components/Map';
import { HotspotModal } from './components/HotspotModal';
import { theme } from './theme';
import { Flame } from 'lucide-react';

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
`;

const Navbar = styled.div`
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 500;
  ${theme.effects.glassmorphism}
  padding: 12px 24px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Brand = styled.h1`
  font-size: 1.2rem;
  color: ${theme.colors.primary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const StatsBadge = styled.div`
  background: rgba(255, 69, 0, 0.15);
  border: 1px solid rgba(255, 69, 0, 0.4);
  color: #ff7849;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
`;

const NavActions = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

function App() {
  const [selectedHotspot, setSelectedHotspot] = useState<number | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);

  return (
    <AppContainer>
      <Navbar>
        <Brand>
          <Flame color={theme.colors.danger} />
          Thermal Sentinel: NASA FIRMS Intelligence
        </Brand>
        <NavActions>
          <StatsBadge>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ff4500', display: 'inline-block' }} />
            {totalCount > 0 ? `${totalCount} Active Anomalies Monitored` : 'Active Anomalies Monitored'}
          </StatsBadge>
        </NavActions>
      </Navbar>
      
      <MapComponent 
        onHotspotClick={(id) => setSelectedHotspot(id)} 
        onDataLoaded={(count) => setTotalCount(count)}
      />
      
      {selectedHotspot && (
        <HotspotModal 
          hotspotId={selectedHotspot} 
          onClose={() => setSelectedHotspot(null)} 
        />
      )}
    </AppContainer>
  );
}

export default App;
