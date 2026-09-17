import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { getMaterialInspections } from '../api/inspections'
import { getMaterialReportDownload } from '../api/reports'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { Search, ChevronLeft, ChevronRight, Download } from 'lucide-react'

const MATERIALS  = [
  { key: 'steel',   label: 'Steel' },
  { key: 'metal',   label: 'Metal' },
  { key: 'fabric',  label: 'Fabric' },
  { key: 'pcb',     label: 'PCB' },
  { key: 'welding', label: 'Welding' },
]
const STATUSES   = ['', 'PASS', 'REWORK', 'FAIL']
const SEVERITIES = ['', 'NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export default function InspectionHistory() {
  const [searchParams] = useSearchParams()
  const [material, setMaterial] = useState(searchParams.get('material') || 'steel')
  const [data, setData]         = useState({ items: [], total: 0, pages: 1 })
  const [page, setPage]         = useState(1)
  const [filters, setFilters]   = useState({ status: '', severity: '', search: '' })
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [dlId, setDlId]         = useState('')
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getMaterialInspections(material, { page, limit: 20, ...filters })
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load inspections.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [material, page, filters])

  const setFilter = (key, val) => {
    setFilters(f => ({ ...f, [key]: val }))
    setPage(1)
  }

  const changeMaterial = (m) => {
    setMaterial(m)
    setPage(1)
    setFilters({ status: '', severity: '', search: '' })
  }

  const handleDownload = async (id) => {
    setDlId(id)
    try { await getMaterialReportDownload(material, id) }
    catch { alert('Report not available or could not be generated.') }
    finally { setDlId('') }
  }

  const defectKey = (r) => r.total_defects ?? r.defect_count ?? 0

  return (
    <div className="page">
      <Header title="Inspection History" />
      <div className="page__body">

        <div className="inspection-mode-bar" style={{ marginBottom: 20 }}>
          {MATERIALS.map(m => (
            <button
              key={m.key}
              className={`inspection-mode-btn ${material === m.key ? 'inspection-mode-btn--active' : ''}`}
              onClick={() => changeMaterial(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="filters-bar">
          <div className="search-wrap">
            <Search size={16} />
            <input
              className="search-input"
              placeholder="Search inspection ID..."
              value={filters.search}
              onChange={e => setFilter('search', e.target.value)}
            />
          </div>
          <select className="filter-select" value={filters.status} onChange={e => setFilter('status', e.target.value)}>
            {STATUSES.map(s => <option key={s} value={s}>{s || 'All Status'}</option>)}
          </select>
          <select className="filter-select" value={filters.severity} onChange={e => setFilter('severity', e.target.value)}>
            {SEVERITIES.map(s => <option key={s} value={s}>{s || 'All Severity'}</option>)}
          </select>
          <span className="filter-count">{data.total} records</span>
        </div>

        {loading && <Loading text={`Loading ${material} inspections...`} />}
        {error   && <ErrorMessage message={error} onRetry={load} />}

        {!loading && !error && (
          <>
            {data.items.length === 0 ? (
              <p className="empty-text">No inspection records available.</p>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Inspection ID</th>
                      <th>Date &amp; Time</th>
                      <th>Material</th>
                      <th>Defects</th>
                      <th>Score</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Inspector</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map(r => (
                      <tr key={r.inspection_id}>
                        <td className="mono">{r.inspection_id}</td>
                        <td>{r.timestamp}</td>
                        <td>{r.material || (material === 'steel' ? 'Steel' : 'Metal')}</td>
                        <td>{defectKey(r)}</td>
                        <td>{r.quality_score}%</td>
                        <td><StatusBadge value={r.severity} /></td>
                        <td><StatusBadge value={r.status} /></td>
                        <td>{r.inspector}</td>
                        <td style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn btn--sm btn--ghost"
                            onClick={() => navigate(`/inspection-history/${r.inspection_id}?material=${material}`)}
                          >
                            View
                          </button>
                          <button
                            className="btn btn--sm btn--primary"
                            onClick={() => handleDownload(r.inspection_id)}
                            disabled={dlId === r.inspection_id}
                            title="Download PDF"
                          >
                            {dlId === r.inspection_id
                              ? <div className="spinner spinner--sm" />
                              : <Download size={13} />
                            }
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {data.pages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn--sm btn--ghost"
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  <ChevronLeft size={16} /> Prev
                </button>
                <span className="pagination__info">Page {page} of {data.pages}</span>
                <button
                  className="btn btn--sm btn--ghost"
                  disabled={page === data.pages}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
