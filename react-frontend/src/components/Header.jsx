import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Wifi, WifiOff, Bell } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/apiClient'

const PAGE_META = {
  '/home':               { title: 'Home',               desc: 'Overview of the AI inspection system' },
  '/dashboard':          { title: 'Dashboard',          desc: 'Real-time inspection metrics and statistics' },
  '/inspection':         { title: 'Inspection',         desc: 'Run AI-powered defect detection on products' },
  '/analysis':           { title: 'Analysis',           desc: 'Explore historical inspection analytics' },
  '/inspection-history': { title: 'Inspection History', desc: 'Review and filter past inspection records' },
  '/reports':            { title: 'Reports',            desc: 'Generate, view, and export inspection reports' },
  '/help':               { title: 'Help',               desc: 'Guides, FAQs and troubleshooting' },
  '/settings':           { title: 'Settings',           desc: 'System information and configuration' },
  '/profile':            { title: 'User Profile',       desc: 'Account details and session settings' },
}

export default function Header() {
  const { user } = useAuth()
  const [health, setHealth] = useState(null)
  const location = useLocation()
  const meta = PAGE_META[location.pathname] || { title: 'Inspection System', desc: '' }

  useEffect(() => {
    const check = () => apiClient.get('/health').then(r => setHealth(r.data)).catch(() => setHealth(null))
    check()
    const id = setInterval(check, 20000)
    return () => clearInterval(id)
  }, [])

  const online = health?.status === 'online'
  const initial = user?.username?.[0]?.toUpperCase() || 'U'

  return (
    <header className="topbar">
      <div className="topbar__left">
        <h1 className="topbar__title">{meta.title}</h1>
        {meta.desc && <p className="topbar__desc">{meta.desc}</p>}
      </div>
      <div className="topbar__right">
        <div className={`topbar__status ${online ? 'topbar__status--on' : 'topbar__status--off'}`}>
          {online ? <Wifi size={13} /> : <WifiOff size={13} />}
          <span>{online ? 'Online' : 'Offline'}</span>
        </div>
        <button className="topbar__icon-btn" aria-label="Notifications">
          <Bell size={16} />
        </button>
        <div className="topbar__avatar" title={user?.username}>{initial}</div>
      </div>
    </header>
  )
}
