import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import Loading from '../components/Loading'
import apiClient from '../api/apiClient'
import { Settings as SettingsIcon, User, Shield, Server, Cpu, LogOut } from 'lucide-react'

function Section({ icon: Icon, title, children }) {
  return (
    <div className="settings-section">
      <div className="settings-section__hdr">
        <Icon size={15} />
        <h3 className="settings-section__title">{title}</h3>
      </div>
      <div className="settings-section__body">{children}</div>
    </div>
  )
}

function Row({ label, value, valueColor }) {
  return (
    <div className="settings-row">
      <span className="settings-row__label">{label}</span>
      <span className="settings-row__value" style={valueColor ? { color: valueColor } : {}}>{value ?? '—'}</span>
    </div>
  )
}

export default function Settings() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/health')
      .then(r => setHealth(r.data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false))
  }, [])

  const handleLogout = async () => { await logout(); navigate('/login') }

  const statusColor = (v, good, warn) => {
    if (v === good) return '#4ade80'
    if (warn && v === warn) return '#fb923c'
    return '#f87171'
  }

  return (
    <div className="page-content">
      <div className="settings-grid">
        {/* Account */}
        <Section icon={User} title="Account">
          <Row label="Username" value={user?.username} />
          <Row label="Role"     value={user?.role || 'operator'} />
          <Row label="Session"  value="Active" valueColor="#4ade80" />
        </Section>

        {/* System */}
        <Section icon={Server} title="System Information">
          {loading && <Loading text="Loading system info…" />}
          {!loading && !health && <p className="empty-text">Unable to connect to backend.</p>}
          {!loading && health && (
            <>
              <Row label="Backend Status"   value={health.status}           valueColor={statusColor(health.status, 'online')} />
              <Row label="Steel Database"   value={health.database_steel}   valueColor={statusColor(health.database_steel, 'online')} />
              <Row label="Metal Database"   value={health.database_metal}   valueColor={statusColor(health.database_metal, 'online')} />
              <Row label="Fabric Database"  value={health.database_fabric}  valueColor={statusColor(health.database_fabric, 'online')} />
              <Row label="PCB Database"     value={health.database_pcb}     valueColor={statusColor(health.database_pcb, 'online')} />
              <Row label="Welding Database" value={health.database_welding} valueColor={statusColor(health.database_welding, 'online')} />
              <Row label="Camera"           value={health.camera}           valueColor={statusColor(health.camera, 'connected', 'disconnected')} />
            </>
          )}
        </Section>

        {/* AI Models */}
        <Section icon={Cpu} title="AI Models">
          {loading && <Loading text="Loading model status…" />}
          {!loading && health?.models && Object.entries(health.models).map(([mat, status]) => (
            <Row
              key={mat}
              label={`${mat.charAt(0).toUpperCase() + mat.slice(1)} Model`}
              value={status}
              valueColor={statusColor(status, 'ready')}
            />
          ))}
          {!loading && health && (
            <>
              <Row label="Detection Engine" value="YOLOv8" />
              <Row label="Report Format"    value="PDF (ReportLab)" />
            </>
          )}
        </Section>

        {/* Security */}
        <Section icon={Shield} title="Security">
          <p className="settings-info-text">
            Passwords are stored as PBKDF2 hashes. To change your password, use the Forgot Password flow from the login page.
          </p>
          <button className="btn btn--danger" style={{ marginTop: 16, width: '100%' }} onClick={handleLogout}>
            <LogOut size={14} /> Sign Out
          </button>
        </Section>
      </div>
    </div>
  )
}
