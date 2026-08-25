export default function Loading({ text = 'Loading...' }) {
  return (
    <div className="loading">
      <div className="spinner" />
      <span style={{ marginTop: 10, color: 'var(--muted)', fontSize: 13 }}>{text}</span>
    </div>
  )
}
