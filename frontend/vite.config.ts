import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Subpath deploys (e.g. ops.myosin.io/genflow) set VITE_BASE_PATH at build
// time so all asset URLs and import.meta.env.BASE_URL are correctly prefixed.
// Local dev defaults to "/".
const basePath = process.env.VITE_BASE_PATH || '/'

export default defineConfig({
  base: basePath,
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/output': 'http://localhost:8000',
      '/asset': 'http://localhost:8000',
    },
  },
})
