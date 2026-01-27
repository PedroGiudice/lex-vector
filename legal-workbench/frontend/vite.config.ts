import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Detect Tauri environment
const isTauri = !!process.env.TAURI_ENV_PLATFORM;
const port = isTauri ? 1420 : 3000;

// https://vitejs.dev/config/
export default defineConfig({
  base: '/', // Root path - React is the only frontend
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port,
    host: true,
    strictPort: true,
    // Proxies only active in web mode (not Tauri)
    proxy: isTauri
      ? undefined
      : {
          // Claude Code UI backend (WebSocket for chat)
          '/ws': {
            target: 'ws://localhost:3002',
            ws: true,
            changeOrigin: true,
          },
          // Claude Code UI auth routes
          '/api/auth': {
            target: 'http://localhost:3002',
            changeOrigin: true,
          },
          // FastAPI backends
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
          },
        },
  },
  // Required for Tauri
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Tauri requires ES2021 target for WebView
    target: isTauri ? ['es2021', 'chrome100', 'safari13'] : 'esnext',
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
  },
});
