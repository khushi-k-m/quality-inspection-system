import { useEffect, useState } from 'react'
import { getReports, downloadReport } from '../api/reports'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { Download, FileText } from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getReports()
      setReports(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load reports.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleDownload = async (id) => {
    setDownloading(id)
    try { await downloadReport(id) }
    catch { alert('Report not available or could not be generated.') }
    finally { setDownloading('') }
  }

  return (
    <div className="page">
      <Header title="Reports" />
      <div className="page__body">
        {loading && <Loading text="Loading reports..." />}
        {error && <ErrorMessage message={error} onRetry={load} />}

        {!loading && !error && (
          <>
            {reports.length === 0 ? (
              <p className="empty-text">No reports available.</p>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Inspection ID</th>
                      <th>Date & Time</th>
                      <th>Status</th>
                      <th>Quality Score</th>
                      <th>Report</th>
                      <th>Download</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.map(r => (
                      <tr key={r.inspection_id}>
                        <td className="mono">{r.inspection_id}</td>
                        <td>{r.timestamp}</td>
                        <td><StatusBadge value={r.status} /></td>
                        <td>{r.quality_score}%</td>
                        <td>
                          {r.report_available
                            ? <span className="text-green"><FileText size={14} /> Available</span>
                            : <span className="text-muted">Will generate on download</span>
                          }
                        </td>
                        <td>
                          <button
                            className="btn btn--sm btn--primary"
                            onClick={() => handleDownload(r.inspection_id)}
                            disabled={downloading === r.inspection_id}
                          >
                            {downloading === r.inspection_id
                              ? <div className="spinner spinner--sm" />
                              : <Download size={14} />
                            }
                            PDF
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
