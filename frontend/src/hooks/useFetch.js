import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Generic data-fetching hook.
 *
 * @param {Function} fetchFn  - Async function that returns the data (e.g. () => getMarketOverview())
 * @param {Array}    deps     - Dependency array — re-fetches whenever any dep changes (like useEffect)
 *
 * @returns {{ data, loading, error, refetch }}
 *   data     - The resolved value, or null before the first successful fetch
 *   loading  - true while a fetch is in flight
 *   error    - Error message string, or null when no error
 *   refetch  - Call this to manually trigger a fresh fetch (e.g. on Retry button click)
 */
export default function useFetch(fetchFn, deps = []) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  // Keep a stable ref to fetchFn so changing its identity between renders
  // does not trigger an extra fetch when deps haven't changed.
  const fetchRef = useRef(fetchFn)
  fetchRef.current = fetchFn

  // Incremented by refetch() to force a re-run without changing deps.
  const [tick, setTick] = useState(0)

  const run = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchRef.current()
      setData(result)
    } catch (e) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [tick, ...deps]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { run() }, [run])

  const refetch = useCallback(() => setTick(t => t + 1), [])

  return { data, loading, error, refetch }
}
