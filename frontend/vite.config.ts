import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/studio': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/generate': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/jobs': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/videos': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/dashboard': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
