import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import useFetch from '../hooks/useFetch'

// ─── helpers ─────────────────────────────────────────────────────────────────

const ok   = data => vi.fn().mockResolvedValue(data)
const fail = msg  => vi.fn().mockRejectedValue(new Error(msg))
const failAxios = (detail) => vi.fn().mockRejectedValue({ response: { data: { detail } } })

// ─── tests ───────────────────────────────────────────────────────────────────

describe('useFetch', () => {

  // ── Initial state ──────────────────────────────────────────────────────────

  it('starts with loading=true, data=null, error=null', () => {
    const fetchFn = () => new Promise(() => {}) // never resolves
    const { result } = renderHook(() => useFetch(fetchFn))
    expect(result.current.loading).toBe(true)
    expect(result.current.data).toBe(null)
    expect(result.current.error).toBe(null)
  })

  // ── Success path ───────────────────────────────────────────────────────────

  it('sets data and clears loading on successful fetch', async () => {
    const { result } = renderHook(() => useFetch(ok({ total: 42 })))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual({ total: 42 })
    expect(result.current.error).toBe(null)
  })

  it('works for array responses', async () => {
    const { result } = renderHook(() => useFetch(ok([1, 2, 3])))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual([1, 2, 3])
  })

  // ── Error paths ────────────────────────────────────────────────────────────

  it('sets error from plain Error message', async () => {
    const { result } = renderHook(() => useFetch(fail('network error')))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toBe(null)
    expect(result.current.error).toBe('network error')
  })

  it('extracts detail from Axios error response', async () => {
    const { result } = renderHook(() => useFetch(failAxios('Program not found')))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Program not found')
  })

  it('falls back to "Something went wrong" when error has no message', async () => {
    const fetchFn = vi.fn().mockRejectedValue({})
    const { result } = renderHook(() => useFetch(fetchFn))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Something went wrong')
  })

  // ── Refetch ────────────────────────────────────────────────────────────────

  it('refetch() re-runs the fetch and updates data', async () => {
    let call = 0
    const fetchFn = vi.fn().mockImplementation(() =>
      Promise.resolve({ count: ++call })
    )
    const { result } = renderHook(() => useFetch(fetchFn))
    await waitFor(() => expect(result.current.data).toEqual({ count: 1 }))

    act(() => result.current.refetch())
    await waitFor(() => expect(result.current.data).toEqual({ count: 2 }))
    expect(fetchFn).toHaveBeenCalledTimes(2)
  })

  it('refetch() resets error to null before re-fetching', async () => {
    let call = 0
    const fetchFn = vi.fn().mockImplementation(() => {
      call++
      return call === 1
        ? Promise.reject(new Error('first failure'))
        : Promise.resolve({ ok: true })
    })
    const { result } = renderHook(() => useFetch(fetchFn))
    await waitFor(() => expect(result.current.error).toBe('first failure'))

    act(() => result.current.refetch())
    await waitFor(() => expect(result.current.data).toEqual({ ok: true }))
    expect(result.current.error).toBe(null)
  })

  it('refetch() sets loading=true while re-fetching', async () => {
    let resolve
    const fetchFn = vi.fn()
      .mockResolvedValueOnce({ first: true })
      .mockImplementationOnce(() => new Promise(r => { resolve = r }))

    const { result } = renderHook(() => useFetch(fetchFn))
    await waitFor(() => expect(result.current.data).toEqual({ first: true }))

    act(() => result.current.refetch())
    await waitFor(() => expect(result.current.loading).toBe(true))

    act(() => resolve({ second: true }))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual({ second: true })
  })

  // ── Dep-change re-fetch ────────────────────────────────────────────────────

  it('re-fetches when deps array changes', async () => {
    let program = 'MS Data Science'
    const fetchFn = vi.fn().mockImplementation(() =>
      Promise.resolve({ program })
    )
    const { result, rerender } = renderHook(
      ({ p }) => useFetch(() => fetchFn(p), [p]),
      { initialProps: { p: 'MS Data Science' } }
    )
    await waitFor(() => expect(result.current.data).toEqual({ program: 'MS Data Science' }))

    program = 'MS AI'
    rerender({ p: 'MS AI' })
    await waitFor(() => expect(result.current.data).toEqual({ program: 'MS AI' }))
    expect(fetchFn).toHaveBeenCalledTimes(2)
  })

  it('does NOT re-fetch when deps are the same value', async () => {
    const fetchFn = vi.fn().mockResolvedValue({ data: 1 })
    const { rerender } = renderHook(
      ({ n }) => useFetch(fetchFn, [n]),
      { initialProps: { n: 5 } }
    )
    await waitFor(() => expect(fetchFn).toHaveBeenCalledTimes(1))
    rerender({ n: 5 })
    // give it a tick to see if it fires again
    await new Promise(r => setTimeout(r, 20))
    expect(fetchFn).toHaveBeenCalledTimes(1)
  })

  // ── fetchFn identity stability ─────────────────────────────────────────────

  it('does NOT re-fetch when fetchFn reference changes but deps stay the same', async () => {
    const fetchFn = vi.fn().mockResolvedValue(42)
    const { rerender } = renderHook(
      ({ fn }) => useFetch(fn, []),
      { initialProps: { fn: fetchFn } }
    )
    await waitFor(() => expect(fetchFn).toHaveBeenCalledTimes(1))
    // pass a new function reference with no dep change
    rerender({ fn: vi.fn().mockResolvedValue(99) })
    await new Promise(r => setTimeout(r, 20))
    expect(fetchFn).toHaveBeenCalledTimes(1)
  })
})
