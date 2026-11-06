import { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/auth'
import { ScanLine, Mail } from 'lucide-react'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await forgotPassword(email.trim())
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Request failed.')
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
            </div>
          </div>

          <h2 className="auth-card__title">Forgot Password</h2>
          <p className="auth-card__hint">Enter your registered email to receive a reset token.</p>

          {result ? (
            <div style={{ marginTop: 24 }}>
              <div className="auth-success" style={{ textAlign: 'left', lineHeight: 1.7 }}>
                {result.smtp_configured === false ? (
                  <>
                    <strong>Development mode — SMTP not configured.</strong><br />
                    {result.dev_token ? (
                      <>
                        Your reset token:<br />
                        <code style={{ display: 'block', marginTop: 8, padding: '8px 10px', background: 'rgba(0,0,0,.4)', borderRadius: 6, fontSize: 11, wordBreak: 'break-all', fontFamily: 'monospace' }}>
                          {result.dev_token}
                        </code>
                        <br />
                        Copy this token and use it on the{' '}
                        <Link to="/reset-password" className="auth-link">Reset Password</Link> page.
                      </>
                    ) : (
                      <span style={{ color: 'var(--t-muted)' }}>If that email is registered, a reset token would be sent.</span>
                    )}
                  </>
                ) : result.message}
              </div>
              <p style={{ marginTop: 16, textAlign: 'center', fontSize: 12, color: 'var(--t-muted)' }}>
                Have a token? <Link to="/reset-password" className="auth-link">Reset your password</Link>
              </p>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="auth-field">
                <label className="auth-label">Email Address</label>
                <div className="auth-input-wrap">
                  <input className="auth-input" type="email" placeholder="Enter your registered email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus style={{ paddingRight: 40 }} />
                  <span className="auth-eye" style={{ pointerEvents: 'none' }}><Mail size={14} /></span>
                </div>
              </div>
              {error && <div className="auth-error">{error}</div>}
              <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
                {loading ? <><div className="spin" /> Sending…</> : 'Send Reset Token'}
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
