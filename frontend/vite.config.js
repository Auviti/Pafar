import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Expose the server to the network
    allowedHosts: [
      '5173-auviti-pafar-jzva5zi5m4e.ws-eu118.gitpod.io', // Add your Gitpod host here
      'localhost', // Optional: Allow localhost as well
    ],
  },
})

