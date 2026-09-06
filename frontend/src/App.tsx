import React, { useState } from 'react';
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

function App() {
  const [selectedHotspot, setSelectedHotspot] = useState<number | null>(null);

  return (
    <AppContainer>
      <Navbar>
        <Brand>
          <Flame color={theme.colors.danger} />
          NASA FIRMS Intelligence
        </Brand>
      </Navbar>
      
      <MapComponent onHotspotClick={(id) => setSelectedHotspot(id)} />
      
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
