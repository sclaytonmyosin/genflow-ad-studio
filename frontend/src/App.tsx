import { ThemeProvider, CssBaseline } from '@mui/material';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { theme } from './theme';
import MainLayout from './components/layout/MainLayout';
import PipelinePage from './components/pages/PipelinePage';
import BulkPage from './components/pages/BulkPage';
import ReviewPage from './components/pages/ReviewPage';
import HistoryPage from './components/pages/HistoryPage';
import HowItWorksPage from './components/pages/HowItWorksPage';

// Strip trailing slash from Vite's BASE_URL so React Router gets a clean
// basename (e.g. "/genflow/" → "/genflow"). For dev / single-app deploys
// where BASE_URL = "/", basename is undefined (default).
const BASENAME = (() => {
  const b = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');
  return b === '' ? undefined : b;
})();

function App() {
  return (
    <ThemeProvider theme={theme} defaultMode="dark">
      <CssBaseline />
      <BrowserRouter basename={BASENAME}>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<PipelinePage />} />
            <Route path="/bulk" element={<BulkPage />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/how-it-works" element={<HowItWorksPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
