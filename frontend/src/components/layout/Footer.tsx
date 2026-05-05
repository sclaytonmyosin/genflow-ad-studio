import { Box, Typography } from '@mui/material';

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        mt: 'auto',
        py: 3,
        px: 2,
        textAlign: 'center',
        borderTop: '1px solid rgba(6, 182, 212, 0.10)',
      }}
    >
      <Typography
        variant="caption"
        sx={{
          display: 'block',
          fontFamily: '"IBM Plex Mono", monospace',
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          color: '#22d3ee',
          fontWeight: 500,
          fontSize: '0.62rem',
        }}
      >
        myosin · executive cockpit
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{
          mt: 0.5,
          display: 'block',
          fontSize: '0.65rem',
          fontFamily: '"IBM Plex Mono", monospace',
          letterSpacing: '0.05em',
          opacity: 0.55,
        }}
      >
        creative genflow · gemini 3 pro · imagen 4 · veo 3.1
      </Typography>
    </Box>
  );
}
