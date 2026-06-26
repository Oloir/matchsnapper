import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3070,
    proxy: {
      '/api': {
        target: 'http://localhost:9070',
        changeOrigin: true,
      },
    },
  },
})
