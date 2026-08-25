export default function StatCard({ label, value, icon: Icon, color, sub }) {
  return (
    <div className="stat-card" style={{ '--stat-color': color }}>
      <div className="stat-card__top">
        <span className="stat-card__label">{label}</span>
        <Icon size={18} style={{ color }} />
      </div>
      <span className="stat-card__value">{value ?? '—'}</span>
      {sub && <span className="stat-card__sub">{sub}</span>}
    </div>
  )
}
