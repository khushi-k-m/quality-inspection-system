import { useAuth } from '../context/AuthContext'
import { User, Shield, Clock } from 'lucide-react'

export default function Profile() {
  const { user } = useAuth()
  const initial = user?.username?.[0]?.toUpperCase() || 'U'

  return (
    <div className="page-content">
      <div className="glass-card" style={{ padding: 28, maxWidth: 560, display: 'flex', alignItems: 'center', gap: 24 }}>
        <div className="profile-avatar">{initial}</div>
        <div style={{ flex: 1 }}>
          {[
            { icon: User,   label: 'Username', value: user?.username },
            { icon: Shield, label: 'Role',     value: user?.role || 'operator' },
            { icon: Clock,  label: 'Session',  value: 'Active' },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="detail-row">
              <span className="detail-row__label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Icon size={13} /> {label}
              </span>
              <span style={{ fontWeight: 600 }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
