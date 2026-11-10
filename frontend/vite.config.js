import { execSync } from 'node:child_process'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Short commit shown in the app footer. CI and Render expose the commit as an
// environment variable; a local checkout asks git; a Docker build without
// .git falls back to 'dev' unless VITE_BUILD_SHA is passed as a build arg.
function buildSha() {
  const fromEnv = process.env.VITE_BUILD_SHA || process.env.RENDER_GIT_COMMIT || process.env.GITHUB_SHA
  if (fromEnv) return fromEnv.slice(0, 7)
  try {
    return execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()
  } catch {
    return 'dev'
  }
}

export default defineConfig({
  plugins: [react()],
  define: { __BUILD_SHA__: JSON.stringify(buildSha()) },
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
