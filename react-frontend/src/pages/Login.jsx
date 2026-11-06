import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Eye, EyeOff, ScanLine } from 'lucide-react'

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
      navigate('/home')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      {/* Video background */}
      <video
        className="auth-video"
        autoPlay
        loop
        muted
        playsInline
        src="/bg-video.mp4"
      />
      <div className="auth-overlay" />
      <div className="auth-glow auth-glow--blue" />
      <div className="auth-glow auth-glow--purple" />

      {/* Card */}
      <div className="auth-card-wrap">
        <div className="auth-card">
          <div className="auth-card__brand">
            <div className="auth-card__logo">
              <ScanLine size={22} />
            </div>
            <div>
              <p className="auth-card__sys">AI POWERED DEFECT DETECTION SYSTEM</p>
              <p className="auth-card__sub">Intelligent • Automated • AI-Based Inspection</p>
            </div>
          </div>

          <h2 className="auth-card__title">Welcome back</h2>
          <p className="auth-card__hint">Sign in to your inspection dashboard</p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-field">
              <label className="auth-label">Username or Email</label>
              <input
                className="auth-input"
                type="text"
                placeholder="Enter username or email"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
                autoFocus
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">Password</label>
              <div className="auth-input-wrap">
                <input
                  className="auth-input"
                  type={showPw ? 'text' : 'password'}
                  placeholder="Enter password"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button type="button" className="auth-eye" onClick={() => setShowPw(p => !p)}>
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {error && <div className="auth-error">{error}</div>}

            <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
              {loading ? <><div className="spin" /> Signing in…</> : 'Sign In'}
            </button>

            <p className="auth-link-row">
              <Link to="/forgot-password" className="auth-link">Forgot Password?</Link>
            </p>
          </form>

          <p className="auth-footer">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="auth-link">Create Account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
