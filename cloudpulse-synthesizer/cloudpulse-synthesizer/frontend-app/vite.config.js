import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allows the cloud console to expose it
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // Points to your Uvicorn backend locally inside the VM
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
