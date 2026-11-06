export default function AnimatedBackground() {
  return (
    <div className="amb" aria-hidden="true">
      <video
        className="amb__video"
        autoPlay
        loop
        muted
        playsInline
      >
        <source src="/app-bg-video.webm" type="video/webm" />
        <source src="/app-bg-video.mp4" type="video/mp4" />
      </video>
      <div className="amb__overlay" />
      <div className="amb__grid" />
      <div className="amb__blob amb__blob--1" />
      <div className="amb__blob amb__blob--2" />
      <div className="amb__blob amb__blob--3" />
      <div className="amb__blob amb__blob--4" />
    </div>
  )
}
