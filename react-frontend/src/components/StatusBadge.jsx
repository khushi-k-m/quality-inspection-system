const S = {
  PASS:               { bg: 'rgba(34,197,94,.13)',   c: '#4ade80', b: 'rgba(34,197,94,.28)' },
  REWORK:             { bg: 'rgba(251,146,60,.13)',  c: '#fb923c', b: 'rgba(251,146,60,.28)' },
  FAIL:               { bg: 'rgba(248,113,113,.13)', c: '#f87171', b: 'rgba(248,113,113,.28)' },
  NONE:               { bg: 'rgba(148,163,184,.08)', c: '#94a3b8', b: 'rgba(148,163,184,.2)' },
  LOW:                { bg: 'rgba(34,197,94,.13)',   c: '#4ade80', b: 'rgba(34,197,94,.28)' },
  MEDIUM:             { bg: 'rgba(251,146,60,.13)',  c: '#fb923c', b: 'rgba(251,146,60,.28)' },
  HIGH:               { bg: 'rgba(248,113,113,.13)', c: '#f87171', b: 'rgba(248,113,113,.28)' },
  CRITICAL:           { bg: 'rgba(239,68,68,.18)',   c: '#ef4444', b: 'rgba(239,68,68,.4)' },
  IDLE:               { bg: 'rgba(100,116,139,.08)', c: '#64748b', b: 'rgba(100,116,139,.2)' },
  INVALID_IMAGE:      { bg: 'rgba(251,146,60,.13)',  c: '#fb923c', b: 'rgba(251,146,60,.28)' },
  INVALID_MATERIAL:   { bg: 'rgba(248,113,113,.13)', c: '#f87171', b: 'rgba(248,113,113,.28)' },
  MATERIAL_UNVERIFIED:{ bg: 'rgba(251,146,60,.13)',  c: '#fb923c', b: 'rgba(251,146,60,.28)' },
}

export default function StatusBadge({ value }) {
  const s = S[value] || S.NONE
  return (
    <span className="sbadge" style={{ background: s.bg, color: s.c, border: `1px solid ${s.b}` }}>
      <span className="sbadge__dot" style={{ background: s.c }} />
      {value}
    </span>
  )
}
