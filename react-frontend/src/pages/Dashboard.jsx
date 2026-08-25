import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSummary } from '../api/analytics'
import { getInspections } from '../api/inspections'
import Header from '../components/Header'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import {
  ClipboardCheck, CheckCircle, AlertTriangle, XCircle,
  Star, TrendingDown, Activity, Layers
} from 'lucide-react'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [s, r] = await Promise.all([
        getSummary(),
        getInspections({ page: 1, limit: 5 })
      ])
      setSummary(s.data)
      setRecent(r.data.items)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to connect to inspection server.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="page">
      <Header title="Dashboard" />
      <div className="page__body">
        {loading && <Loading text="Loading dashboard..." />}
        {error && <ErrorMessage message={error} onRetry={load} />}

        {!loading && !error && summary && (
          <>
            <div className="stat-grid">
              <StatCard label="Total Inspections" value={summary.total_inspections} icon={ClipboardCheck} color="#6366f1" />
              <StatCard label="PASS" value={summary.pass_count} icon={CheckCircle} color="#22c55e" sub={`${summary.quality_rate}%`} />
              <StatCard label="REWORK" value={summary.rework_count} icon={AlertTriangle} color="#f97316" sub={`${summary.rework_rate}%`} />
              <StatCard label="FAIL" value={summary.fail_count} icon={XCircle} color="#ef4444" sub={`${summary.failure_rate}%`} />
              <StatCard label="Avg Quality Score" value={`${summary.avg_quality_score}%`} icon={Star} color="#eab308" />
              <StatCard label="Total Defects" value={summary.total_defects} icon={Layers} color="#8b5cf6" />
              <StatCard label="Avg Defects/Inspection" value={summary.avg_defects_per_inspection} icon={Activity} color="#06b6d4" />
              <StatCard label="Failure Rate" value={`${summary.failure_rate}%`} icon={TrendingDown} color="#f43f5e" />
            </div>

            <div className="section">
              <div className="section__header">
                <h2 className="section__title">Recent Inspections</h2>
                <button className="btn btn--ghost btn--sm" onClick={() => navigate('/inspection-history')}>
                  View All
                </button>
              </div>

              {recent.length === 0 ? (
                <p className="empty-text">No inspection records available.</p>
              ) : (
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Inspection ID</th>
                        <th>Date & Time</th>
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
                          className="table__row--clickable"
                          onClick={() => navigate(`/inspection-history/${r.inspection_id}`)}
                        >
                          <td className="mono">{r.inspection_id}</td>
                          <td>{r.timestamp}</td>
                          <td>{r.total_defects}</td>
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
    </div>
  )
}
