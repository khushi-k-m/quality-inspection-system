const STATUS_COLORS = {
  PASS: { bg: '#0d2e1a', color: '#22c55e', border: '#22c55e' },
  REWORK: { bg: '#2e1f0a', color: '#f97316', border: '#f97316' },
  FAIL: { bg: '#2e0a0a', color: '#ef4444', border: '#ef4444' },
  NONE: { bg: '#1a1f2e', color: '#94a3b8', border: '#334155' },
  LOW: { bg: '#0d2e1a', color: '#22c55e', border: '#22c55e' },
  MEDIUM: { bg: '#2e1f0a', color: '#f97316', border: '#f97316' },
  HIGH: { bg: '#2e1a0a', color: '#ef4444', border: '#ef4444' },
  CRITICAL: { bg: '#2e0a0a', color: '#dc2626', border: '#dc2626' },
  IDLE: { bg: '#1a1f2e', color: '#64748b', border: '#334155' },
}

export default function StatusBadge({ value }) {
  const style = STATUS_COLORS[value] || STATUS_COLORS.NONE
  return (
    <span
      className="status-badge"
      style={{
        background: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
      }}
    >
      {value}
    </span>
  )
}
