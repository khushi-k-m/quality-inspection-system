export default function Loading({ text = 'Loading...' }) {
  return (
    <div className="loading">
      <div className="loading__ring" />
      <span className="loading__text">{text}</span>
    </div>
  )
}
