import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register as apiRegister } from '../api/auth'
import { Eye, EyeOff, Shield, Cpu, Activity, Zap } from 'lucide-react'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm_password: '' })
  const [showPw, setShowPw] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await apiRegister(form.username, form.email, form.password, form.confirm_password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
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
            <h1 className="login-brand__name">SteelVision AI</h1>
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
              <span>Automated Quality Scoring &amp; Reports</span>
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
            <h2>Create Account</h2>
            <p>Register to access the inspection dashboard</p>
          </div>

          {success ? (
            <div style={{ marginTop: 30, padding: '16px', border: '1px solid rgba(109,224,164,.3)', borderRadius: 7, color: 'var(--green)', background: 'rgba(109,224,164,.08)', fontSize: 13 }}>
              Registration successful! Redirecting to login…
            </div>
          ) : (
            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Username</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Choose a username"
                  value={form.username}
                  onChange={set('username')}
                  required
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  className="form-input"
                  type="email"
                  placeholder="Enter your email"
                  value={form.email}
                  onChange={set('email')}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <div className="form-input-wrap">
                  <input
                    className="form-input"
                    type={showPw ? 'text' : 'password'}
                    placeholder="Create a password"
                    value={form.password}
                    onChange={set('password')}
                    required
                  />
                  <button type="button" className="form-input-icon" onClick={() => setShowPw(!showPw)}>
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm Password</label>
                <div className="form-input-wrap">
                  <input
                    className="form-input"
                    type={showConfirm ? 'text' : 'password'}
                    placeholder="Repeat your password"
                    value={form.confirm_password}
                    onChange={set('confirm_password')}
                    required
                  />
                  <button type="button" className="form-input-icon" onClick={() => setShowConfirm(!showConfirm)}>
                    {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {error && <div className="login-error">{error}</div>}

              <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
                {loading ? <><div className="spinner spinner--sm" /> Creating account…</> : 'Create Account'}
              </button>
            </form>
          )}

          <p className="login-card__footer">
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--cyan)' }}>Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
