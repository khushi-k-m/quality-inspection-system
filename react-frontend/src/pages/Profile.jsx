import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import { User, Shield, Clock } from 'lucide-react'

export default function Profile() {
  const { user } = useAuth()

  const rows = [
    { icon: <User size={15} />, label: 'Username', value: user?.username },
    { icon: <Shield size={15} />, label: 'Role', value: user?.role },
    { icon: <Clock size={15} />, label: 'Session', value: 'Active' },
  ]

  return (
    <div className="page">
      <Header title="Profile" />
      <div className="page__body">
        <div className="card profile-card">
          <div className="profile-avatar" style={{ width: 64, height: 64, fontSize: 26 }}>
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="profile-info" style={{ flex: 1 }}>
            {rows.map(({ icon, label, value }) => (
              <div key={label} className="detail-row">
                <span style={{ display: 'flex', alignItems: 'center', gap: 7, color: 'var(--muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '.7px' }}>
                  {icon} {label}
                </span>
                <span style={{ fontWeight: 600 }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
