import { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/auth'
import { Shield, Mail } from 'lucide-react'

export default function ForgotPassword() {
  const [email, setEmail]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [result, setResult]   = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await forgotPassword(email.trim())
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Request failed. Please try again.')
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
            <h2>Forgot Password</h2>
            <p>Enter your registered email to receive a reset token.</p>
          </div>

          {result ? (
            <div style={{ marginTop: 24 }}>
              <div style={{ padding: '14px', border: '1px solid rgba(69,214,209,.3)', borderRadius: 7, color: 'var(--cyan)', background: 'rgba(69,214,209,.07)', fontSize: 13, lineHeight: 1.6 }}>
                {result.smtp_configured === false ? (
                  <>
                    <strong>Development mode — SMTP not configured.</strong>
                    <br />
                    {result.dev_token ? (
                      <>
                        Your reset token: <br />
                        <code style={{ display: 'block', marginTop: 8, padding: '8px 10px', background: 'rgba(0,0,0,.3)', borderRadius: 5, fontFamily: 'var(--mono)', fontSize: 12, wordBreak: 'break-all' }}>
                          {result.dev_token}
                        </code>
                        <br />
                        Copy this token and use it on the{' '}
                        <Link to="/reset-password" style={{ color: 'var(--cyan)', textDecoration: 'underline' }}>Reset Password</Link> page.
                        <br />
                        <span style={{ color: 'var(--muted)', fontSize: 11 }}>
                          In production, configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM environment variables.
                        </span>
                      </>
                    ) : (
                      <span style={{ color: 'var(--muted)' }}>
                        If that email is registered, a reset token would be sent. (No token returned — email not found or already processed.)
                      </span>
                    )}
                  </>
                ) : (
                  result.message
                )}
              </div>
              <p style={{ marginTop: 18, textAlign: 'center', fontSize: 12, color: 'var(--muted)' }}>
                Have a token?{' '}
                <Link to="/reset-password" style={{ color: 'var(--cyan)' }}>Reset your password</Link>
              </p>
            </div>
          ) : (
            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <div className="form-input-wrap">
                  <input
                    className="form-input"
                    type="email"
                    placeholder="Enter your registered email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    autoFocus
                    style={{ paddingRight: 40 }}
                  />
                  <span className="form-input-icon" style={{ pointerEvents: 'none' }}>
                    <Mail size={15} />
                  </span>
                </div>
              </div>

              {error && <div className="login-error">{error}</div>}

              <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
                {loading ? <><div className="spinner spinner--sm" /> Sending…</> : 'Send Reset Token'}
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
