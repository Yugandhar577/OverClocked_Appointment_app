import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/** Standalone payments UI: 5174 by default so it does not clash with the main app on 5173. */
const apiPort = process.env.PAYMENTS_API_PORT ?? "8888";
const devPort = Number(process.env.PAYMENTS_UI_PORT ?? "5174");

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: devPort,
    strictPort: true,
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
      },
      "/health": {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
      },
    },
  },
});
