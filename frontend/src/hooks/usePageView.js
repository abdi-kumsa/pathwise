import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import client, { getToken } from '../api/client'

const LEFTOVER = new Set([
  '/student/careers', '/student/evaluator', '/student/salary', '/student/market',
  '/university/expansion', '/university/benchmark', '/university/enrollment',
  '/moe/fields', '/moe/quadrant', '/moe/labour',
  '/mol/emerging', '/mol/supply-demand', '/mol/regional',
])

/** DOC2 W.ADM.08 — one page_view audit row per widget-route visit. */
export default function usePageView() {
  const location = useLocation()
  useEffect(() => {
    const path = location.pathname
    if (!path || path === '/login' || path === '/signup' || LEFTOVER.has(path)) return
    if (!getToken()) return
    client.post('/api/auth/page-view', { path }).catch(() => {})
  }, [location.pathname])
}
