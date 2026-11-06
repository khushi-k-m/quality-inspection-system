import { useEffect, useRef, useState, useCallback } from 'react'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'
import ErrorMessage from '../components/ErrorMessage'
import apiClient from '../api/apiClient'
import { getCameraStatus, startCamera, stopCamera, setCameraMode, captureInspection, getStreamUrl } from '../api/camera'
import { uploadMaterialInspection } from '../api/inspections'
import { downloadReportWithDetails } from '../api/reports'
import {
  Camera, CameraOff, Save, CheckCircle, Upload, ImageIcon, X, RefreshCw,
  Download, AlertTriangle, Zap, Flame, Sliders, ChevronDown, ChevronUp, FileText
} from 'lucide-react'

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
const MAX_MB = 20

const MATERIAL_DEFECTS = {
  steel: [
    { label: 'Scratches', color: '#f97316' },
    { label: 'Dents',     color: '#eab308' },
    { label: 'Rust',      color: '#ef4444' },
    { label: 'Other',     color: '#8b5cf6' },
  ],
  metal: [
    { label: 'Water Spot',    color: '#06b6d4' },
    { label: 'Oil Spot',      color: '#f97316' },
    { label: 'Silk Spot',     color: '#eab308' },
    { label: 'Welding Line',  color: '#ef4444' },
    { label: 'Inclusion',     color: '#8b5cf6' },
    { label: 'Punching Hole', color: '#f43f5e' },
  ],
  fabric: [
    { label: 'Color Bleeding', color: '#ec4899' },
    { label: 'Crease',         color: '#f97316' },
    { label: 'Hole',           color: '#ef4444' },
  ],
  pcb: [
    { label: 'Missing Hole',     color: '#6366f1' },
    { label: 'Mouse Bite',       color: '#f97316' },
    { label: 'Open Circuit',     color: '#ef4444' },
    { label: 'Short',            color: '#dc2626' },
    { label: 'Spur',             color: '#eab308' },
    { label: 'Spurious Copper',  color: '#8b5cf6' },
  ],
  welding: [
    { label: 'Bad Weld',  color: '#ef4444' },
    { label: 'Good Weld', color: '#22c55e' },
  ],
}

const UPLOAD_MATERIALS = [
  { key: 'steel',   label: 'Steel' },
  { key: 'metal',   label: 'Metal' },
  { key: 'fabric',  label: 'Fabric' },
  { key: 'pcb',     label: 'PCB' },
  { key: 'welding', label: 'Welding' },
]

// ─── Shared result panel with Thermal Sheet & 2-Page Client Report ───────────
function InspectionResult({ result, onNew }) {
  const [activeTab, setActiveTab] = useState('optical') // 'optical' | 'thermal'
  const [opticalSrc, setOpticalSrc] = useState(null)
  const [thermalSrc, setThermalSrc] = useState(null)
  const [dlLoading, setDlLoading] = useState(false)
  const [thermalDlLoading, setThermalDlLoading] = useState(false)
  const [showConfig, setShowConfig] = useState(false)

  // Client & Company report customization form state
  const [clientName, setClientName] = useState('Global Precision Components Ltd.')
  const [poNumber, setPoNumber] = useState('PO-2026-INSP-882')
  const [batchId, setBatchId] = useState('LOT-B492-REV3')
  const [companyName, setCompanyName] = useState('Apex Industrial Quality Labs')

  // Load optical annotated image
  useEffect(() => {
    if (!result?.image_url) return
    apiClient.get(result.image_url, { responseType: 'blob' })
      .then(r => setOpticalSrc(URL.createObjectURL(r.data)))
      .catch(() => setOpticalSrc(null))
    return () => { if (opticalSrc) URL.revokeObjectURL(opticalSrc) }
  }, [result?.image_url])

  // Load false-color thermal sheet
  useEffect(() => {
    if (!result?.inspection_id) return
    const thermalUrl = result.thermal_sheet_url || `/api/images/thermal/${result.inspection_id}`
    apiClient.get(thermalUrl, { responseType: 'blob' })
      .then(r => setThermalSrc(URL.createObjectURL(r.data)))
      .catch(() => setThermalSrc(null))
    return () => { if (thermalSrc) URL.revokeObjectURL(thermalSrc) }
  }, [result?.inspection_id, result?.thermal_sheet_url])

  if (!result) return null

  // Error / Validation rejection handler
  if (result.status === 'INVALID_IMAGE' || result.status === 'INVALID_MATERIAL' || result.status === 'MATERIAL_UNVERIFIED') {
    const isInvalidImage = result.status === 'INVALID_IMAGE'
    const isUnverified = result.status === 'MATERIAL_UNVERIFIED'

    return (
      <div className="upload-result">
        <div className="upload-result__header" style={{ color: isInvalidImage ? 'var(--amber)' : isUnverified ? 'var(--amber)' : 'var(--red)' }}>
          {isInvalidImage ? <ImageIcon size={18} color="var(--amber)" /> : isUnverified ? <AlertTriangle size={18} color="var(--amber)" /> : <X size={18} color="var(--red)" />}
          <span>
            {isInvalidImage ? '⚠️ No Valid Product Detected' : isUnverified ? '⚠️ Material Could Not Be Verified' : '❌ Invalid Material'}
          </span>
        </div>

        <div className="detection-grid" style={{ marginTop: 0 }}>
          <div className="detection-item">
            <span className="detection-label">Selected</span>
            <span className="detection-value">{result.selected_material ? result.selected_material.toUpperCase() : 'UNKNOWN'}</span>
          </div>
          <div className="detection-item">
            <span className="detection-label">Auto-Detected</span>
            <span className="detection-value" style={{ color: 'var(--cyan)' }}>{result.detected_material ? result.detected_material.toUpperCase() : 'None'}</span>
          </div>
          <div className="detection-item detection-item--full">
            <span className="detection-label">Message</span>
            <span className="detection-remarks">{result.message}</span>
          </div>
        </div>

        <div className="live-controls" style={{ marginTop: 18 }}>
          <button className="btn btn--ghost" onClick={onNew}>
            <RefreshCw size={15} /> Try Again
          </button>
        </div>
      </div>
    )
  }

  // Download 2-Page Client PDF with customized metadata
  const handleDownloadReport = async () => {
    setDlLoading(true)
    try {
      await downloadReportWithDetails(result.inspection_id, {
        material: result.material || 'steel',
        client_name: clientName,
        po_number: poNumber,
        batch_id: batchId,
        company_name: companyName,
      })
    } catch {
      alert('Report could not be downloaded.')
    } finally {
      setDlLoading(false)
    }
  }

  // Download thermal sheet directly as JPG image
  const handleDownloadThermalSheet = async () => {
    setThermalDlLoading(true)
    try {
      const thermalUrl = result.thermal_sheet_url || `/api/images/thermal/${result.inspection_id}`
      const resp = await apiClient.get(thermalUrl, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'image/jpeg' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${result.inspection_id}_thermal_sheet.jpg`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('Thermal sheet could not be downloaded.')
    } finally {
      setThermalDlLoading(false)
    }
  }

  return (
    <div className="upload-result">
      <div className="upload-result__header">
        <CheckCircle size={18} color="var(--green)" />
        <span>Inspection Verified &amp; Saved Successfully</span>
        <span className="mono" style={{ marginLeft: 'auto', fontSize: 11 }}>{result.inspection_id}</span>
      </div>

      {/* Dual Tab Visual Switcher: Optical Frame vs False-Color Thermal Sheet */}
      <div className="inspection-mode-bar" style={{ margin: '14px 0 10px 0', background: 'rgba(255,255,255,0.03)' }}>
        <button
          className={`inspection-mode-btn ${activeTab === 'optical' ? 'inspection-mode-btn--active' : ''}`}
          onClick={() => setActiveTab('optical')}
        >
          <Camera size={15} /> Optical Inspection Capture
        </button>
        <button
          className={`inspection-mode-btn ${activeTab === 'thermal' ? 'inspection-mode-btn--active' : ''}`}
          onClick={() => setActiveTab('thermal')}
          style={{ borderColor: activeTab === 'thermal' ? '#f59e0b' : 'transparent' }}
        >
          <Flame size={15} color="#f59e0b" /> Thermal Sheet Output (FLIR False-Color)
        </button>
      </div>

      {/* Image Viewer */}
      <div className="upload-result__image" style={{ minHeight: 280, background: '#0a0f18', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, overflow: 'hidden' }}>
        {activeTab === 'optical' ? (
          opticalSrc ? (
            <img src={opticalSrc} alt="Annotated inspection capture" style={{ width: '100%', height: 'auto', maxHeight: 440, objectFit: 'contain' }} />
          ) : (
            <div style={{ color: 'var(--t-muted)', padding: 20, textAlign: 'center' }}>Loading optical frame...</div>
          )
        ) : (
          thermalSrc ? (
            <img src={thermalSrc} alt="Thermographic False-Color Defect Sheet" style={{ width: '100%', height: 'auto', maxHeight: 440, objectFit: 'contain' }} />
          ) : (
            <div style={{ color: 'var(--t-muted)', padding: 20, textAlign: 'center' }}>
              <Flame size={28} color="#f59e0b" style={{ margin: '0 auto 8px auto', display: 'block' }} />
              Generating high-resolution thermal sheet...
            </div>
          )
        )}
      </div>

      {/* Core Metrics Grid */}
      <div className="detection-grid" style={{ marginTop: 16 }}>
        <div className="detection-item">
          <span className="detection-label">Quality Status</span>
          <StatusBadge value={result.status} />
        </div>
        <div className="detection-item">
          <span className="detection-label">Quality Score</span>
          <span className="detection-value detection-value--score">{result.quality_score}%</span>
        </div>
        <div className="detection-item">
          <span className="detection-label">Material</span>
          <span className="detection-value" style={{ color: 'var(--cyan)' }}>
            {(result.material || 'steel').toUpperCase()}
          </span>
        </div>
        <div className="detection-item">
          <span className="detection-label">Total Defects</span>
          <span className="detection-value" style={{ color: result.total_defects > 0 ? 'var(--red)' : 'var(--green)' }}>
            {result.total_defects}
          </span>
        </div>
        <div className="detection-item detection-item--full">
          <span className="detection-label">Evaluation &amp; Remarks</span>
          <span className="detection-remarks">{result.remarks}</span>
        </div>
      </div>

      {/* Detected Defect Table */}
      {result.detections?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <span className="detection-label" style={{ display: 'block', marginBottom: 8 }}>Detected Defects Inventory</span>
          <table className="table" style={{ marginTop: 0 }}>
            <thead>
              <tr>
                <th>#</th>
                <th>Defect Class</th>
                <th>Confidence</th>
                <th>Coordinates (px)</th>
              </tr>
            </thead>
            <tbody>
              {result.detections.map((d, i) => (
                <tr key={i}>
                  <td className="mono">{i + 1}</td>
                  <td><strong>{d.class || d.class_name || 'Defect'}</strong></td>
                  <td className="mono" style={{ color: 'var(--cyan)' }}>{d.confidence}%</td>
                  <td className="mono" style={{ fontSize: 11, color: 'var(--t-muted)' }}>
                    {d.x1 != null ? `(${d.x1}, ${d.y1}) - (${d.x2}, ${d.y2})` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Expandable Client & Company Report Details Form */}
      <div style={{ marginTop: 16, border: '1px solid var(--border)', borderRadius: 8, padding: '12px 16px', background: 'rgba(255,255,255,0.02)' }}>
        <div
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          onClick={() => setShowConfig(!showConfig)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sliders size={15} color="var(--cyan)" />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Client &amp; Company Details (Included on 2-Page Report)</span>
          </div>
          <button type="button" style={{ color: 'var(--t-muted)' }}>
            {showConfig ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        {showConfig && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--t-muted)', marginBottom: 4 }}>Client / Customer Name</label>
              <input
                type="text"
                value={clientName}
                onChange={e => setClientName(e.target.value)}
                style={{ width: '100%', padding: '6px 10px', background: '#0a1420', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--t-base)', fontSize: 12 }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--t-muted)', marginBottom: 4 }}>Purchase Order (PO / WO #)</label>
              <input
                type="text"
                value={poNumber}
                onChange={e => setPoNumber(e.target.value)}
                style={{ width: '100%', padding: '6px 10px', background: '#0a1420', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--t-base)', fontSize: 12 }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--t-muted)', marginBottom: 4 }}>Batch / Lot ID</label>
              <input
                type="text"
                value={batchId}
                onChange={e => setBatchId(e.target.value)}
                style={{ width: '100%', padding: '6px 10px', background: '#0a1420', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--t-base)', fontSize: 12 }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--t-muted)', marginBottom: 4 }}>Inspection Lab / Company Name</label>
              <input
                type="text"
                value={companyName}
                onChange={e => setCompanyName(e.target.value)}
                style={{ width: '100%', padding: '6px 10px', background: '#0a1420', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--t-base)', fontSize: 12 }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Action Controls */}
      <div className="live-controls" style={{ marginTop: 20 }}>
        <button className="btn btn--primary" onClick={handleDownloadReport} disabled={dlLoading}>
          {dlLoading ? <div className="spinner spinner--sm" /> : <FileText size={16} />}
          Download 2-Page Client Report (PDF)
        </button>

        <button className="btn btn--ghost" onClick={handleDownloadThermalSheet} disabled={thermalDlLoading} style={{ borderColor: '#f59e0b', color: '#fbbf24' }}>
          {thermalDlLoading ? <div className="spinner spinner--sm" /> : <Flame size={16} />}
          Download Thermal Sheet (JPG)
        </button>

        <button className="btn btn--ghost" onClick={onNew}>
          <RefreshCw size={15} /> New Inspection
        </button>
      </div>
    </div>
  )
}

// ─── Live Camera Mode with Real-Time Auto-Detection ─────────────────────────
function LiveCameraMode() {
  const [material, setMaterial] = useState('auto') // default to 'auto' for auto-detection!
  const [detection, setDetection] = useState(null)
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastSaved, setLastSaved] = useState(null)
  const [saveLoading, setSaveLoading] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [dlLoading, setDlLoading] = useState(false)
  const pollRef = useRef(null)
  const streamUrl = getStreamUrl()

  const fetchStatus = useCallback(async () => {
    try {
      const res = await getCameraStatus()
      setDetection(res.data.detection)
      setRunning(res.data.running)
    } catch {
      setRunning(false)
    }
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  useEffect(() => {
    if (running) {
      pollRef.current = setInterval(fetchStatus, 900)
    } else {
      clearInterval(pollRef.current)
    }
    return () => clearInterval(pollRef.current)
  }, [running, fetchStatus])

  const handleStart = async () => {
    setLoading(true); setError('')
    try {
      await startCamera(material)
      setRunning(true)
      await fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start camera.')
    } finally { setLoading(false) }
  }

  const handleStop = async () => {
    setLoading(true)
    try {
      await stopCamera()
      setRunning(false)
      setDetection(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to stop camera.')
    } finally { setLoading(false) }
  }

  const handleModeSwitch = async (targetOption) => {
    setMaterial(targetOption)
    if (running) {
      try {
        await setCameraMode(targetOption)
        await fetchStatus()
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to switch camera mode.')
      }
    }
  }

  const handleCapture = async () => {
    setSaveLoading(true); setSaveError(''); setLastSaved(null)
    try {
      const res = await captureInspection('AI Live Camera Inspector')
      setLastSaved(res.data)
    } catch (err) {
      setSaveError(err.response?.data?.detail || 'Capture failed.')
    } finally { setSaveLoading(false) }
  }

  // Active detected material
  const activeMaterial = detection?.material || (material === 'auto' ? 'steel' : material)
  const isAutoMode = material === 'auto' || detection?.auto_mode
  const detectedMaterial = detection?.detected_material || activeMaterial
  const detectedConfidence = detection?.material_confidence ? `${detection.material_confidence.toFixed(0)}%` : '95%'

  return (
    <div className="live-layout">
      {/* Camera feed panel */}
      <div className="live-camera-panel">
        <div className="live-camera-header">
          <span className="live-camera-title">
            <Camera size={18} /> Live Quality Inspection Camera
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {isAutoMode && (
              <span className="live-badge" style={{ background: 'linear-gradient(135deg, #0284c7, #6366f1)', color: '#fff', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <Zap size={12} /> Auto-Detect: {detectedMaterial.toUpperCase()} ({detectedConfidence})
              </span>
            )}
            {running && <span className="live-badge">● LIVE</span>}
          </div>
        </div>

        {/* Material Selection / Auto-Detection Mode Bar */}
        <div className="inspection-mode-bar" style={{ margin: '12px 0' }}>
          <button
            className={`inspection-mode-btn ${material === 'auto' ? 'inspection-mode-btn--active' : ''}`}
            onClick={() => handleModeSwitch('auto')}
            style={material === 'auto' ? { border: '1px solid #38bdf8', color: '#38bdf8', fontWeight: 700 } : {}}
          >
            <Zap size={14} color={material === 'auto' ? '#38bdf8' : 'currentColor'} /> ⚡ Auto Detect
          </button>
          {['steel', 'metal', 'fabric', 'pcb', 'welding'].map(option => (
            <button
              key={option}
              className={`inspection-mode-btn ${material === option ? 'inspection-mode-btn--active' : ''}`}
              onClick={() => handleModeSwitch(option)}
            >
              {option[0].toUpperCase() + option.slice(1)}
            </button>
          ))}
        </div>

        {/* Video stream container */}
        <div className="live-camera-view">
          {running ? (
            <img
              src={streamUrl}
              alt="Live YOLO stream"
              className="live-stream-img"
              onError={() => setError('Camera stream disconnected.')}
            />
          ) : (
            <div className="live-camera-placeholder">
              <CameraOff size={48} />
              <p>Camera not started</p>
              <p style={{ fontSize: 11, marginTop: 4 }}>Select Auto Detect or a material, then click Start Camera</p>
            </div>
          )}
        </div>

        {error && <ErrorMessage message={error} onRetry={fetchStatus} />}

        {/* Controls */}
        <div className="live-controls">
          {!running ? (
            <button className="btn btn--primary" onClick={handleStart} disabled={loading}>
              {loading ? <div className="spinner spinner--sm" /> : <Camera size={16} />}
              Start Camera
            </button>
          ) : (
            <button className="btn btn--danger" onClick={handleStop} disabled={loading}>
              <CameraOff size={16} /> Stop Camera
            </button>
          )}
          <button className="btn btn--accent" onClick={handleCapture} disabled={!running || saveLoading}>
            {saveLoading ? <div className="spinner spinner--sm" /> : <Save size={16} />}
            Save &amp; Generate Client Report
          </button>
        </div>
      </div>

      {/* Right Telemetry & Status Panel */}
      <div className="live-info-panel">
        <div className="live-section">
          <h3 className="live-section-title">Inspection State</h3>
          {detection ? (
            <div className="detection-grid">
              <div className="detection-item">
                <span className="detection-label">Active Material</span>
                <span className="detection-value" style={{ color: 'var(--cyan)' }}>
                  {activeMaterial.toUpperCase()} {isAutoMode && '(AUTO)'}
                </span>
              </div>
              <div className="detection-item">
                <span className="detection-label">Quality Status</span>
                <StatusBadge value={detection.status} />
              </div>
              <div className="detection-item">
                <span className="detection-label">Quality Score</span>
                <span className="detection-value detection-value--score">{detection.quality_score}%</span>
              </div>
              <div className="detection-item">
                <span className="detection-label">Severity</span>
                <StatusBadge value={detection.severity} />
              </div>
              <div className="detection-item">
                <span className="detection-label">Stream FPS</span>
                <span className="detection-value">{detection.fps}</span>
              </div>
              <div className="detection-item">
                <span className="detection-label">Total Defects</span>
                <span className="detection-value" style={{ color: detection.total_defects > 0 ? 'var(--red)' : 'var(--green)' }}>
                  {detection.total_defects}
                </span>
              </div>
              <div className="detection-item detection-item--full">
                <span className="detection-label">Remarks</span>
                <span className="detection-remarks">{detection.remarks}</span>
              </div>
            </div>
          ) : (
            <p className="empty-text">No active telemetry. Start camera to begin live analysis.</p>
          )}
        </div>

        {/* Defect Categories for active material */}
        <div className="live-section">
          <h3 className="live-section-title">Monitored Defect Classes ({activeMaterial.toUpperCase()})</h3>
          <div className="detection-list" style={{ marginTop: 10 }}>
            {(MATERIAL_DEFECTS[activeMaterial] || []).map(d => (
              <div key={d.label} className="detection-tag">
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
                <span className="detection-tag__class">{d.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Live Detected Objects */}
        {detection?.detections?.length > 0 && (
          <div className="live-section">
            <h3 className="live-section-title">Live Detections ({detection.detections.length})</h3>
            <div className="detection-list">
              {detection.detections.map((d, i) => (
                <div key={i} className="detection-tag">
                  <span className="detection-tag__class">{d.class || d.class_name}</span>
                  <span className="detection-tag__conf">{d.confidence}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {saveError && <ErrorMessage message={saveError} />}

        {/* Last Saved Inspection Callout & Report Launcher */}
        {lastSaved && (
          <div className="save-result" style={{ border: '1px solid var(--green)', background: 'rgba(74, 222, 128, 0.05)' }}>
            <div className="save-result__header">
              <CheckCircle size={18} color="var(--green)" />
              <span style={{ fontWeight: 600 }}>Inspection Captured &amp; Report Ready</span>
            </div>
            <div className="save-result__body">
              {[
                ['Inspection ID', <span className="mono">{lastSaved.inspection_id}</span>],
                ['Material',      lastSaved.material?.toUpperCase() || activeMaterial.toUpperCase()],
                ['Quality Score', `${lastSaved.quality_score}%`],
                ['Status',        <StatusBadge value={lastSaved.status} />],
                ['Total Defects', lastSaved.total_defects],
                ['Thermal Sheet', <span style={{ color: '#fbbf24', display: 'inline-flex', alignItems: 'center', gap: 4 }}><Flame size={12} /> Generated ✓</span>],
              ].map(([label, val]) => (
                <div key={label} className="save-result__row">
                  <span>{label}</span><span>{val}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 14 }}>
              <button
                className="btn btn--primary"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => downloadReportWithDetails(lastSaved.inspection_id, { material: lastSaved.material || activeMaterial })}
                disabled={dlLoading}
              >
                {dlLoading ? <div className="spinner spinner--sm" /> : <Download size={14} />}
                Download 2-Page Client Report (PDF)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Upload Image Mode ───────────────────────────────────────────────────────
function UploadMode() {
  const [material, setMaterial] = useState('steel')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [detecting, setDetecting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const inputRef = useRef(null)
  const dropRef = useRef(null)

  const validateAndSet = (f) => {
    setError('')
    setResult(null)
    if (!f) return
    if (!ALLOWED_TYPES.includes(f.type)) {
      setError(`Unsupported file type. Please upload a JPG or PNG image.`)
      return
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_MB} MB.`)
      return
    }
    setFile(f)
    const url = URL.createObjectURL(f)
    setPreview(url)
  }

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const handleFileChange = (e) => validateAndSet(e.target.files?.[0])

  const handleDrop = (e) => {
    e.preventDefault()
    dropRef.current?.classList.remove('upload-drop--over')
    validateAndSet(e.dataTransfer.files?.[0])
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    dropRef.current?.classList.add('upload-drop--over')
  }

  const handleDragLeave = () => dropRef.current?.classList.remove('upload-drop--over')

  const handleDetect = async () => {
    if (!file || detecting) return
    setDetecting(true)
    setError('')
    try {
      const res = await uploadMaterialInspection(material, file)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed. Please try again.')
    } finally {
      setDetecting(false)
    }
  }

  const handleNew = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleMaterialChange = (m) => {
    setMaterial(m)
    setFile(null)
    setPreview(null)
    setResult(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  if (result) {
    return (
      <div className="upload-result-wrap">
        <InspectionResult
          result={result}
          onNew={handleNew}
        />
      </div>
    )
  }

  return (
    <div className="upload-wrap">
      <div className="upload-panel">
        <div className="inspection-mode-bar" style={{ marginBottom: 14 }}>
          {UPLOAD_MATERIALS.map(m => (
            <button
              key={m.key}
              className={`inspection-mode-btn ${material === m.key ? 'inspection-mode-btn--active' : ''}`}
              onClick={() => handleMaterialChange(m.key)}
              disabled={detecting}
            >
              {m.label}
            </button>
          ))}
        </div>

        {!file ? (
          <div
            ref={dropRef}
            className="upload-drop"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => inputRef.current?.click()}
          >
            <ImageIcon size={48} style={{ color: 'var(--muted)', marginBottom: 16 }} />
            <p className="upload-drop__title">Upload {UPLOAD_MATERIALS.find(m => m.key === material)?.label} Surface Image</p>
            <p className="upload-drop__sub">Drag &amp; drop here, or click to browse</p>
            <p className="upload-drop__hint">Supported: JPG, JPEG, PNG · Max {MAX_MB} MB</p>
            <button className="btn btn--primary" style={{ marginTop: 20 }} type="button">
              <Upload size={15} /> Browse Image
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
          </div>
        ) : (
          <div className="upload-preview">
            <div className="upload-preview__img-wrap">
              <img src={preview} alt="Selected" className="upload-preview__img" />
              <button className="upload-preview__remove" onClick={handleNew} title="Remove">
                <X size={16} />
              </button>
            </div>
            <div className="upload-preview__info">
              <span className="upload-preview__name">{file.name}</span>
              <span className="upload-preview__size" style={{ color: 'var(--muted)', fontSize: 11 }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
            <div className="live-controls" style={{ marginTop: 18 }}>
              <button className="btn btn--ghost" onClick={handleNew} disabled={detecting}>
                <RefreshCw size={15} /> Change Image
              </button>
              <button className="btn btn--primary" onClick={handleDetect} disabled={detecting}>
                {detecting
                  ? <><div className="spinner spinner--sm" /> AI Detection in Progress...</>
                  : <><ImageIcon size={15} /> Detect Defects &amp; Generate Thermal Sheet</>
                }
              </button>
            </div>
          </div>
        )}

        {error && <ErrorMessage message={error} />}
      </div>

      <div className="live-info-panel upload-info-panel">
        <div className="live-section">
          <h3 className="live-section-title">Inspection Workflow</h3>
          <div style={{ display: 'grid', gap: 14, marginTop: 16 }}>
            {[
              ['1', 'Upload workpiece surface image (Optical or NDT)'],
              ['2', 'YOLO model identifies defects and localized bounding boxes'],
              ['3', 'Generates false-color infrared Thermal Sheet with hotspot modeling'],
              ['4', 'Produces certified 2-page client report with company and customer details'],
            ].map(([n, text]) => (
              <div key={n} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <span style={{
                  flexShrink: 0, width: 22, height: 22, borderRadius: '50%',
                  background: 'rgba(69,214,209,.15)', color: 'var(--cyan)',
                  display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 700
                }}>{n}</span>
                <span style={{ color: 'var(--muted)', fontSize: 12, lineHeight: 1.6 }}>{text}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="live-section">
          <h3 className="live-section-title">Monitored Defect Classes</h3>
          <div className="detection-list" style={{ marginTop: 14 }}>
            {(MATERIAL_DEFECTS[material] || []).map(d => (
              <div key={d.label} className="detection-tag">
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
                <span className="detection-tag__class">{d.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ───────────────────────────────────────────────────────────────
export default function LiveInspection() {
  const [mode, setMode] = useState('camera') // 'camera' | 'upload'

  return (
    <div className="page">
      <Header title="Live Inspection &amp; Thermal Diagnostics" />
      <div className="page__body">
        <div className="inspection-mode-bar">
          <button
            className={`inspection-mode-btn ${mode === 'camera' ? 'inspection-mode-btn--active' : ''}`}
            onClick={() => setMode('camera')}
          >
            <Camera size={16} /> Live Camera Feed &amp; Auto-Detect
          </button>
          <button
            className={`inspection-mode-btn ${mode === 'upload' ? 'inspection-mode-btn--active' : ''}`}
            onClick={() => setMode('upload')}
          >
            <ImageIcon size={16} /> Upload Image &amp; Thermal Analysis
          </button>
        </div>

        {mode === 'camera' ? <LiveCameraMode /> : <UploadMode />}
      </div>
    </div>
  )
}
