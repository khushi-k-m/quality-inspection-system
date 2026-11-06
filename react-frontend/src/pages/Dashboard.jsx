import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMaterialAnalytics } from '../api/analytics'
import { getMaterialInspections } from '../api/inspections'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { ClipboardCheck, CheckCircle, AlertTriangle, XCircle, Star, Layers, Activity, TrendingDown } from 'lucide-react'

const MATERIALS = [
  { key: 'steel',   label: 'Steel',   color: '#38bdf8' },
  { key: 'metal',   label: 'Metal',   color: '#818cf8' },
  { key: 'fabric',  label: 'Fabric',  color: '#f472b6' },
  { key: 'pcb',     label: 'PCB',     color: '#34d399' },
  { key: 'welding', label: 'Welding', color: '#fb923c' },
]

export default function Dashboard() {
  const [material, setMaterial] = useState('steel')
  const [summary, setSummary] = useState(null)
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true); setError('')
    try {
      const [a, r] = await Promise.all([
        getMaterialAnalytics(material),
        getMaterialInspections(material, { page: 1, limit: 5 }),
      ])
      setSummary(a.data)
      setRecent(r.data.items)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to connect to inspection server.')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [material])

  const mat = MATERIALS.find(m => m.key === material)

  return (
    <div className="page-content">
      {/* Material tabs */}
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

      {loading && <Loading text={`Loading ${mat?.label} dashboard…`} />}
      {error && <ErrorMessage message={error} onRetry={load} />}

      {!loading && !error && summary && (
        <>
          <div className="stat-grid">
            <StatCard label="Total Inspections"      value={summary.total_inspections}           icon={ClipboardCheck} color="#6366f1" />
            <StatCard label="PASS"                   value={summary.pass_count}                  icon={CheckCircle}    color="#22c55e" sub={`${summary.quality_rate}%`} />
            <StatCard label="REWORK"                 value={summary.rework_count}                icon={AlertTriangle}  color="#f97316" sub={`${summary.rework_rate}%`} />
            <StatCard label="FAIL"                   value={summary.fail_count}                  icon={XCircle}        color="#ef4444" sub={`${summary.failure_rate}%`} />
            <StatCard label="Avg Quality Score"      value={`${summary.avg_quality_score}%`}     icon={Star}           color="#eab308" />
            <StatCard label="Total Defects"          value={summary.total_defects}               icon={Layers}         color="#8b5cf6" />
            <StatCard label="Avg Defects/Inspection" value={summary.avg_defects_per_inspection}  icon={Activity}       color="#06b6d4" />
            <StatCard label="Failure Rate"           value={`${summary.failure_rate}%`}          icon={TrendingDown}   color="#f43f5e" />
          </div>

          <div className="glass-section">
            <div className="glass-section__hdr">
              <h2 className="glass-section__title">Recent {mat?.label} Inspections</h2>
              <button className="btn btn--ghost btn--sm" onClick={() => navigate(`/inspection-history?material=${material}`)}>
                View All
              </button>
            </div>
            {recent.length === 0 ? (
              <p className="empty-text">No inspection records available.</p>
            ) : (
              <div className="tbl-wrap">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Inspection ID</th>
                      <th>Date &amp; Time</th>
                      <th>Defects</th>
                      <th>Score</th>
                      <th>Severity</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map(r => (
                      <tr
                        key={r.inspection_id}
                        className="tbl__row--click"
                        onClick={() => navigate(`/inspection-history/${r.inspection_id}?material=${material}`)}
                      >
                        <td className="mono">{r.inspection_id}</td>
                        <td>{r.timestamp}</td>
                        <td>{r.total_defects ?? r.defect_count}</td>
                        <td>{r.quality_score}%</td>
                        <td><StatusBadge value={r.severity} /></td>
                        <td><StatusBadge value={r.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
