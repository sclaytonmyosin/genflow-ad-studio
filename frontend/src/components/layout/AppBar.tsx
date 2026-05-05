import {
  AppBar as MuiAppBar,
  Toolbar,
  Box,
  Typography,
} from '@mui/material';
import { useColorScheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

/**
 * Myosin wordmark — lowercase "myosin" with the parallel-slash M-mark in
 * cyan. Aligned exactly with ops.myosin.io.
 */
function MyosinWordmark({ mode }: { mode: string }) {
  const textColor = mode === 'dark' ? '#E8EEF5' : '#0B0E11';
  const accentColor = '#22d3ee';
  const accentBgFill = mode === 'dark' ? '#06b6d4' : '#06b6d4';

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.25,
        cursor: 'pointer',
        userSelect: 'none',
      }}
    >
      <Box sx={{ position: 'relative', width: 32, height: 32 }}>
        <svg width="32" height="32" viewBox="0 0 36 36" fill="none">
          <rect width="36" height="36" rx="8" fill={accentBgFill} fillOpacity="0.10" />
          <rect width="36" height="36" rx="8" fill="none" stroke={accentBgFill} strokeOpacity="0.35" strokeWidth="1" />
          <path
            d="M9 26 L17 10 M19 26 L27 10"
            stroke={accentColor}
            strokeWidth="2.6"
            strokeLinecap="round"
            fill="none"
          />
        </svg>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', lineHeight: 1 }}>
        <Typography
          sx={{
            fontFamily: '"Inter", system-ui, sans-serif',
            fontWeight: 600,
            fontSize: '1.05rem',
            letterSpacing: '-0.02em',
            lineHeight: 1,
            color: textColor,
          }}
        >
          myosin
        </Typography>
        <Typography
          sx={{
            fontFamily: '"IBM Plex Mono", monospace',
            fontWeight: 500,
            fontSize: '0.55rem',
            letterSpacing: '0.22em',
            textTransform: 'uppercase',
            color: accentColor,
            lineHeight: 1,
            mt: 0.4,
          }}
        >
          creative genflow
        </Typography>
      </Box>
    </Box>
  );
}

export default function AppBar() {
  const navigate = useNavigate();
  const { mode } = useColorScheme();

  return (
    <MuiAppBar
      position="static"
      color="default"
      elevation={0}
      sx={{ borderBottom: '1px solid rgba(6, 182, 212, 0.10)', boxShadow: 'none' }}
    >
      <Toolbar
        sx={{
          justifyContent: 'space-between',
          py: 1.5,
          px: { xs: 2, sm: 3 },
          minHeight: 'auto !important',
        }}
      >
        <Box sx={{ width: 40 }} />

        <Box
          sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}
          onClick={() => navigate('/')}
        >
          <MyosinWordmark mode={mode ?? 'dark'} />
        </Box>

        <ThemeToggle />
      </Toolbar>
    </MuiAppBar>
  );
}
