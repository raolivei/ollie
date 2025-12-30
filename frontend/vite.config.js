import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    }
  },
  preview: {
    allowedHosts: [
      'ollie.eldertree.local',
      'pihole.eldertree.local',
      'grafana.eldertree.local',
      'prometheus.eldertree.local',
      'vault.eldertree.local',
      'flux-ui.eldertree.local',
      'localhost',
    ],
  },
})

