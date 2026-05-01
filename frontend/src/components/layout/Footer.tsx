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
        backgroundColor: 'background.default',
        borderTop: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Powered by Gemini 1.5 Pro + Veo 3.1
      </Typography>
    </Box>
  );
}
