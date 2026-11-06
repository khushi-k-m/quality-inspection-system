export default function StatCard({ label, value, icon: Icon, color, sub }) {
  return (
    <div className="stat-card" style={{ '--sc': color }}>
      <div className="stat-card__top">
        <span className="stat-card__label">{label}</span>
        <div className="stat-card__icon" style={{ background: `${color}1a`, border: `1px solid ${color}33` }}>
          <Icon size={15} style={{ color }} />
        </div>
      </div>
      <span className="stat-card__value">{value ?? '—'}</span>
      {sub && <span className="stat-card__sub">{sub}</span>}
      <div className="stat-card__glow" />
    </div>
  )
}
