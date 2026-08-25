import Header from '../components/Header'
import { Settings as SettingsIcon, Info } from 'lucide-react'

export default function Settings() {
  return (
    <div className="page">
      <Header title="Settings" />
      <div className="page__body">
        <div className="card">
          <h3 className="card__title"><SettingsIcon size={16} /> System Settings</h3>
          <div className="settings-info">
            <Info size={16} />
            <p>
              Camera, model, and inspection settings are configured in the backend.
              Edit <code>backend/auth.py</code> for credentials and
              <code>backend/services/camera_service.py</code> for camera/model settings.
            </p>
          </div>
          <div className="settings-grid">
            <div className="settings-item">
              <span className="settings-label">Confidence Threshold</span>
              <span className="settings-value">0.40 (40%)</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Image Size</span>
              <span className="settings-value">320px</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Model</span>
              <span className="settings-value">YOLOv8 (best.pt)</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Defect Classes</span>
              <span className="settings-value">Scratches, Dents, Rust, Other</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Database</span>
              <span className="settings-value">SQLite (inspection.db)</span>
            </div>
            <div className="settings-item">
              <span className="settings-label">Report Format</span>
              <span className="settings-value">PDF (ReportLab)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
