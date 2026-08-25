import { useEffect, useState } from 'react'
import Header from '../components/Header'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import StatCard from '../components/StatCard'
import {
  getSummary, getStatusDistribution, getSeverityDistribution,
  getDefectDistribution, getQualityTrend, getDefectTrend, getDailyVolume
} from '../api/analytics'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  LineChart, Line, CartesianGrid, ResponsiveContainer
} from 'recharts'
import { ClipboardCheck, CheckCircle, XCircle, AlertTriangle, Star } from 'lucide-react'

const STATUS_COLORS = { PASS: '#22c55e', REWORK: '#f97316', FAIL: '#ef4444' }
const SEVERITY_COLORS = { NONE: '#64748b', LOW: '#22c55e', MEDIUM: '#f97316', HIGH: '#ef4444', CRITICAL: '#dc2626' }
const DEFECT_COLORS = ['#6366f1', '#f97316', '#ef4444', '#8b5cf6']

export default function Analytics() {
  const [summary, setSummary] = useState(null)
  const [statusDist, setStatusDist] = useState([])
  const [severityDist, setSeverityDist] = useState([])
  const [defectDist, setDefectDist] = useState([])
  const [qualityTrend, setQualityTrend] = useState([])
  const [defectTrend, setDefectTrend] = useState([])
  const [dailyVol, setDailyVol] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [s, sd, sv, dd, qt, dt, dv] = await Promise.all([
        getSummary(), getStatusDistribution(), getSeverityDistribution(),
        getDefectDistribution(), getQualityTrend(), getDefectTrend(), getDailyVolume()
      ])
      setSummary(s.data)
      setStatusDist(sd.data)
      setSeverityDist(sv.data)
      setDefectDist(dd.data)
      setQualityTrend(qt.data)
      setDefectTrend(dt.data)
      setDailyVol(dv.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const noData = (arr) => !arr || arr.length === 0 || arr.every(i => (i.count ?? i.total_defects ?? i.quality_score ?? 0) === 0)

  return (
    <div className="page">
      <Header title="Analytics" />
      <div className="page__body">
        {loading && <Loading text="Loading analytics..." />}
        {error && <ErrorMessage message={error} onRetry={load} />}

        {!loading && !error && (
          <>
            {summary && (
              <div className="stat-grid">
                <StatCard label="Total Inspections" value={summary.total_inspections} icon={ClipboardCheck} color="#6366f1" />
                <StatCard label="PASS" value={summary.pass_count} icon={CheckCircle} color="#22c55e" sub={`${summary.quality_rate}%`} />
                <StatCard label="REWORK" value={summary.rework_count} icon={AlertTriangle} color="#f97316" sub={`${summary.rework_rate}%`} />
                <StatCard label="FAIL" value={summary.fail_count} icon={XCircle} color="#ef4444" sub={`${summary.failure_rate}%`} />
                <StatCard label="Avg Quality Score" value={`${summary.avg_quality_score}%`} icon={Star} color="#eab308" />
              </div>
            )}

            <div className="charts-grid">
              {/* Status Distribution */}
              <div className="chart-card">
                <h3 className="chart-title">Status Distribution</h3>
                {noData(statusDist) ? <p className="empty-text">No inspection data available.</p> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie data={statusDist} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={90} label={({ status, percent }) => `${status} ${(percent * 100).toFixed(0)}%`}>
                        {statusDist.map((e, i) => <Cell key={i} fill={STATUS_COLORS[e.status] || '#6366f1'} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Severity Distribution */}
              <div className="chart-card">
                <h3 className="chart-title">Severity Distribution</h3>
                {noData(severityDist) ? <p className="empty-text">No inspection data available.</p> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={severityDist}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="severity" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', color: '#e2e8f0' }} />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {severityDist.map((e, i) => <Cell key={i} fill={SEVERITY_COLORS[e.severity] || '#6366f1'} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Defect Distribution */}
              <div className="chart-card">
                <h3 className="chart-title">Defect Distribution</h3>
                {noData(defectDist) ? <p className="empty-text">No defect data available.</p> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={defectDist}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="type" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', color: '#e2e8f0' }} />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {defectDist.map((e, i) => <Cell key={i} fill={DEFECT_COLORS[i % DEFECT_COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Daily Volume */}
              <div className="chart-card">
                <h3 className="chart-title">Daily Inspection Volume</h3>
                {noData(dailyVol) ? <p className="empty-text">No data available.</p> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={dailyVol}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', color: '#e2e8f0' }} />
                      <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Quality Score Trend */}
              <div className="chart-card chart-card--wide">
                <h3 className="chart-title">Quality Score Trend</h3>
                {qualityTrend.length === 0 ? <p className="empty-text">No data available.</p> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={qualityTrend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="inspection_id" tick={false} />
                      <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', color: '#e2e8f0' }} formatter={(v) => [`${v}%`, 'Quality Score']} />
                      <Line type="monotone" dataKey="quality_score" stroke="#22c55e" strokeWidth={2} dot={{ r: 3, fill: '#22c55e' }} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Defect Trend */}
              <div className="chart-card chart-card--wide">
                <h3 className="chart-title">Defect Trend Over Time</h3>
                {defectTrend.length === 0 ? <p className="empty-text">No data available.</p> : (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={defectTrend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', color: '#e2e8f0' }} />
                      <Line type="monotone" dataKey="total_defects" stroke="#ef4444" strokeWidth={2} dot={{ r: 3, fill: '#ef4444' }} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
