import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { resetPassword } from '../api/auth'
import { ScanLine, Eye, EyeOff } from 'lucide-react'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ token: '', new_password: '', confirm_password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const set = f => e => setForm({ ...form, [f]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.new_password !== form.confirm_password) { setError('Passwords do not match.'); return }
    if (form.new_password.length < 8) { setError('Password must be at least 8 characters.'); return }
    setLoading(true)
    try {
      await resetPassword(form.token.trim(), form.new_password, form.confirm_password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Reset failed. Token may be invalid or expired.')
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
            <div><p className="auth-card__sys">AI POWERED DEFECT DETECTION SYSTEM</p></div>
          </div>

          <h2 className="auth-card__title">Reset Password</h2>
          <p className="auth-card__hint">Enter your reset token and choose a new password.</p>

          {success ? (
            <div className="auth-success">Password reset successful! Redirecting to login…</div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="auth-field">
                <label className="auth-label">Reset Token</label>
                <input className="auth-input" type="text" placeholder="Paste your reset token" value={form.token} onChange={set('token')} required autoFocus style={{ fontFamily: 'monospace', fontSize: 12 }} />
              </div>
              <div className="auth-field">
                <label className="auth-label">New Password</label>
                <div className="auth-input-wrap">
                  <input className="auth-input" type={showPw ? 'text' : 'password'} placeholder="At least 8 characters" value={form.new_password} onChange={set('new_password')} required />
                  <button type="button" className="auth-eye" onClick={() => setShowPw(p => !p)}>
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
              <div className="auth-field">
                <label className="auth-label">Confirm New Password</label>
                <input className="auth-input" type={showPw ? 'text' : 'password'} placeholder="Repeat new password" value={form.confirm_password} onChange={set('confirm_password')} required />
              </div>
              {error && <div className="auth-error">{error}</div>}
              <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
                {loading ? <><div className="spin" /> Resetting…</> : 'Reset Password'}
              </button>
            </form>
          )}

          <p className="auth-footer">
            <Link to="/login" className="auth-link">← Back to Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
