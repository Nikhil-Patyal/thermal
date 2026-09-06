export const theme = {
  colors: {
    background: '#0B0F19',
    surface: 'rgba(20, 27, 45, 0.6)',
    surfaceHighlight: 'rgba(30, 41, 59, 0.8)',
    primary: '#38BDF8', // Cool cyan
    secondary: '#818CF8', // Indigo
    text: '#F8FAFC',
    textMuted: '#94A3B8',
    danger: '#F43F5E',
    warning: '#FBBF24',
    success: '#10B981',
    info: '#0EA5E9',
    glassBorder: 'rgba(255, 255, 255, 0.1)',
  },
  effects: {
    glassmorphism: `
      background: rgba(20, 27, 45, 0.6);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    `,
  },
  transitions: {
    default: '0.3s ease-in-out',
    fast: '0.15s ease-in-out',
  }
};
