import { createTheme } from '@mui/material/styles';

// ─────────────────────────────────────────
// Myosin Executive Cockpit — Design Tokens
// Aligned with ops.myosin.io brand language.
// ─────────────────────────────────────────
// Primary  Cyan         #06b6d4 → #22d3ee → #67e8f9
// Accent   Electric Blue #0066FF
// Surface  Deep Navy    #020617 → #0B0E11 → #12161B
// Status   Amber #f59e0b · Emerald #10b981 · Red #ef4444 · Yellow #eab308

export const theme = createTheme({
  cssVariables: {
    colorSchemeSelector: 'class',
  },
  colorSchemes: {
    // Dark is the primary/default experience
    dark: {
      palette: {
        primary: {
          main: '#06b6d4',
          light: '#67e8f9',
          dark: '#0891b2',
          contrastText: '#020617',
        },
        secondary: {
          main: '#0066FF',
          light: '#3b82f6',
          dark: '#0050CC',
          contrastText: '#FFFFFF',
        },
        success: {
          main: '#10b981',
          light: '#052E1E',
          dark: '#059669',
        },
        warning: {
          main: '#f59e0b',
          light: '#2D1F02',
          dark: '#d97706',
        },
        error: {
          main: '#ef4444',
          light: '#2D0A0A',
          dark: '#dc2626',
        },
        info: {
          main: '#22d3ee',
          light: '#67e8f9',
          dark: '#06b6d4',
        },
        background: {
          default: '#020617',
          paper: '#0B0E11',
        },
        text: {
          primary: '#E8EEF5',
          secondary: '#8A95A5',
          disabled: '#5A6473',
        },
        divider: 'rgba(6, 182, 212, 0.12)',
      },
    },
    light: {
      palette: {
        primary: {
          main: '#0891b2',
          light: '#CFFAFE',
          dark: '#0E7490',
          contrastText: '#FFFFFF',
        },
        secondary: {
          main: '#0066FF',
          light: '#DBEAFE',
          dark: '#1E40AF',
          contrastText: '#FFFFFF',
        },
        success: { main: '#10b981', light: '#D1FAE5' },
        warning: { main: '#f59e0b', light: '#FEF3C7' },
        error:   { main: '#ef4444', light: '#FEE2E2' },
        info:    { main: '#22d3ee', light: '#CFFAFE' },
        background: {
          default: '#F4F8FB',
          paper: '#FFFFFF',
        },
        text: {
          primary: '#0B0E11',
          secondary: '#5A6473',
        },
        divider: 'rgba(6, 182, 212, 0.14)',
      },
    },
  },
  typography: {
    fontFamily: '"Inter", system-ui, -apple-system, sans-serif',
    h1: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 800,
      letterSpacing: '-0.035em',
    },
    h2: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 800,
      letterSpacing: '-0.03em',
    },
    h3: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h4: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h5: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 600,
      letterSpacing: '-0.015em',
    },
    h6: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    body1: {
      fontFamily: '"Inter", system-ui, sans-serif',
      letterSpacing: '-0.005em',
    },
    body2: {
      fontFamily: '"Inter", system-ui, sans-serif',
      letterSpacing: '-0.005em',
    },
    button: {
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 600,
      letterSpacing: '0.005em',
      textTransform: 'none' as const,
    },
    caption: {
      fontFamily: '"IBM Plex Mono", "JetBrains Mono", monospace',
      letterSpacing: '0.04em',
      fontSize: '0.72rem',
    },
    overline: {
      fontFamily: '"IBM Plex Mono", "JetBrains Mono", monospace',
      letterSpacing: '0.20em',
      fontWeight: 500,
      textTransform: 'uppercase',
      fontSize: '0.65rem',
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none' as const,
          fontWeight: 600,
          boxShadow: 'none',
          padding: '8px 18px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: '0 4px 14px rgba(6, 182, 212, 0.30)',
            transform: 'translateY(-1px)',
          },
          '&:active': { transform: 'translateY(0)' },
        },
        containedPrimary: {
          background: '#06b6d4',
          color: '#020617',
          border: '1px solid #22d3ee',
          '&:hover': {
            background: '#22d3ee',
            boxShadow: '0 6px 20px rgba(6, 182, 212, 0.45)',
          },
        },
        containedSecondary: {
          background: 'linear-gradient(135deg, #0066FF 0%, #06b6d4 100%)',
          color: '#FFFFFF',
          border: '1px solid rgba(34, 211, 238, 0.45)',
          '&:hover': {
            background: 'linear-gradient(135deg, #1A75FF 0%, #22d3ee 100%)',
            boxShadow: '0 6px 22px rgba(0, 102, 255, 0.40)',
          },
        },
        outlinedPrimary: {
          borderColor: 'rgba(6, 182, 212, 0.45)',
          color: '#22d3ee',
          '&:hover': {
            borderColor: '#22d3ee',
            backgroundColor: 'rgba(6, 182, 212, 0.08)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 14,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: 'none',
          transition: 'border-color 0.25s ease, box-shadow 0.25s ease',
          backgroundImage: 'none',
          ...theme.applyStyles('dark', {
            backgroundColor: '#0B0E11',
            '&:hover': {
              borderColor: 'rgba(6, 182, 212, 0.28)',
              boxShadow: '0 0 0 1px rgba(6, 182, 212, 0.10), 0 14px 36px rgba(0, 0, 0, 0.45)',
            },
          }),
          ...theme.applyStyles('light', {
            backgroundColor: '#FFFFFF',
            '&:hover': {
              borderColor: 'rgba(6, 182, 212, 0.32)',
              boxShadow: '0 10px 28px rgba(6, 182, 212, 0.10)',
            },
          }),
        }),
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 14,
          boxShadow: 'none',
          backgroundImage: 'none',
          border: `1px solid ${theme.palette.divider}`,
          ...theme.applyStyles('dark', {
            backgroundColor: '#0B0E11',
          }),
          ...theme.applyStyles('light', {
            backgroundColor: '#FFFFFF',
          }),
        }),
      },
    },
    MuiChip: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 6,
          fontWeight: 500,
          fontFamily: '"IBM Plex Mono", "JetBrains Mono", monospace',
          letterSpacing: '0.02em',
          fontSize: '0.72rem',
          ...theme.applyStyles('dark', {
            backgroundColor: 'rgba(6, 182, 212, 0.10)',
            color: '#67e8f9',
            border: '1px solid rgba(6, 182, 212, 0.22)',
          }),
        }),
        outlined: ({ theme }) => ({
          ...theme.applyStyles('dark', {
            borderColor: 'rgba(6, 182, 212, 0.22)',
            color: '#8A95A5',
          }),
        }),
        filled: ({ theme }) => ({
          ...theme.applyStyles('dark', {
            backgroundColor: 'rgba(6, 182, 212, 0.16)',
            color: '#67e8f9',
            border: '1px solid rgba(6, 182, 212, 0.32)',
          }),
        }),
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined' as const },
      styleOverrides: {
        root: ({ theme }) => ({
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            transition: 'box-shadow 0.2s ease, background 0.2s ease',
            fontFamily: '"Inter", system-ui, sans-serif',
            '&.Mui-focused': {
              boxShadow: '0 0 0 3px rgba(6, 182, 212, 0.18)',
            },
            ...theme.applyStyles('dark', {
              backgroundColor: 'rgba(2, 6, 23, 0.55)',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(6, 182, 212, 0.22)',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(6, 182, 212, 0.45)',
              },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                borderColor: '#22d3ee',
              },
            }),
          },
        }),
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: ({ theme }) => ({
          backgroundColor: 'transparent',
          color: theme.palette.text.primary,
          boxShadow: 'none',
          backgroundImage: 'none',
          borderBottom: 'none',
        }),
      },
    },
    MuiStepConnector: {
      styleOverrides: {
        line: ({ theme }) => ({
          borderColor: theme.palette.divider,
          borderTopWidth: 1,
          borderRadius: 1,
          transition: 'border-color 0.4s ease',
        }),
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          height: 4,
          backgroundColor: 'rgba(6, 182, 212, 0.10)',
        },
        bar: {
          background: 'linear-gradient(90deg, #0066FF, #06b6d4, #22d3ee)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: ({ theme }) => ({
          '& .MuiTableCell-head': {
            fontWeight: 500,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            fontFamily: '"IBM Plex Mono", "JetBrains Mono", monospace',
            fontSize: '0.65rem',
          },
          ...theme.applyStyles('dark', {
            '& .MuiTableCell-head': {
              backgroundColor: '#12161B',
              color: '#8A95A5',
              borderBottom: '1px solid rgba(6, 182, 212, 0.12)',
            },
          }),
          ...theme.applyStyles('light', {
            '& .MuiTableCell-head': {
              backgroundColor: '#F0F9FB',
              color: '#5A6473',
            },
          }),
        }),
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 18px rgba(0, 0, 0, 0.35)',
        },
      },
    },
  },
});
