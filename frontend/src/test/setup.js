import '@testing-library/jest-dom'

// Recharts uses ResizeObserver — polyfill for jsdom
global.ResizeObserver = class ResizeObserver {
  observe()   {}
  unobserve() {}
  disconnect() {}
}

// Suppress noisy console.error from recharts SVG warnings in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (typeof args[0] === 'string' && args[0].includes('ResizeObserver')) return
    originalError(...args)
  }
})
afterAll(() => {
  console.error = originalError
})
