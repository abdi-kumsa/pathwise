import { useEffect, useRef } from 'react'

/**
 * Dialog used by the admin console forms.
 *
 * Escape closes, scrim click closes, focus moves in on open and returns to
 * whatever opened it on close, and Tab is trapped inside — otherwise keyboard
 * users tab straight out into the page behind the scrim and lose the dialog.
 */
export default function Modal({ open, title, subtitle, onClose, children, width = 460 }) {
  const panelRef = useRef(null)
  const restoreRef = useRef(null)

  useEffect(() => {
    if (!open) return

    restoreRef.current = document.activeElement

    // Focus the first input so the dialog is usable without reaching for a
    // mouse. Fields are looked up before buttons rather than in one combined
    // selector: querySelector returns the first match in document order, and
    // the close button precedes the form, so a combined selector would land
    // the caret on "Close" every time.
    requestAnimationFrame(() => {
      const panel = panelRef.current
      if (!panel) return
      const target =
        panel.querySelector('input:not([disabled]), select:not([disabled]), textarea:not([disabled])')
        ?? panel.querySelector('button:not([disabled])')
      target?.focus()
    })

    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
        return
      }
      if (e.key !== 'Tab') return

      const focusable = panelRef.current?.querySelectorAll(
        'input:not([disabled]), select:not([disabled]), textarea, button:not([disabled]), [href]'
      )
      if (!focusable?.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', onKey)
    // Stop the page behind from scrolling under the dialog.
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
      restoreRef.current?.focus?.()
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-scrim" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div
        ref={panelRef}
        className="modal-panel"
        style={{ maxWidth: width }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="modal-head">
          <div style={{ minWidth: 0 }}>
            <p className="modal-title">{title}</p>
            {subtitle && <p className="modal-sub">{subtitle}</p>}
          </div>
          <button className="modal-x" onClick={onClose} aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                 strokeLinecap="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </header>

        <div className="modal-body">{children}</div>
      </div>

      <style>{`
        .modal-scrim {
          position: fixed; inset: 0; z-index: 120;
          background: rgba(15, 23, 42, 0.45);
          display: flex; align-items: flex-start; justify-content: center;
          padding: 8vh 16px 16px; overflow-y: auto;
        }
        .modal-panel {
          width: 100%; background: var(--white); border-radius: 14px;
          box-shadow: var(--shadow-pop); overflow: hidden;
        }
        .modal-head {
          display: flex; align-items: flex-start; gap: 12px;
          padding: 18px 20px 14px; border-bottom: 1px solid var(--border);
        }
        .modal-title {
          font-family: 'Sora', sans-serif; font-size: 15px;
          font-weight: 600; color: var(--navy);
        }
        .modal-sub { font-size: 12.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.5; }
        .modal-x {
          margin-left: auto; background: none; border: none; cursor: pointer;
          color: var(--text-muted); padding: 4px; border-radius: 6px;
          display: flex; flex-shrink: 0;
        }
        .modal-x svg { width: 17px; height: 17px; }
        .modal-x:hover { color: var(--navy); background: var(--page); }
        .modal-body { padding: 18px 20px 20px; }

        /* Shared form styling for dialog contents */
        .mf-label {
          display: block; font-size: 12px; font-weight: 600;
          color: var(--navy); margin-bottom: 6px;
        }
        .mf-input, .mf-select {
          width: 100%; font-size: 13.5px; padding: 9px 11px;
          border: 1px solid var(--border); border-radius: 9px;
          color: var(--navy); background: var(--white); font-family: inherit;
          margin-bottom: 14px;
        }
        .mf-input:focus, .mf-select:focus {
          outline: none; border-color: var(--blue);
          box-shadow: 0 0 0 3px var(--blue-light);
        }
        .mf-hint { font-size: 11.5px; color: var(--text-muted); margin: -10px 0 14px; }
        .mf-error {
          font-size: 12.5px; color: var(--red); background: var(--red-bg);
          border-radius: 8px; padding: 9px 11px; margin-bottom: 14px; line-height: 1.5;
        }
        .mf-ok {
          font-size: 12.5px; color: var(--green); background: var(--green-bg);
          border-radius: 8px; padding: 9px 11px; margin-bottom: 14px;
        }
        .mf-actions {
          display: flex; gap: 9px; justify-content: flex-end;
          padding-top: 4px;
        }
        .mf-btn {
          padding: 9px 16px; border-radius: 9px; font-size: 13.5px;
          font-weight: 600; font-family: 'Sora', sans-serif; cursor: pointer;
          border: 1px solid var(--border); background: var(--white); color: var(--navy);
        }
        .mf-btn:hover:not(:disabled) { background: var(--page); }
        .mf-btn-primary { background: var(--blue); border-color: var(--blue); color: #fff; }
        .mf-btn-primary:hover:not(:disabled) { background: #2563EB; }
        .mf-btn-danger { background: var(--red); border-color: var(--red); color: #fff; }
        .mf-btn:disabled { opacity: .55; cursor: not-allowed; }
      `}</style>
    </div>
  )
}
