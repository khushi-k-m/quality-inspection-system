import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { resetPassword } from '../api/auth'
import { Shield, Eye, EyeOff } from 'lucide-react'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [form, setForm]       = useState({ token: '', new_password: '', confirm_password: '' })
  const [showPw, setShowPw]   = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [success, setSuccess] = useState(false)

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.new_password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    if (form.new_password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      await resetPassword(form.token.trim(), form.new_password, form.confirm_password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Reset failed. The token may be invalid or expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-left__content">
          <div className="login-brand">
            <Shield size={52} className="login-brand__icon" />
            <h1 className="login-brand__name">InspectAI</h1>
            <p className="login-brand__tagline">AI-Powered Industrial Quality Inspection System</p>
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-card">
          <div className="login-card__header">
            <h2>Reset Password</h2>
            <p>Enter your reset token and choose a new password.</p>
          </div>

          {success ? (
            <div style={{ marginTop: 30, padding: '16px', border: '1px solid rgba(109,224,164,.3)', borderRadius: 7, color: 'var(--green)', background: 'rgba(109,224,164,.08)', fontSize: 13 }}>
              Password reset successful! Redirecting to login…
            </div>
          ) : (
            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Reset Token</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Paste your reset token here"
                  value={form.token}
                  onChange={set('token')}
                  required
                  autoFocus
                  style={{ fontFamily: 'var(--mono)', fontSize: 12 }}
                />
              </div>

              <div className="form-group">
                <label className="form-label">New Password</label>
                <div className="form-input-wrap">
                  <input
                    className="form-input"
                    type={showPw ? 'text' : 'password'}
                    placeholder="At least 8 characters"
                    value={form.new_password}
                    onChange={set('new_password')}
                    required
                  />
                  <button type="button" className="form-input-icon" onClick={() => setShowPw(!showPw)}>
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm New Password</label>
                <input
                  className="form-input"
                  type={showPw ? 'text' : 'password'}
                  placeholder="Repeat new password"
                  value={form.confirm_password}
                  onChange={set('confirm_password')}
                  required
                />
              </div>

              {error && <div className="login-error">{error}</div>}

              <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
                {loading ? <><div className="spinner spinner--sm" /> Resetting…</> : 'Reset Password'}
              </button>
            </form>
          )}

          <p className="login-card__footer">
            <Link to="/login" style={{ color: 'var(--cyan)' }}>← Back to Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
