import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE || 'http://localhost:8000'

  const proxy = {
    '/v1': { target: apiBase, changeOrigin: true },
    '/healthz': { target: apiBase, changeOrigin: true },
    '/readyz': { target: apiBase, changeOrigin: true },
    '/metrics': { target: apiBase, changeOrigin: true },
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: true,
      proxy,
    },
    preview: {
      port: 5173,
      host: true,
      proxy,
    },
    build: {
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom'],
            charts: ['recharts'],
          },
        },
      },
    },
  }
})
