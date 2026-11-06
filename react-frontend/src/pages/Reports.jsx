import { useEffect, useState } from 'react'
import { getMaterialReports, getMaterialReportDownload } from '../api/reports'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { Download, FileText } from 'lucide-react'

const MATERIALS = [
  { key: 'steel',   label: 'Steel',   color: '#38bdf8' },
  { key: 'metal',   label: 'Metal',   color: '#818cf8' },
  { key: 'fabric',  label: 'Fabric',  color: '#f472b6' },
  { key: 'pcb',     label: 'PCB',     color: '#34d399' },
  { key: 'welding', label: 'Welding', color: '#fb923c' },
]

export default function Reports() {
  const [material, setMaterial] = useState('steel')
  const [reports, setReports]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [downloading, setDownloading] = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try {
      const res = await getMaterialReports(material)
      setReports(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load reports.')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [material])

  const handleDownload = async (id) => {
    setDownloading(id)
    try { await getMaterialReportDownload(material, id) }
    catch { alert('Report not available or could not be generated.') }
    finally { setDownloading('') }
  }

  const mat = MATERIALS.find(m => m.key === material)

  return (
    <div className="page-content">
      <div className="tab-bar">
        {MATERIALS.map(m => (
          <button
            key={m.key}
            className={`tab-btn${material === m.key ? ' tab-btn--active' : ''}`}
            style={material === m.key ? { '--tc': m.color } : {}}
            onClick={() => setMaterial(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      {loading && <Loading text={`Loading ${mat?.label} reports…`} />}
      {error && <ErrorMessage message={error} onRetry={load} />}

      {!loading && !error && (
        reports.length === 0 ? (
          <p className="empty-text">No reports available.</p>
        ) : (
          <div className="tbl-wrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Inspection ID</th><th>Date &amp; Time</th><th>Material</th>
                  <th>Status</th><th>Quality Score</th><th>Report</th><th>Download</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(r => (
                  <tr key={r.inspection_id}>
                    <td className="mono">{r.inspection_id}</td>
                    <td>{r.timestamp}</td>
                    <td>{r.material || mat?.label}</td>
                    <td><StatusBadge value={r.status} /></td>
                    <td>{r.quality_score}%</td>
                    <td>
                      {r.report_available
                        ? <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: '#4ade80', fontSize: 11 }}><FileText size={13} /> Available</span>
                        : <span style={{ color: 'var(--t-muted)', fontSize: 11 }}>Will generate on download</span>
                      }
                    </td>
                    <td>
                      <button className="btn btn--sm btn--primary" onClick={() => handleDownload(r.inspection_id)} disabled={downloading === r.inspection_id}>
                        {downloading === r.inspection_id ? <div className="spin" /> : <Download size={13} />} PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  )
}
