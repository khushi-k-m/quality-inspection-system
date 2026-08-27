import { useEffect, useState } from 'react'
import Header from '../components/Header'
import Loading from '../components/Loading'
import apiClient from '../api/apiClient'
import { Settings as SettingsIcon, Info } from 'lucide-react'

export default function Settings() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/health')
      .then(r => setHealth(r.data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <Header title="Settings" />
      <div className="page__body">
        <div className="card">
          <h3 className="card__title"><SettingsIcon size={16} /> System Information</h3>
          <div className="settings-info">
            <Info size={16} />
            <p>
              Camera, model, and inspection settings are configured in the backend.
              Edit <code>backend/services/material_registry.py</code> to add new materials or adjust model paths.
            </p>
          </div>

          {loading && <Loading text="Loading system info..." />}

          {!loading && health && (
            <div className="settings-grid" style={{ marginTop: 18 }}>
              <div className="settings-item">
                <span className="settings-label">Backend Status</span>
                <span className="settings-value" style={{ color: health.status === 'online' ? 'var(--green)' : 'var(--red)' }}>
                  {health.status}
                </span>
              </div>
              <div className="settings-item">
                <span className="settings-label">Steel Database</span>
                <span className="settings-value" style={{ color: health.database_steel === 'online' ? 'var(--green)' : 'var(--red)' }}>
                  {health.database_steel}
                </span>
              </div>
              <div className="settings-item">
                <span className="settings-label">Metal Database</span>
                <span className="settings-value" style={{ color: health.database_metal === 'online' ? 'var(--green)' : 'var(--red)' }}>
                  {health.database_metal}
                </span>
              </div>
              <div className="settings-item">
                <span className="settings-label">Camera</span>
                <span className="settings-value" style={{ color: health.camera === 'connected' ? 'var(--green)' : 'var(--amber)' }}>
                  {health.camera}
                </span>
              </div>
              {health.models && Object.entries(health.models).map(([mat, status]) => (
                <div key={mat} className="settings-item">
                  <span className="settings-label">{mat.charAt(0).toUpperCase() + mat.slice(1)} Model</span>
                  <span className="settings-value" style={{ color: status === 'ready' ? 'var(--green)' : 'var(--red)' }}>
                    {status}
                  </span>
                </div>
              ))}
              <div className="settings-item">
                <span className="settings-label">Report Format</span>
                <span className="settings-value">PDF (ReportLab)</span>
              </div>
              <div className="settings-item">
                <span className="settings-label">Detection Engine</span>
                <span className="settings-value">YOLOv8</span>
              </div>
            </div>
          )}

          {!loading && !health && (
            <p className="empty-text" style={{ marginTop: 16 }}>
              Unable to connect to backend. Start the server to view system information.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
