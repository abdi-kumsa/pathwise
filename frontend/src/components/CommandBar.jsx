import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { globalSearch } from '../api/roles'

const KIND_LABEL = {
  occupation:  'Occupation',
  field:       'Field',
  program:     'Programme',
  institution: 'Institution',
}

/**
 * Global search, opened with Ctrl/Cmd-K.
 *
 * Results come from /api/search, which filters by the caller's role on the
 * server — a student is never sent institution records to begin with, so there
 * is nothing here to hide client-side.
 */
export default function CommandBar() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [cursor, setCursor] = useState(0)
  const [loading, setLoading] = useState(false)

  const inputRef = useRef(null)
  const navigate = useNavigate()

  // ── Global shortcut ─────────────────────────────────────────────────────────
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen(o => !o)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    if (open) {
      setQuery('')
      setResults([])
      setCursor(0)
      // Focus after the dialog paints, or the caret lands nowhere.
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  // ── Debounced search ────────────────────────────────────────────────────────
  useEffect(() => {
    const q = query.trim()
    if (!q) {
      setResults([])
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)

    const timer = setTimeout(async () => {
      try {
        const data = await globalSearch(q, 12)
        if (!cancelled) {
          setResults(data.results ?? [])
          setCursor(0)
        }
      } catch {
        if (!cancelled) setResults([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 180)

    return () => { cancelled = true; clearTimeout(timer) }
  }, [query])

  const choose = useCallback((result) => {
    if (!result) return
    setOpen(false)
    navigate(result.route)
  }, [navigate])

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setCursor(c => Math.min(c + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setCursor(c => Math.max(c - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      choose(results[cursor])
    }
  }

  return (
    <>
      <button className="cmd-trigger" onClick={() => setOpen(true)} aria-label="Search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
             strokeLinecap="round">
          <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
        </svg>
        <span className="cmd-trigger-text">Search…</span>
        <kbd className="cmd-kbd">Ctrl K</kbd>
      </button>

      {open && (
        <div className="cmd-overlay" onClick={() => setOpen(false)}>
          <div className="cmd-panel" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true">
            <div className="cmd-input-row">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                   strokeLinecap="round" className="cmd-input-icon">
                <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
              </svg>
              <input
                ref={inputRef}
                className="cmd-input"
                placeholder="Search occupations, fields, programmes…"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
              />
              <kbd className="cmd-kbd">Esc</kbd>
            </div>

            <div className="cmd-results">
              {loading && <p className="cmd-hint">Searching…</p>}

              {!loading && query.trim() && results.length === 0 && (
                <p className="cmd-hint">No matches for “{query.trim()}”.</p>
              )}

              {!loading && !query.trim() && (
                <p className="cmd-hint">
                  Type to search. Results are scoped to what your role can open.
                </p>
              )}

              {results.map((r, i) => (
                <button
                  key={`${r.kind}-${r.label}`}
                  className={`cmd-result${i === cursor ? ' active' : ''}`}
                  onMouseEnter={() => setCursor(i)}
                  onClick={() => choose(r)}
                >
                  <span className={`cmd-kind cmd-kind-${r.kind}`}>{KIND_LABEL[r.kind] ?? r.kind}</span>
                  <span className="cmd-label">{r.label}</span>
                  <span className="cmd-sublabel">{r.sublabel}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <style>{`
        .cmd-trigger {
          display: flex; align-items: center; gap: 8px;
          background: var(--white); border: 1px solid var(--border);
          border-radius: 10px; padding: 8px 10px 8px 12px;
          cursor: pointer; color: var(--text-muted); font-family: inherit;
          font-size: 13px; min-width: 240px; transition: border-color .15s ease;
        }
        .cmd-trigger:hover { border-color: var(--blue); }
        .cmd-trigger svg { width: 15px; height: 15px; flex-shrink: 0; }
        .cmd-trigger-text { flex: 1; text-align: left; }
        .cmd-kbd {
          font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 10.5px;
          color: var(--text-muted); background: var(--page);
          border: 1px solid var(--border); border-radius: 5px; padding: 2px 6px;
        }
        .cmd-overlay {
          position: fixed; inset: 0; background: rgba(15,23,42,0.45);
          z-index: 100; display: flex; align-items: flex-start;
          justify-content: center; padding: 12vh 16px 16px;
        }
        .cmd-panel {
          width: 100%; max-width: 580px; background: var(--white);
          border-radius: 14px; box-shadow: var(--shadow-pop); overflow: hidden;
        }
        .cmd-input-row {
          display: flex; align-items: center; gap: 10px;
          padding: 14px 16px; border-bottom: 1px solid var(--border);
        }
        .cmd-input-icon { width: 17px; height: 17px; color: var(--text-muted); flex-shrink: 0; }
        .cmd-input {
          flex: 1; border: none; outline: none; font-size: 15px;
          font-family: inherit; color: var(--navy); background: transparent;
        }
        .cmd-results { max-height: 340px; overflow-y: auto; padding: 6px; }
        .cmd-hint { font-size: 13px; color: var(--text-muted); padding: 18px 12px; text-align: center; }
        .cmd-result {
          width: 100%; display: flex; align-items: center; gap: 10px;
          padding: 9px 11px; border: none; background: none; border-radius: 8px;
          cursor: pointer; text-align: left; font-family: inherit;
        }
        .cmd-result.active { background: var(--blue-light); }
        .cmd-kind {
          font-size: 10px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 0.04em; border-radius: 5px; padding: 3px 7px;
          flex-shrink: 0; min-width: 78px; text-align: center;
        }
        .cmd-kind-occupation  { background: #EAF1FE; color: #2563EB; }
        .cmd-kind-field       { background: #E7F7F0; color: #0EA872; }
        .cmd-kind-program     { background: #FEF3C7; color: #B45309; }
        .cmd-kind-institution { background: #F1F5F9; color: #475569; }
        .cmd-label { font-size: 13.5px; color: var(--navy); font-weight: 500; }
        .cmd-sublabel {
          font-size: 12px; color: var(--text-muted); margin-left: auto;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 40%;
        }
        @media (max-width: 768px) {
          .cmd-trigger { min-width: 0; }
          .cmd-trigger-text, .cmd-trigger .cmd-kbd { display: none; }
          .cmd-overlay { padding: 8vh 12px 12px; }
          .cmd-sublabel { display: none; }
        }
      `}</style>
    </>
  )
}
