import { useEffect, useRef } from 'react'
import { ScanLine, X } from 'lucide-react'

export default function ActionConfirmModal({
  title,
  description,
  confirmLabel,
  onConfirm,
  onClose,
}) {
  const confirmButtonRef = useRef(null)
  const dialogRef = useRef(null)
  const previouslyFocusedRef = useRef(null)

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose()
        return
      }
      if (event.key !== 'Tab') return

      const focusable = dialogRef.current?.querySelectorAll(
        'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
      )
      if (!focusable?.length) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    previouslyFocusedRef.current = document.activeElement
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', handleKeyDown)
    confirmButtonRef.current?.focus()

    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
      previouslyFocusedRef.current?.focus?.()
    }
  }, [onClose])

  return (
    <div
      className="action-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="action-modal"
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="action-modal-title"
        aria-describedby="action-modal-description"
      >
        <button
          className="action-modal__close"
          type="button"
          onClick={onClose}
          aria-label="Close confirmation"
        >
          <X size={17} />
        </button>
        <div className="action-modal__icon">
          <ScanLine size={21} />
        </div>
        <span className="action-modal__eyebrow">INSPECTION WORKSPACE</span>
        <h2 className="action-modal__title" id="action-modal-title">{title}</h2>
        <p className="action-modal__description" id="action-modal-description">{description}</p>
        <div className="action-modal__actions">
          <button className="btn btn--ghost" type="button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn--primary"
            type="button"
            onClick={onConfirm}
            ref={confirmButtonRef}
          >
            <ScanLine size={15} />
            {confirmLabel}
          </button>
        </div>
      </section>
    </div>
  )
}
