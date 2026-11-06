import { useEffect, useRef, useState, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import StatusBadge from '../components/StatusBadge'
import ErrorMessage from '../components/ErrorMessage'
import Loading from '../components/Loading'
import apiClient from '../api/apiClient'
import { getCameraStatus, startCamera, stopCamera, captureInspection, getStreamUrl } from '../api/camera'
import { uploadMaterialInspection } from '../api/inspections'
import { getMaterialReportDownload } from '../api/reports'
import {
  Camera, CameraOff, Upload, ImageIcon, X, RefreshCw,
  Download, CheckCircle, Save, AlertTriangle, ScanLine, ChevronDown
} from 'lucide-react'

const ALLOWED = ['image/jpeg', 'image/jpg', 'image/png']
const MAX_MB = 20

const MATERIALS = [
  { key: 'steel',   label: 'Steel',   color: '#38bdf8', defects: ['Crazing','Inclusion','Patches','Pitted Surface','Rolled-in Scale','Scratches'] },
  { key: 'metal',   label: 'Metal',   color: '#818cf8', defects: ['Water Spot','Oil Spot','Silk Spot','Welding Line','Inclusion','Punching Hole'] },
  { key: 'fabric',  label: 'Fabric',  color: '#f472b6', defects: ['Color Bleeding','Crease','Hole'] },
  { key: 'pcb',     label: 'PCB',     color: '#34d399', defects: ['Missing Hole','Mouse Bite','Open Circuit','Short','Spur','Spurious Copper'] },
  { key: 'welding', label: 'Welding', color: '#fb923c', defects: ['Bad Weld','Good Weld'] },
]

// ── Result panel ─────────────────────────────────────────────────────────────
function ResultPanel({ result, material, onNew, onDownload, dlLoading }) {
  const [imgSrc, setImgSrc] = useState(null)

  useEffect(() => {
    if (!result?.image_url) return
    let url
    apiClient.get(result.image_url, { responseType: 'blob' })
      .then(r => { url = URL.createObjectURL(r.data); setImgSrc(url) })
      .catch(() => setImgSrc(null))
    return () => { if (url) URL.revokeObjectURL(url) }
  }, [result?.image_url])

  if (!result) return null

  const isInvalid = ['INVALID_IMAGE', 'INVALID_MATERIAL', 'MATERIAL_UNVERIFIED'].includes(result.status)

  if (isInvalid) {
    return (
      <div className="result-panel result-panel--invalid">
        <div className="result-panel__hdr">
          <AlertTriangle size={18} />
          <span>
            {result.status === 'INVALID_IMAGE' && 'No Valid Product Detected'}
            {result.status === 'INVALID_MATERIAL' && 'Invalid Material'}
            {result.status === 'MATERIAL_UNVERIFIED' && 'Material Could Not Be Verified'}
          </span>
          <StatusBadge value={result.status} />
        </div>
        <div className="result-grid">
          <div className="result-item">
            <span className="result-label">Selected</span>
            <span className="result-val">{result.selected_material ? result.selected_material.charAt(0).toUpperCase() + result.selected_material.slice(1) : material}</span>
          </div>
          <div className="result-item">
            <span className="result-label">Detected</span>
            <span className="result-val">{result.detected_material ? result.detected_material.charAt(0).toUpperCase() + result.detected_material.slice(1) : 'None'}</span>
          </div>
          <div className="result-item result-item--full">
            <span className="result-label">Message</span>
            <span className="result-val result-val--muted">{result.message}</span>
          </div>
        </div>
        <button className="btn btn--ghost" onClick={onNew}><RefreshCw size={14} /> Try Again</button>
      </div>
    )
  }

  return (
    <div className="result-panel">
      <div className="result-panel__hdr result-panel__hdr--ok">
        <CheckCircle size={18} />
        <span>Inspection Complete</span>
        <span className="mono" style={{ marginLeft: 'auto', fontSize: 11 }}>{result.inspection_id}</span>
      </div>

      {imgSrc && (
        <div className="result-img-wrap">
          <img src={imgSrc} alt="Annotated inspection result" className="result-img" />
        </div>
      )}

      <div className="result-grid">
        <div className="result-item">
          <span className="result-label">Status</span>
          <StatusBadge value={result.status} />
        </div>
        <div className="result-item">
          <span className="result-label">Quality Score</span>
          <span className="result-val result-val--score">{result.quality_score}%</span>
        </div>
        <div className="result-item">
          <span className="result-label">Severity</span>
          <StatusBadge value={result.severity} />
        </div>
        <div className="result-item">
          <span className="result-label">Total Defects</span>
          <span className="result-val">{result.total_defects}</span>
        </div>
        <div className="result-item result-item--full">
          <span className="result-label">Remarks</span>
          <span className="result-val result-val--muted">{result.remarks}</span>
        </div>
      </div>

      {result.detections?.length > 0 && (
        <div className="result-detections">
          <span className="result-label" style={{ display: 'block', marginBottom: 10 }}>Detected Objects</span>
          <table className="tbl" style={{ marginTop: 0 }}>
            <thead><tr><th>Defect</th><th>Confidence</th></tr></thead>
            <tbody>
              {result.detections.map((d, i) => (
                <tr key={i}>
                  <td>{d.class}</td>
                  <td className="mono" style={{ color: 'var(--t-cyan)' }}>{d.confidence}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="result-actions">
        {result.report_available && (
          <button className="btn btn--primary" onClick={onDownload} disabled={dlLoading}>
            {dlLoading ? <div className="spin" /> : <Download size={14} />} Download PDF
          </button>
        )}
        <button className="btn btn--ghost" onClick={onNew}><RefreshCw size={14} /> New Inspection</button>
      </div>
    </div>
  )
}

// ── Upload mode ───────────────────────────────────────────────────────────────
function UploadMode({ material, matInfo }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [detecting, setDetecting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [dlLoading, setDlLoading] = useState(false)
  const inputRef = useRef(null)
  const dropRef = useRef(null)

  const validate = (f) => {
    setError(''); setResult(null)
    if (!f) return
    if (!ALLOWED.includes(f.type)) { setError('Unsupported file type. Please upload JPG or PNG.'); return }
    if (f.size > MAX_MB * 1024 * 1024) { setError(`File too large. Max ${MAX_MB} MB.`); return }
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const handleDrop = (e) => {
    e.preventDefault()
    dropRef.current?.classList.remove('drop--over')
    validate(e.dataTransfer.files?.[0])
  }

  const handleDetect = async () => {
    if (!file || detecting) return
    setDetecting(true); setError('')
    try {
      const res = await uploadMaterialInspection(material, file)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed. Please try again.')
    } finally { setDetecting(false) }
  }

  const handleNew = () => {
    setFile(null); setPreview(null); setResult(null); setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleDownload = async () => {
    if (!result) return
    setDlLoading(true)
    try { await getMaterialReportDownload(result.material || material, result.inspection_id) }
    catch { alert('Report not available.') }
    finally { setDlLoading(false) }
  }

  if (result) {
    return (
      <ResultPanel
        result={result}
        material={material}
        onNew={handleNew}
        onDownload={handleDownload}
        dlLoading={dlLoading}
      />
    )
  }

  return (
    <div className="insp-upload">
      {!file ? (
        <div
          ref={dropRef}
          className="drop-zone"
          onDrop={handleDrop}
          onDragOver={e => { e.preventDefault(); dropRef.current?.classList.add('drop--over') }}
          onDragLeave={() => dropRef.current?.classList.remove('drop--over')}
          onClick={() => inputRef.current?.click()}
        >
          <div className="drop-zone__icon" style={{ color: matInfo?.color }}>
            <ImageIcon size={40} />
          </div>
          <p className="drop-zone__title">Upload {matInfo?.label} Surface Image</p>
          <p className="drop-zone__sub">Drag &amp; drop here, or click to browse</p>
          <p className="drop-zone__hint">JPG, JPEG, PNG · Max {MAX_MB} MB</p>
          <button className="btn btn--primary" style={{ marginTop: 20, background: matInfo?.color, borderColor: matInfo?.color, color: '#050d14' }} type="button">
            <Upload size={14} /> Browse Image
          </button>
          <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,image/jpeg,image/png" style={{ display: 'none' }} onChange={e => validate(e.target.files?.[0])} />
        </div>
      ) : (
        <div className="preview-panel">
          <div className="preview-panel__img-wrap">
            <img src={preview} alt="Selected" className="preview-panel__img" />
            <button className="preview-panel__remove" onClick={handleNew} title="Remove"><X size={15} /></button>
          </div>
          <div className="preview-panel__info">
            <span className="preview-panel__name">{file.name}</span>
            <span className="preview-panel__size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
          </div>
          <div className="insp-actions">
            <button className="btn btn--ghost" onClick={handleNew} disabled={detecting}><RefreshCw size={14} /> Change</button>
            <button className="btn btn--primary" onClick={handleDetect} disabled={detecting} style={{ background: matInfo?.color, borderColor: matInfo?.color, color: '#050d14' }}>
              {detecting ? <><div className="spin" /> Detecting…</> : <><ScanLine size={14} /> Detect Defects</>}
            </button>
          </div>
        </div>
      )}
      {error && <ErrorMessage message={error} />}
    </div>
  )
}

// ── Camera mode ───────────────────────────────────────────────────────────────
function CameraMode({ material, matInfo }) {
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
    } catch { setRunning(false) }
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  useEffect(() => {
    if (running) { pollRef.current = setInterval(fetchStatus, 1000) }
    else { clearInterval(pollRef.current) }
    return () => clearInterval(pollRef.current)
  }, [running, fetchStatus])

  const handleStart = async () => {
    setLoading(true); setError('')
    try { await startCamera(material); setRunning(true); await fetchStatus() }
    catch (err) { setError(err.response?.data?.detail || 'Failed to start camera.') }
    finally { setLoading(false) }
  }

  const handleStop = async () => {
    setLoading(true)
    try { await stopCamera(); setRunning(false); setDetection(null) }
    catch (err) { setError(err.response?.data?.detail || 'Failed to stop camera.') }
    finally { setLoading(false) }
  }

  const handleCapture = async () => {
    setSaveLoading(true); setSaveError(''); setLastSaved(null)
    try { const res = await captureInspection(); setLastSaved(res.data) }
    catch (err) { setSaveError(err.response?.data?.detail || 'Capture failed.') }
    finally { setSaveLoading(false) }
  }

  const handleDownload = async () => {
    if (!lastSaved) return
    setDlLoading(true)
    try { await getMaterialReportDownload(lastSaved.material || material, lastSaved.inspection_id) }
    catch { alert('Report not available.') }
    finally { setDlLoading(false) }
  }

  return (
    <div className="cam-layout">
      <div className="cam-panel">
        <div className="cam-panel__hdr">
          <span className="cam-panel__title"><Camera size={16} /> Live Camera Feed</span>
          {running && <span className="live-badge">● LIVE</span>}
        </div>

        <div className="cam-view">
          {running ? (
            <img src={streamUrl} alt="Live YOLO stream" className="cam-stream" onError={() => setError('Camera stream disconnected.')} />
          ) : (
            <div className="cam-placeholder">
              <CameraOff size={44} />
              <p>Camera not started</p>
              <p style={{ fontSize: 11, marginTop: 4, color: 'var(--t-muted)' }}>Click Start Camera to begin inspection</p>
            </div>
          )}
        </div>

        {error && <ErrorMessage message={error} onRetry={fetchStatus} />}

        <div className="insp-actions">
          {!running ? (
            <button className="btn btn--primary" onClick={handleStart} disabled={loading} style={{ background: matInfo?.color, borderColor: matInfo?.color, color: '#050d14' }}>
              {loading ? <div className="spin" /> : <Camera size={15} />} Start Camera
            </button>
          ) : (
            <button className="btn btn--danger" onClick={handleStop} disabled={loading}>
              <CameraOff size={15} /> Stop Camera
            </button>
          )}
          <button className="btn btn--ghost" onClick={handleCapture} disabled={!running || saveLoading}>
            {saveLoading ? <div className="spin" /> : <Save size={15} />} Save Inspection
          </button>
        </div>
      </div>

      <div className="cam-info">
        <div className="cam-info__section">
          <h3 className="cam-info__title">Current Detection</h3>
          {detection ? (
            <div className="result-grid">
              <div className="result-item"><span className="result-label">Status</span><StatusBadge value={detection.status} /></div>
              <div className="result-item"><span className="result-label">Quality Score</span><span className="result-val result-val--score">{detection.quality_score}%</span></div>
              <div className="result-item"><span className="result-label">Severity</span><StatusBadge value={detection.severity} /></div>
              <div className="result-item"><span className="result-label">FPS</span><span className="result-val">{detection.fps}</span></div>
              <div className="result-item result-item--full"><span className="result-label">Remarks</span><span className="result-val result-val--muted">{detection.remarks}</span></div>
            </div>
          ) : <p className="empty-text">No detection data. Start camera first.</p>}
        </div>

        {detection?.detections?.length > 0 && (
          <div className="cam-info__section">
            <h3 className="cam-info__title">Detected Objects</h3>
            <div className="tag-list">
              {detection.detections.map((d, i) => (
                <div key={i} className="det-tag">
                  <span className="det-tag__cls">{d.class}</span>
                  <span className="det-tag__conf">{d.confidence}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {saveError && <ErrorMessage message={saveError} />}

        {lastSaved && (
          <div className="save-result">
            <div className="save-result__hdr"><CheckCircle size={16} /><span>Inspection Saved</span></div>
            <div className="save-result__body">
              {[['ID', <span className="mono">{lastSaved.inspection_id}</span>], ['Status', <StatusBadge value={lastSaved.status} />], ['Score', `${lastSaved.quality_score}%`], ['Defects', lastSaved.total_defects]].map(([l, v]) => (
                <div key={l} className="save-result__row"><span>{l}</span><span>{v}</span></div>
              ))}
            </div>
            {lastSaved.report_available && (
              <button className="btn btn--sm btn--primary" style={{ marginTop: 10 }} onClick={handleDownload} disabled={dlLoading}>
                {dlLoading ? <div className="spin" /> : <Download size={13} />} Download PDF
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main Inspection page ──────────────────────────────────────────────────────
export default function Inspection() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const initMat = searchParams.get('material') || ''
  const [material, setMaterial] = useState(initMat)
  const [mode, setMode] = useState('upload')
  const [dropOpen, setDropOpen] = useState(false)

  const matInfo = MATERIALS.find(m => m.key === material)

  const handleMaterialSelect = (key) => {
    setMaterial(key)
    setDropOpen(false)
    navigate(`/inspection?material=${key}`, { replace: true })
  }

  return (
    <div className="page-content">
      {/* Material selector */}
      <div className="insp-selector">
        <div className="insp-selector__label">
          <ScanLine size={15} />
          <span>Select Product to Inspect</span>
        </div>
        <div className="insp-dropdown">
          <button className="insp-dropdown__btn" onClick={() => setDropOpen(o => !o)}>
            {matInfo ? (
              <span style={{ color: matInfo.color }}>{matInfo.label}</span>
            ) : (
              <span style={{ color: 'var(--t-muted)' }}>Select Product ▾</span>
            )}
            <ChevronDown size={15} style={{ color: 'var(--t-muted)', transform: dropOpen ? 'rotate(180deg)' : 'none', transition: 'transform .2s' }} />
          </button>
          {dropOpen && (
            <div className="insp-dropdown__menu">
              {MATERIALS.map(m => (
                <button
                  key={m.key}
                  className={`insp-dropdown__item${material === m.key ? ' insp-dropdown__item--active' : ''}`}
                  onClick={() => handleMaterialSelect(m.key)}
                  style={material === m.key ? { color: m.color } : {}}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {!material ? (
        <div className="insp-empty">
          <ScanLine size={52} style={{ color: 'var(--t-muted)', opacity: .4 }} />
          <h2>Select a Product</h2>
          <p>Choose a material from the dropdown above to begin inspection.</p>
          <div className="insp-empty__chips">
            {MATERIALS.map(m => (
              <button key={m.key} className="insp-chip" style={{ borderColor: `${m.color}50`, color: m.color }} onClick={() => handleMaterialSelect(m.key)}>
                {m.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          {/* Mode tabs */}
          <div className="tab-bar" style={{ marginBottom: 24 }}>
            <button className={`tab-btn${mode === 'upload' ? ' tab-btn--active' : ''}`} style={mode === 'upload' ? { '--tc': matInfo?.color } : {}} onClick={() => setMode('upload')}>
              <Upload size={14} /> Upload Image
            </button>
            <button className={`tab-btn${mode === 'camera' ? ' tab-btn--active' : ''}`} style={mode === 'camera' ? { '--tc': matInfo?.color } : {}} onClick={() => setMode('camera')}>
              <Camera size={14} /> Live Camera
            </button>
          </div>

          {/* Inspection panel */}
          <div className="insp-panel">
            <div className="insp-panel__hdr" style={{ borderColor: `${matInfo?.color}30` }}>
              <div className="insp-panel__title" style={{ color: matInfo?.color }}>
                <ScanLine size={16} />
                <span>{matInfo?.label} Inspection</span>
              </div>
              <div className="insp-panel__defects">
                {matInfo?.defects.map(d => (
                  <span key={d} className="insp-defect-tag" style={{ borderColor: `${matInfo.color}30`, color: matInfo.color, background: `${matInfo.color}0d` }}>{d}</span>
                ))}
              </div>
            </div>

            <div className="insp-panel__body">
              {mode === 'upload'
                ? <UploadMode key={material} material={material} matInfo={matInfo} />
                : <CameraMode key={material} material={material} matInfo={matInfo} />
              }
            </div>
          </div>
        </>
      )}
    </div>
  )
}
