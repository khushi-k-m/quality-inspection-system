import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getInspection } from '../api/inspections'
import { downloadReport } from '../api/reports'
import apiClient from '../api/apiClient'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { ArrowLeft, Download, Image } from 'lucide-react'

export default function InspectionDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [dlLoading, setDlLoading] = useState(false)
  const [imgSrc, setImgSrc] = useState(null)

  useEffect(() => {
    setLoading(true)
    getInspection(id)
      .then(r => {
        setData(r.data)
        if (r.data.image_url) {
          // Fetch image with auth header, convert to object URL
          apiClient.get(r.data.image_url, { responseType: 'blob' })
            .then(res => setImgSrc(URL.createObjectURL(res.data)))
            .catch(() => setImgSrc(null))
        }
      })
      .catch(err => setError(err.response?.data?.detail || 'Inspection not found.'))
      .finally(() => setLoading(false))
  }, [id])

  // Revoke object URL on unmount
  useEffect(() => () => { if (imgSrc) URL.revokeObjectURL(imgSrc) }, [imgSrc])

  const handleDownload = async () => {
    setDlLoading(true)
    try { await downloadReport(id) }
    catch { alert('Report not available.') }
    finally { setDlLoading(false) }
  }

  return (
    <div className="page">
      <Header title="Inspection Details" />
      <div className="page__body">
        <button className="btn btn--ghost btn--sm" style={{ marginBottom: 16 }} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Back
        </button>

        {loading && <Loading text="Loading inspection..." />}
        {error && <ErrorMessage message={error} />}

        {!loading && !error && data && (
          <div className="detail-layout">
            <div className="detail-main">
              <div className="card">
                <h3 className="card__title">Inspection Information</h3>
                <div style={{ marginTop: 16 }}>
                  {[
                    ['Inspection ID', <span className="mono">{data.inspection_id}</span>],
                    ['Date & Time', data.timestamp],
                    ['Inspector', data.inspector],
                    ['Status', <StatusBadge value={data.status} />],
                    ['Quality Score', <span style={{ color: 'var(--green)', fontFamily: 'var(--mono)', fontSize: 15 }}>{data.quality_score}%</span>],
                    ['Severity', <StatusBadge value={data.severity} />],
                    ['Remarks', data.remarks],
                  ].map(([label, val]) => (
                    <div key={label} className="detail-row">
                      <span style={{ color: 'var(--muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '.7px' }}>{label}</span>
                      <span>{val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card" style={{ marginTop: 14 }}>
                <h3 className="card__title">Defect Summary</h3>
                <div className="defect-counts" style={{ marginTop: 16 }}>
                  {[
                    { label: 'Total', value: data.total_defects, color: '#6366f1' },
                    { label: 'Scratches', value: data.scratches, color: '#f97316' },
                    { label: 'Dents', value: data.dents, color: '#eab308' },
                    { label: 'Rust', value: data.rust, color: '#ef4444' },
                    { label: 'Other', value: data.other, color: '#8b5cf6' },
                  ].map(d => (
                    <div key={d.label} className="defect-count-item">
                      <span className="defect-count-label">{d.label}</span>
                      <span className="defect-count-value" style={{ color: d.color }}>{d.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                className="btn btn--primary"
                style={{ marginTop: 14 }}
                onClick={handleDownload}
                disabled={dlLoading}
              >
                {dlLoading ? <div className="spinner spinner--sm" /> : <Download size={16} />}
                Download PDF Report
              </button>
            </div>

            <div className="detail-side">
              <div className="card">
                <h3 className="card__title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Image size={16} /> Inspection Image
                </h3>
                {imgSrc ? (
                  <img src={imgSrc} alt="Inspection" className="detail-image" />
                ) : (
                  <p className="empty-text">No image available.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
