import { AlertTriangle, RefreshCw } from 'lucide-react'

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="err-msg">
      <div className="err-msg__left">
        <AlertTriangle size={14} />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button className="btn btn--sm btn--ghost" onClick={onRetry}>
          <RefreshCw size={12} /> Retry
        </button>
      )}
    </div>
  )
}
