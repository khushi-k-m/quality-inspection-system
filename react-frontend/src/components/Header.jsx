import { useEffect, useState } from 'react'
import { Bell, Wifi, WifiOff } from 'lucide-react'
import apiClient from '../api/apiClient'

export default function Header({ title }) {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const check = () =>
      apiClient.get('/health').then(r => setHealth(r.data)).catch(() => setHealth(null))
    check()
    const id = setInterval(check, 15000)
    return () => clearInterval(id)
  }, [])

  const online = health?.status === 'online'

  return (
    <header className="header">
      <h1 className="header__title">{title}</h1>
      <div className="header__right">
        <div className={`header__status ${online ? 'header__status--online' : 'header__status--offline'}`}>
          {online ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span>{online ? 'Backend Online' : 'Backend Offline'}</span>
        </div>
        {health && (
          <div className="header__health-pills">
            <span className={`pill ${health.database === 'online' ? 'pill--green' : 'pill--red'}`}>
              DB
            </span>
            <span className={`pill ${health.model === 'ready' ? 'pill--green' : 'pill--red'}`}>
              AI
            </span>
            <span className={`pill ${health.camera === 'connected' ? 'pill--green' : 'pill--yellow'}`}>
              CAM
            </span>
          </div>
        )}
        <button className="header__icon-btn"><Bell size={18} /></button>
      </div>
    </header>
  )
}
