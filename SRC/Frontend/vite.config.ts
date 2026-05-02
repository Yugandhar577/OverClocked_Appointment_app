import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

/**
 * Browser → Vite (5173) → backend. In Docker, `localhost:8000` from the browser often fails
 * (or hits the wrong process); the service hostname `backend` only resolves inside the compose network.
 */
const backendProxyTarget = process.env.BACKEND_PROXY_TARGET ?? "http://127.0.0.1:8000"

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: backendProxyTarget,
        changeOrigin: true,
      },
    },
  },
})
