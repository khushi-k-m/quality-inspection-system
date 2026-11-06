import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register as apiRegister } from '../api/auth'
import { Eye, EyeOff, ScanLine } from 'lucide-react'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm_password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const set = f => e => setForm({ ...form, [f]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm_password) { setError('Passwords do not match.'); return }
    setLoading(true)
    try {
      await apiRegister(form.username, form.email, form.password, form.confirm_password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally { setLoading(false) }
  }

  return (
    <div className="auth-page">
      <video className="auth-video" autoPlay loop muted playsInline src="/bg-video.mp4" />
      <div className="auth-overlay" />
      <div className="auth-glow auth-glow--blue" />
      <div className="auth-glow auth-glow--purple" />

      <div className="auth-card-wrap">
        <div className="auth-card">
          <div className="auth-card__brand">
            <div className="auth-card__logo"><ScanLine size={22} /></div>
            <div>
              <p className="auth-card__sys">AI POWERED DEFECT DETECTION SYSTEM</p>
              <p className="auth-card__sub">Intelligent • Automated • AI-Based Inspection</p>
            </div>
          </div>

          <h2 className="auth-card__title">Create Account</h2>
          <p className="auth-card__hint">Register to access the inspection platform</p>

          {success ? (
            <div className="auth-success">Registration successful! Redirecting to login…</div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="auth-field">
                <label className="auth-label">Username</label>
                <input className="auth-input" type="text" placeholder="Choose a username" value={form.username} onChange={set('username')} required autoFocus />
              </div>
              <div className="auth-field">
                <label className="auth-label">Email</label>
                <input className="auth-input" type="email" placeholder="Enter your email" value={form.email} onChange={set('email')} required />
              </div>
              <div className="auth-field">
                <label className="auth-label">Password</label>
                <div className="auth-input-wrap">
                  <input className="auth-input" type={showPw ? 'text' : 'password'} placeholder="Create a password" value={form.password} onChange={set('password')} required />
                  <button type="button" className="auth-eye" onClick={() => setShowPw(p => !p)}>
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
              <div className="auth-field">
                <label className="auth-label">Confirm Password</label>
                <input className="auth-input" type={showPw ? 'text' : 'password'} placeholder="Repeat your password" value={form.confirm_password} onChange={set('confirm_password')} required />
              </div>
              {error && <div className="auth-error">{error}</div>}
              <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
                {loading ? <><div className="spin" /> Creating account…</> : 'Create Account'}
              </button>
            </form>
          )}

          <p className="auth-footer">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
