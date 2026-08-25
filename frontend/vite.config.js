import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      // Native filesystem events do not cross a Windows Docker bind mount, so
      // Vite keeps serving its cached transform after a file changes on the
      // host — edits appear to have no effect until the container is restarted.
      // Polling is the reliable path there. It costs a little CPU; correctness
      // of the dev loop is worth more.
      usePolling: true,
      interval: 300,
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
})
