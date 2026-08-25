import { useEffect, useRef, useState, useCallback } from 'react'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'
import ErrorMessage from '../components/ErrorMessage'
import apiClient from '../api/apiClient'
import { getCameraStatus, startCamera, stopCamera, captureInspection, getStreamUrl } from '../api/camera'
import { uploadInspection } from '../api/inspections'
import { downloadReport } from '../api/reports'
import { Camera, CameraOff, Save, CheckCircle, Upload, ImageIcon, X, RefreshCw, Download } from 'lucide-react'

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
const MAX_MB = 20

// ─── Shared result panel ────────────────────────────────────────────────────
function InspectionResult({ result, onDownload, onNew, dlLoading }) {
  const [imgSrc, setImgSrc] = useState(null)

  useEffect(() => {
    if (!result?.image_url) return
    apiClient.get(result.image_url, { responseType: 'blob' })
      .then(r => setImgSrc(URL.createObjectURL(r.data)))
      .catch(() => setImgSrc(null))
    return () => { if (imgSrc) URL.revokeObjectURL(imgSrc) }
  }, [result?.image_url])

  if (!result) return null

  return (
    <div className="upload-result">
      <div className="upload-result__header">
        <CheckCircle size={18} color="var(--green)" />
        <span>Inspection Saved Successfully</span>
        <span className="mono" style={{ marginLeft: 'auto', fontSize: 11 }}>{result.inspection_id}</span>
      </div>

      {imgSrc && (
        <div className="upload-result__image">
          <img src={imgSrc} alt="Annotated inspection" />
        </div>
      )}

      <div className="detection-grid" style={{ marginTop: 16 }}>
        <div className="detection-item">
          <span className="detection-label">Status</span>
          <StatusBadge value={result.status} />
        </div>
        <div className="detection-item">
          <span className="detection-label">Quality Score</span>
          <span className="detection-value detection-value--score">{result.quality_score}%</span>
        </div>
        <div className="detection-item">
          <span className="detection-label">Severity</span>
          <StatusBadge value={result.severity} />
        </div>
        <div className="detection-item">
          <span className="detection-label">Total Defects</span>
          <span className="detection-value">{result.total_defects}</span>
        </div>
        <div className="detection-item detection-item--full">
          <span className="detection-label">Remarks</span>
          <span className="detection-remarks">{result.remarks}</span>
        </div>
      </div>

      {result.detections?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <span className="detection-label" style={{ display: 'block', marginBottom: 10 }}>Detected Objects</span>
          <table className="table" style={{ marginTop: 0 }}>
            <thead>
              <tr>
                <th>Defect</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {result.detections.map((d, i) => (
                <tr key={i}>
                  <td>{d.class}</td>
                  <td className="mono" style={{ color: 'var(--cyan)' }}>{d.confidence}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="live-controls" style={{ marginTop: 18 }}>
        {result.report_available && (
          <button className="btn btn--primary" onClick={onDownload} disabled={dlLoading}>
            {dlLoading ? <div className="spinner spinner--sm" /> : <Download size={15} />}
            Download PDF
          </button>
        )}
        <button className="btn btn--ghost" onClick={onNew}>
          <RefreshCw size={15} /> New Inspection
        </button>
      </div>
    </div>
  )
}

// ─── Live Camera mode ────────────────────────────────────────────────────────
function LiveCameraMode() {
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
      pollRef.current = setInterval(fetchStatus, 1000)
    } else {
      clearInterval(pollRef.current)
    }
    return () => clearInterval(pollRef.current)
  }, [running, fetchStatus])

  const handleStart = async () => {
    setLoading(true); setError('')
    try {
      await startCamera()
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

  const handleCapture = async () => {
    setSaveLoading(true); setSaveError(''); setLastSaved(null)
    try {
      const res = await captureInspection()
      setLastSaved(res.data)
    } catch (err) {
      setSaveError(err.response?.data?.detail || 'Capture failed.')
    } finally { setSaveLoading(false) }
  }

  const handleDownload = async () => {
    if (!lastSaved) return
    setDlLoading(true)
    try { await downloadReport(lastSaved.inspection_id) }
    catch { alert('Report not available.') }
    finally { setDlLoading(false) }
  }

  return (
    <div className="live-layout">
      {/* Camera panel */}
      <div className="live-camera-panel">
        <div className="live-camera-header">
          <span className="live-camera-title">
            <Camera size={18} /> Live Camera Feed
          </span>
          {running && <span className="live-badge">● LIVE</span>}
        </div>

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
              <p style={{ fontSize: 11, marginTop: 4 }}>Click Start Camera to begin inspection</p>
            </div>
          )}
        </div>

        {error && <ErrorMessage message={error} onRetry={fetchStatus} />}

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
            Save Inspection
          </button>
        </div>
      </div>

      {/* Detection panel */}
      <div className="live-info-panel">
        <div className="live-section">
          <h3 className="live-section-title">Current Detection</h3>
          {detection ? (
            <div className="detection-grid">
              <div className="detection-item">
                <span className="detection-label">Status</span>
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
                <span className="detection-label">FPS</span>
                <span className="detection-value">{detection.fps}</span>
              </div>
              <div className="detection-item detection-item--full">
                <span className="detection-label">Remarks</span>
                <span className="detection-remarks">{detection.remarks}</span>
              </div>
            </div>
          ) : (
            <p className="empty-text">No detection data. Start camera first.</p>
          )}
        </div>

        <div className="live-section">
          <h3 className="live-section-title">Defect Counts</h3>
          {detection ? (
            <div className="defect-counts">
              {[
                { label: 'Total',    value: detection.total_defects, color: '#6366f1' },
                { label: 'Scratches', value: detection.scratches,   color: '#f97316' },
                { label: 'Dents',    value: detection.dents,        color: '#eab308' },
                { label: 'Rust',     value: detection.rust,         color: '#ef4444' },
                { label: 'Other',    value: detection.other,        color: '#8b5cf6' },
              ].map(d => (
                <div key={d.label} className="defect-count-item">
                  <span className="defect-count-label">{d.label}</span>
                  <span className="defect-count-value" style={{ color: d.color }}>{d.value}</span>
                </div>
              ))}
            </div>
          ) : <p className="empty-text">—</p>}
        </div>

        {detection?.detections?.length > 0 && (
          <div className="live-section">
            <h3 className="live-section-title">Detected Objects</h3>
            <div className="detection-list">
              {detection.detections.map((d, i) => (
                <div key={i} className="detection-tag">
                  <span className="detection-tag__class">{d.class}</span>
                  <span className="detection-tag__conf">{d.confidence}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {saveError && <ErrorMessage message={saveError} />}

        {lastSaved && (
          <div className="save-result">
            <div className="save-result__header">
              <CheckCircle size={18} color="var(--green)" />
              <span>Inspection Saved</span>
            </div>
            <div className="save-result__body">
              {[
                ['ID',      <span className="mono">{lastSaved.inspection_id}</span>],
                ['Status',  <StatusBadge value={lastSaved.status} />],
                ['Score',   `${lastSaved.quality_score}%`],
                ['Defects', lastSaved.total_defects],
              ].map(([label, val]) => (
                <div key={label} className="save-result__row">
                  <span>{label}</span><span>{val}</span>
                </div>
              ))}
              {lastSaved.report_available && (
                <div className="save-result__row">
                  <span>Report</span>
                  <span style={{ color: 'var(--green)' }}>PDF Generated ✓</span>
                </div>
              )}
            </div>
            {lastSaved.report_available && (
              <button className="btn btn--sm btn--primary" style={{ marginTop: 12 }} onClick={handleDownload} disabled={dlLoading}>
                {dlLoading ? <div className="spinner spinner--sm" /> : <Download size={13} />}
                Download PDF
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Upload Image mode ───────────────────────────────────────────────────────
function UploadMode() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [detecting, setDetecting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [dlLoading, setDlLoading] = useState(false)
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

  // Cleanup preview URL
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
      const res = await uploadInspection(file)
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

  const handleDownload = async () => {
    if (!result) return
    setDlLoading(true)
    try { await downloadReport(result.inspection_id) }
    catch { alert('Report not available.') }
    finally { setDlLoading(false) }
  }

  // ── After detection: show result ──
  if (result) {
    return (
      <div className="upload-result-wrap">
        <InspectionResult
          result={result}
          onDownload={handleDownload}
          onNew={handleNew}
          dlLoading={dlLoading}
        />
      </div>
    )
  }

  // ── Before detection: show upload UI ──
  return (
    <div className="upload-wrap">
      <div className="upload-panel">
        {!file ? (
          // Drop zone
          <div
            ref={dropRef}
            className="upload-drop"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => inputRef.current?.click()}
          >
            <ImageIcon size={48} style={{ color: 'var(--muted)', marginBottom: 16 }} />
            <p className="upload-drop__title">Upload Steel / Fabric Image</p>
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
          // Preview + detect
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
                  : <><ImageIcon size={15} /> Detect Defects</>
                }
              </button>
            </div>
          </div>
        )}

        {error && <ErrorMessage message={error} />}
      </div>

      {/* Info panel */}
      <div className="live-info-panel upload-info-panel">
        <div className="live-section">
          <h3 className="live-section-title">How It Works</h3>
          <div style={{ display: 'grid', gap: 14, marginTop: 16 }}>
            {[
              ['1', 'Select a JPG or PNG image of the steel/fabric surface'],
              ['2', 'Click Detect Defects to send the image to the AI backend'],
              ['3', 'YOLOv8 model analyzes the image for surface defects'],
              ['4', 'View the annotated result with bounding boxes'],
              ['5', 'Save the inspection to the database and download the PDF report'],
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
          <h3 className="live-section-title">Detectable Defects</h3>
          <div className="detection-list" style={{ marginTop: 14 }}>
            {[
              { label: 'Scratches', color: '#f97316' },
              { label: 'Dents',     color: '#eab308' },
              { label: 'Rust',      color: '#ef4444' },
              { label: 'Other',     color: '#8b5cf6' },
            ].map(d => (
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

// ─── Main page ───────────────────────────────────────────────────────────────
export default function LiveInspection() {
  const [mode, setMode] = useState('camera') // 'camera' | 'upload'

  return (
    <div className="page">
      <Header title="Live Inspection" />
      <div className="page__body">

        {/* Mode switcher */}
        <div className="inspection-mode-bar">
          <button
            className={`inspection-mode-btn ${mode === 'camera' ? 'inspection-mode-btn--active' : ''}`}
            onClick={() => setMode('camera')}
          >
            <Camera size={16} /> Live Camera
          </button>
          <button
            className={`inspection-mode-btn ${mode === 'upload' ? 'inspection-mode-btn--active' : ''}`}
            onClick={() => setMode('upload')}
          >
            <ImageIcon size={16} /> Upload Image
          </button>
        </div>

        {mode === 'camera' ? <LiveCameraMode /> : <UploadMode />}
      </div>
    </div>
  )
}
