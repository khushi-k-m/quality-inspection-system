import { useEffect, useState } from 'react'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import StatCard from '../components/StatCard'
import { getMaterialAnalytics } from '../api/analytics'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  LineChart, Line, CartesianGrid, ResponsiveContainer
} from 'recharts'
import { ClipboardCheck, CheckCircle, XCircle, AlertTriangle, Star } from 'lucide-react'

const MATERIALS = [
  { key: 'steel',   label: 'Steel',   color: '#38bdf8' },
  { key: 'metal',   label: 'Metal',   color: '#818cf8' },
  { key: 'fabric',  label: 'Fabric',  color: '#f472b6' },
  { key: 'pcb',     label: 'PCB',     color: '#34d399' },
  { key: 'welding', label: 'Welding', color: '#fb923c' },
]

const STATUS_C   = { PASS: '#4ade80', REWORK: '#fb923c', FAIL: '#f87171' }
const SEVERITY_C = { NONE: '#64748b', LOW: '#4ade80', MEDIUM: '#fb923c', HIGH: '#f87171', CRITICAL: '#ef4444' }
const DEFECT_C   = ['#6366f1','#f97316','#ef4444','#8b5cf6','#06b6d4','#ec4899','#eab308','#14b8a6']
const TT = { contentStyle: { background: '#0d1b26', border: '1px solid rgba(255,255,255,.08)', borderRadius: 8, color: '#e2e8f0', fontSize: 12 } }
const AX = { fill: '#64748b', fontSize: 11 }

function noData(arr) {
  return !arr || arr.length === 0 || arr.every(i => (i.count ?? i.total_defects ?? i.quality_score ?? 0) === 0)
}

function ChartCard({ title, children, wide }) {
  return (
    <div className={`chart-card${wide ? ' chart-card--wide' : ''}`}>
      <h3 className="chart-card__title">{title}</h3>
      {children}
    </div>
  )
}

export default function Analysis() {
  const [material, setMaterial] = useState('steel')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try {
      const res = await getMaterialAnalytics(material)
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics.')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [material])

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

      {loading && <Loading text={`Loading ${mat?.label} analytics…`} />}
      {error && <ErrorMessage message={error} onRetry={load} />}

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
            <ChartCard title="Status Distribution">
              {noData(data.status_distribution) ? <p className="empty-text">No data available.</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={data.status_distribution} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={85} label={({ status, percent }) => `${status} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                      {data.status_distribution.map((e, i) => <Cell key={i} fill={STATUS_C[e.status] || '#6366f1'} />)}
                    </Pie>
                    <Tooltip {...TT} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Severity Distribution">
              {noData(data.severity_distribution) ? <p className="empty-text">No data available.</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.severity_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
                    <XAxis dataKey="severity" tick={AX} />
                    <YAxis tick={AX} />
                    <Tooltip {...TT} />
                    <Bar dataKey="count" radius={[4,4,0,0]}>
                      {data.severity_distribution.map((e, i) => <Cell key={i} fill={SEVERITY_C[e.severity] || '#6366f1'} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Defect Distribution">
              {noData(data.defect_distribution) ? <p className="empty-text">No data available.</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.defect_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
                    <XAxis dataKey="type" tick={{ ...AX, fontSize: 10 }} />
                    <YAxis tick={AX} />
                    <Tooltip {...TT} />
                    <Bar dataKey="count" radius={[4,4,0,0]}>
                      {data.defect_distribution.map((e, i) => <Cell key={i} fill={DEFECT_C[i % DEFECT_C.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Daily Inspection Volume">
              {noData(data.daily_volume) ? <p className="empty-text">No data available.</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.daily_volume}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
                    <XAxis dataKey="date" tick={{ ...AX, fontSize: 10 }} />
                    <YAxis tick={AX} />
                    <Tooltip {...TT} />
                    <Bar dataKey="count" fill={mat?.color || '#6366f1'} radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Quality Score Trend" wide>
              {!data.quality_trend?.length ? <p className="empty-text">No data available.</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={data.quality_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
                    <XAxis dataKey="inspection_id" tick={false} />
                    <YAxis domain={[0,100]} tick={AX} />
                    <Tooltip {...TT} formatter={v => [`${v}%`, 'Quality Score']} labelFormatter={(_, p) => p?.[0]?.payload?.inspection_id || ''} />
                    <Line type="monotone" dataKey="quality_score" stroke="#4ade80" strokeWidth={2} dot={{ r: 2, fill: '#4ade80' }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Defect Trend Over Time" wide>
              {!data.defect_trend?.length ? <p className="empty-text">No data available.</p> : (
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={data.defect_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
                    <XAxis dataKey="date" tick={{ ...AX, fontSize: 10 }} />
                    <YAxis tick={AX} />
                    <Tooltip {...TT} />
                    <Line type="monotone" dataKey="total_defects" stroke="#f87171" strokeWidth={2} dot={{ r: 2, fill: '#f87171' }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>
        </>
      )}
    </div>
  )
}
