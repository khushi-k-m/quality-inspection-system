import { AlertTriangle } from 'lucide-react'

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="error-message">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <AlertTriangle size={16} />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button className="btn btn--sm btn--ghost" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
