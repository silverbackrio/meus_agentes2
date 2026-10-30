import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Host público do preview do Cloud. Ele muda a cada restauração do workspace,
// por isso vem de variável de ambiente com fallback para o host atual.
const previewHost =
  process.env.__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS ??
  'pv-ef7cc9fdece6-f6de514f-4a24-439d-9c9e-9517db2ad31a.style.dev'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [previewHost],
    proxy: {
      '/api': {
        // A 8000 está ocupada nesta máquina; o Django roda na 8901.
        target: 'http://localhost:8901',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
