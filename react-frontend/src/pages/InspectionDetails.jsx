import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { getMaterialInspection } from '../api/inspections'
import { getMaterialReportDownload } from '../api/reports'
import apiClient from '../api/apiClient'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { ArrowLeft, Download, ImageIcon } from 'lucide-react'

const MAT_LABEL = { steel: 'Steel', metal: 'Metal', fabric: 'Fabric', pcb: 'PCB', welding: 'Welding' }

export default function InspectionDetails() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const material = searchParams.get('material') || 'steel'
  const navigate = useNavigate()

  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [dlLoading, setDlLoading] = useState(false)
  const [imgSrc, setImgSrc]       = useState(null)

  useEffect(() => {
    setLoading(true)
    getMaterialInspection(material, id)
      .then(r => {
        setData(r.data)
        if (r.data.image_url) {
          apiClient.get(r.data.image_url, { responseType: 'blob' })
            .then(res => setImgSrc(URL.createObjectURL(res.data)))
            .catch(() => setImgSrc(null))
        }
      })
      .catch(err => setError(err.response?.data?.detail || 'Inspection not found.'))
      .finally(() => setLoading(false))
  }, [id, material])

  useEffect(() => () => { if (imgSrc) URL.revokeObjectURL(imgSrc) }, [imgSrc])

  const handleDownload = async () => {
    setDlLoading(true)
    try { await getMaterialReportDownload(material, id) }
    catch { alert('Report not available.') }
    finally { setDlLoading(false) }
  }

  const defectCount = data ? (data.total_defects ?? data.defect_count ?? 0) : 0

  return (
    <div className="page-content">
      <button className="btn btn--ghost btn--sm" style={{ marginBottom: 20 }} onClick={() => navigate(-1)}>
        <ArrowLeft size={14} /> Back
      </button>

      {loading && <Loading text="Loading inspection…" />}
      {error && <ErrorMessage message={error} />}

      {!loading && !error && data && (
        <div className="detail-layout">
          <div className="detail-main">
            <div className="glass-card" style={{ padding: 24 }}>
              <h3 className="glass-card__title">Inspection Information</h3>
              <div style={{ marginTop: 16 }}>
                {[
                  ['Inspection ID', <span className="mono">{data.inspection_id}</span>],
                  ['Date & Time',   data.timestamp],
                  ['Material',      data.material || MAT_LABEL[material]],
                  ['Inspector',     data.inspector],
                  ['Status',        <StatusBadge value={data.status} />],
                  ['Quality Score', <span style={{ color: '#4ade80', fontFamily: 'monospace', fontSize: 15 }}>{data.quality_score}%</span>],
                  ['Severity',      <StatusBadge value={data.severity} />],
                  ['Remarks',       data.remarks],
                ].map(([label, val]) => (
                  <div key={label} className="detail-row">
                    <span className="detail-row__label">{label}</span>
                    <span>{val}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card" style={{ padding: 24, marginTop: 14 }}>
              <h3 className="glass-card__title">Defect Summary</h3>
              {material === 'steel' ? (
                <div className="defect-counts">
                  {[
                    { label: 'Total',     value: defectCount,    color: '#6366f1' },
                    { label: 'Scratches', value: data.scratches, color: '#f97316' },
                    { label: 'Dents',     value: data.dents,     color: '#eab308' },
                    { label: 'Rust',      value: data.rust,      color: '#ef4444' },
                    { label: 'Other',     value: data.other,     color: '#8b5cf6' },
                  ].map(d => (
                    <div key={d.label} className="defect-count-item">
                      <span className="defect-count-label">{d.label}</span>
                      <span className="defect-count-value" style={{ color: d.color }}>{d.value ?? 0}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <div className="defect-counts" style={{ marginTop: 16 }}>
                    <div className="defect-count-item">
                      <span className="defect-count-label">Total</span>
                      <span className="defect-count-value" style={{ color: '#6366f1' }}>{defectCount}</span>
                    </div>
                  </div>
                  {data.defects?.length > 0 && (
                    <div className="tbl-wrap" style={{ marginTop: 14 }}>
                      <table className="tbl">
                        <thead><tr><th>Defect Class</th><th>Confidence</th></tr></thead>
                        <tbody>
                          {data.defects.map((d, i) => (
                            <tr key={i}>
                              <td>{d.defect_class}</td>
                              <td className="mono" style={{ color: 'var(--t-cyan)' }}>{(d.confidence * 100).toFixed(1)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}
            </div>

            <button className="btn btn--primary" style={{ marginTop: 14 }} onClick={handleDownload} disabled={dlLoading}>
              {dlLoading ? <div className="spin" /> : <Download size={15} />} Download PDF Report
            </button>
          </div>

          <div className="detail-side">
            <div className="glass-card" style={{ padding: 24 }}>
              <h3 className="glass-card__title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ImageIcon size={15} /> Inspection Image
              </h3>
              {imgSrc
                ? <img src={imgSrc} alt="Inspection" style={{ width: '100%', marginTop: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,.07)' }} />
                : <p className="empty-text">No image available.</p>
              }
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
