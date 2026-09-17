import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Eye, EyeOff, Shield, Cpu, Activity, Zap } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check your credentials.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Left panel */}
      <div className="login-left">
        <div className="login-left__content">
          <div className="login-brand">
            <Shield size={52} className="login-brand__icon" />
            <h1 className="login-brand__name">InspectAI </h1>
            <p className="login-brand__tagline">
              AI-Powered Industrial Quality Inspection System
            </p>
          </div>

          <div className="login-features">
            <div className="login-feature">
              <Cpu size={20} />
              <span>YOLOv8 Real-Time Defect Detection</span>
            </div>
            <div className="login-feature">
              <Activity size={20} />
              <span>Live Camera Inspection Stream</span>
            </div>
            <div className="login-feature">
              <Zap size={20} />
              <span>Automated Quality Scoring & Reports</span>
            </div>
          </div>

          <div className="login-stats">
            <div className="login-stat">
              <span className="login-stat__value">10+</span>
              <span className="login-stat__label">Defect Classes</span>
            </div>
            <div className="login-stat">
              <span className="login-stat__value">Real-Time</span>
              <span className="login-stat__label">Detection</span>
            </div>
            <div className="login-stat">
              <span className="login-stat__value">PDF</span>
              <span className="login-stat__label">Auto Reports</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div className="login-right">
        <div className="login-card">
          <div className="login-card__header">
            <h2>Welcome Back</h2>
            <p>Sign in to your inspection dashboard</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username or Email</label>
              <input
                className="form-input"
                type="text"
                placeholder="Enter username or email"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="form-input-wrap">
                <input
                  className="form-input"
                  type={showPw ? 'text' : 'password'}
                  placeholder="Enter password"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  className="form-input-icon"
                  onClick={() => setShowPw(!showPw)}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn btn--primary btn--full"
              disabled={loading}
            >
              {loading ? <><div className="spinner spinner--sm" /> Signing in...</> : 'Sign In'}
            </button>

            <p style={{ margin: 0, textAlign: 'center', fontSize: 12 }}>
              <Link to="/forgot-password" style={{ color: 'var(--muted)' }}>Forgot Password?</Link>
            </p>
          </form>

          <p className="login-card__footer">
            Don&apos;t have an account?{' '}
            <Link to="/register" style={{ color: 'var(--cyan)' }}>Create Account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
