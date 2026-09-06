import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from '../theme';
import { X } from 'lucide-react';

const Overlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
`;

const ModalContainer = styled(motion.div)`
  width: 450px;
  height: 100%;
  ${theme.effects.glassmorphism}
  background: rgba(11, 15, 25, 0.85); /* Slightly darker for readability */
  border-left: 1px solid ${theme.colors.glassBorder};
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h2`
  font-size: 1.5rem;
  color: ${theme.colors.primary};
  margin: 0;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: ${theme.colors.textMuted};
  cursor: pointer;
  transition: ${theme.transitions.fast};
  &:hover {
    color: ${theme.colors.danger};
  }
`;

const SectionTitle = styled.h3`
  font-size: 1.1rem;
  color: ${theme.colors.secondary};
  margin: 16px 0 8px 0;
  border-bottom: 1px solid ${theme.colors.glassBorder};
  padding-bottom: 4px;
`;

const StatGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
`;

const StatCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
`;

const StatLabel = styled.div`
  font-size: 0.8rem;
  color: ${theme.colors.textMuted};
  margin-bottom: 4px;
`;

const StatValue = styled.div`
  font-size: 1.1rem;
  font-weight: bold;
`;

interface HotspotModalProps {
  hotspotId: number | null;
  onClose: () => void;
}

export const HotspotModal: React.FC<HotspotModalProps> = ({ hotspotId, onClose }) => {
  if (!hotspotId) return null;

  return (
    <AnimatePresence>
      <Overlay
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <ModalContainer
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        >
          <Header>
            <Title>Thermal Dossier</Title>
            <CloseButton onClick={onClose}>
              <X size={24} />
            </CloseButton>
          </Header>

          {/* Placeholder for Satellite Image */}
          <div style={{ width: '100%', height: '200px', backgroundColor: '#1e293b', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
            NASA GIBS True-Color Thumbnail
          </div>

          <SectionTitle>Classification</SectionTitle>
          <StatGrid>
            <StatCard>
              <StatLabel>Predicted Class</StatLabel>
              <StatValue style={{ color: theme.colors.warning }}>Industrial Fire</StatValue>
            </StatCard>
            <StatCard>
              <StatLabel>Confidence</StatLabel>
              <StatValue style={{ color: theme.colors.success }}>94.2%</StatValue>
            </StatCard>
          </StatGrid>

          <SectionTitle>Enrichment Data</SectionTitle>
          <StatGrid>
            <StatCard>
              <StatLabel>Economic Exposure</StatLabel>
              <StatValue>$45M GDP</StatValue>
            </StatCard>
            <StatCard>
              <StatLabel>Air Quality (AQI)</StatLabel>
              <StatValue style={{ color: theme.colors.danger }}>142</StatValue>
            </StatCard>
            <StatCard>
              <StatLabel>Safe Route</StatLabel>
              <StatValue>12.4 km</StatValue>
            </StatCard>
            <StatCard>
              <StatLabel>Population Exposed</StatLabel>
              <StatValue>14,500</StatValue>
            </StatCard>
            <StatCard>
              <StatLabel>Weather (Temp)</StatLabel>
              <StatValue>32°C</StatValue>
            </StatCard>
            <StatCard>
              <StatLabel>Water Contamination</StatLabel>
              <StatValue>Low</StatValue>
            </StatCard>
          </StatGrid>

          <SectionTitle>SHAP Explanation</SectionTitle>
          <div style={{ fontSize: '0.9rem', color: theme.colors.textMuted, marginBottom: '16px' }}>
            High confidence driven by high Fire Radiative Power (FRP) and proximity to industrial zone.
          </div>
          {/* Simple mock bar chart for SHAP */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ width: '100px', fontSize: '0.8rem' }}>FRP</div>
              <div style={{ height: '8px', background: theme.colors.primary, width: '80%', borderRadius: '4px' }}></div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ width: '100px', fontSize: '0.8rem' }}>Dist to Industry</div>
              <div style={{ height: '8px', background: theme.colors.primary, width: '60%', borderRadius: '4px' }}></div>
            </div>
          </div>
          
        </ModalContainer>
      </Overlay>
    </AnimatePresence>
  );
};
