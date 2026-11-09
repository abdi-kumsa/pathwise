import { useEffect, useState } from 'react'

/**
 * Return `value` once it has stopped changing for `delay` ms.
 *
 * Used by the policy simulator so dragging a slider sends one scenario run
 * when the user lets go, not one per step. Each run is audited server-side
 * (SCOPE.MOE.R3), so an undebounced slider would flood the audit log and trip
 * the per-user rate limit.
 */
export default function useDebounced(value, delay = 400) {
  const [settled, setSettled] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return settled
}
