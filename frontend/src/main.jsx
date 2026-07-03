import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';

// Version de déploiement - BUILD_2026-01-10_07:25:00_API_FIX_COMPLETE
console.log('%c🚀 COORDINATOR FRONTEND v2026.01.10.0725 - API PATHS FIXED', 'background: #00B0F0; color: white; font-size: 14px; padding: 5px 10px; border-radius: 3px;');
console.log('%c✅ Tous les appels API corrigés: /api/ -> pas de double préfixe', 'color: #00FF88; font-size: 12px;');

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
)