import { useEffect, useState } from 'react'
import Header from '../components/Header'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import StatCard from '../components/StatCard'
import { getMaterialAnalytics } from '../api/analytics'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  LineChart, Line, CartesianGrid, ResponsiveContainer, Legend
} from 'recharts'
import { ClipboardCheck, CheckCircle, XCircle, AlertTriangle, Star } from 'lucide-react'

const MATERIALS = [
  { key: 'steel', label: 'Steel' },
  { key: 'metal', label: 'Metal' },
]

const STATUS_COLORS   = { PASS: '#22c55e', REWORK: '#f97316', FAIL: '#ef4444' }
const SEVERITY_COLORS = { NONE: '#64748b', LOW: '#22c55e', MEDIUM: '#f97316', HIGH: '#ef4444', CRITICAL: '#dc2626' }
const DEFECT_COLORS   = ['#6366f1', '#f97316', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

const CHART_TOOLTIP = { background: '#0f172a', border: '1px solid #1e293b', color: '#e2e8f0' }
const AXIS_TICK     = { fill: '#94a3b8', fontSize: 12 }

function noData(arr) {
  return !arr || arr.length === 0 || arr.every(i =>
    (i.count ?? i.total_defects ?? i.quality_score ?? 0) === 0
  )
}

export default function Analytics() {
  const [material, setMaterial] = useState('steel')
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getMaterialAnalytics(material)
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [material])

  return (
    <div className="page">
      <Header title="Analytics" />
      <div className="page__body">

        {/* Material selector */}
        <div className="inspection-mode-bar" style={{ marginBottom: 24 }}>
          {MATERIALS.map(m => (
            <button
              key={m.key}
              className={`inspection-mode-btn ${material === m.key ? 'inspection-mode-btn--active' : ''}`}
              onClick={() => setMaterial(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>

        {loading && <Loading text={`Loading ${material} analytics...`} />}
        {error   && <ErrorMessage message={error} onRetry={load} />}

        {!loading && !error && data && (
          <>
            <div className="stat-grid">
              <StatCard label="Total Inspections" value={data.total_inspections}       icon={ClipboardCheck} color="#6366f1" />
              <StatCard label="PASS"              value={data.pass_count}              icon={CheckCircle}    color="#22c55e" sub={`${data.quality_rate}%`} />
              <StatCard label="REWORK"            value={data.rework_count}            icon={AlertTriangle}  color="#f97316" sub={`${data.rework_rate}%`} />
              <StatCard label="FAIL"              value={data.fail_count}              icon={XCircle}        color="#ef4444" sub={`${data.failure_rate}%`} />
              <StatCard label="Avg Quality Score" value={`${data.avg_quality_score}%`} icon={Star}           color="#eab308" />
            </div>

            <div className="charts-grid">

              {/* Status Distribution */}
              <div className="chart-card">
                <h3 className="chart-title">Status Distribution</h3>
                {noData(data.status_distribution) ? (
                  <p className="empty-text">No inspection data available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={data.status_distribution}
                        dataKey="count" nameKey="status"
                        cx="50%" cy="50%" outerRadius={90}
                        label={({ status, percent }) => `${status} ${(percent * 100).toFixed(0)}%`}
                      >
                        {data.status_distribution.map((e, i) => (
                          <Cell key={i} fill={STATUS_COLORS[e.status] || '#6366f1'} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={CHART_TOOLTIP} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Severity Distribution */}
              <div className="chart-card">
                <h3 className="chart-title">Severity Distribution</h3>
                {noData(data.severity_distribution) ? (
                  <p className="empty-text">No inspection data available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={data.severity_distribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="severity" tick={AXIS_TICK} />
                      <YAxis tick={AXIS_TICK} />
                      <Tooltip contentStyle={CHART_TOOLTIP} />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {data.severity_distribution.map((e, i) => (
                          <Cell key={i} fill={SEVERITY_COLORS[e.severity] || '#6366f1'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Defect Distribution */}
              <div className="chart-card">
                <h3 className="chart-title">Defect Distribution</h3>
                {noData(data.defect_distribution) ? (
                  <p className="empty-text">No defect data available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={data.defect_distribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="type" tick={{ ...AXIS_TICK, fontSize: 11 }} />
                      <YAxis tick={AXIS_TICK} />
                      <Tooltip contentStyle={CHART_TOOLTIP} />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {data.defect_distribution.map((e, i) => (
                          <Cell key={i} fill={DEFECT_COLORS[i % DEFECT_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Daily Volume */}
              <div className="chart-card">
                <h3 className="chart-title">Daily Inspection Volume</h3>
                {noData(data.daily_volume) ? (
                  <p className="empty-text">No data available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={data.daily_volume}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" tick={{ ...AXIS_TICK, fontSize: 11 }} />
                      <YAxis tick={AXIS_TICK} />
                      <Tooltip contentStyle={CHART_TOOLTIP} />
                      <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Quality Score Trend */}
              <div className="chart-card chart-card--wide">
                <h3 className="chart-title">Quality Score Trend</h3>
                {data.quality_trend.length === 0 ? (
                  <p className="empty-text">No data available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={data.quality_trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="inspection_id" tick={false} />
                      <YAxis domain={[0, 100]} tick={AXIS_TICK} />
                      <Tooltip
                        contentStyle={CHART_TOOLTIP}
                        formatter={(v) => [`${v}%`, 'Quality Score']}
                        labelFormatter={(_, payload) => payload?.[0]?.payload?.inspection_id || ''}
                      />
                      <Line type="monotone" dataKey="quality_score" stroke="#22c55e"
                            strokeWidth={2} dot={{ r: 3, fill: '#22c55e' }} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Defect Trend */}
              <div className="chart-card chart-card--wide">
                <h3 className="chart-title">Defect Trend Over Time</h3>
                {data.defect_trend.length === 0 ? (
                  <p className="empty-text">No data available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={data.defect_trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" tick={{ ...AXIS_TICK, fontSize: 11 }} />
                      <YAxis tick={AXIS_TICK} />
                      <Tooltip contentStyle={CHART_TOOLTIP} />
                      <Line type="monotone" dataKey="total_defects" stroke="#ef4444"
                            strokeWidth={2} dot={{ r: 3, fill: '#ef4444' }} />
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
