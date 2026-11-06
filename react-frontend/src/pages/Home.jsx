import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ScanLine, Layers, Cpu, ArrowRight, ArrowDown, Zap, Shield, BarChart3,
  Cog, PanelsTopLeft, CircuitBoard, Flame,
} from 'lucide-react'
import ActionConfirmModal from '../components/ActionConfirmModal'

const MATERIALS = [
  {
    key: 'steel',
    label: 'Steel',
    desc: 'AI-powered steel surface defect inspection.',
    defects: ['Crazing', 'Inclusion', 'Patches', 'Pitted Surface', 'Rolled-in Scale', 'Scratches'],
    color: '#38bdf8',
    icon: Cog,
  },
  {
    key: 'metal',
    label: 'Metal',
    desc: 'AI-powered metal surface inspection.',
    defects: ['Water Spot', 'Oil Spot', 'Silk Spot', 'Welding Line', 'Inclusion', 'Punching Hole'],
    color: '#818cf8',
    icon: Layers,
  },
  {
    key: 'fabric',
    label: 'Fabric',
    desc: 'AI-powered fabric defect inspection.',
    defects: ['Color Bleeding', 'Crease', 'Hole'],
    color: '#f472b6',
    icon: PanelsTopLeft,
  },
  {
    key: 'pcb',
    label: 'PCB',
    desc: 'AI-powered PCB defect inspection.',
    defects: ['Missing Hole', 'Mouse Bite', 'Open Circuit', 'Short', 'Spur', 'Spurious Copper'],
    color: '#34d399',
    icon: CircuitBoard,
  },
  {
    key: 'welding',
    label: 'Welding',
    desc: 'AI-powered welding defect inspection.',
    defects: ['Bad Weld', 'Good Weld'],
    color: '#fb923c',
    icon: Flame,
  },
]

const FEATURES = [
  { icon: Cpu,      title: 'YOLOv8 Detection',    desc: 'Object detection for identifying supported surface defects.' },
  { icon: Shield,   title: 'Material Validation',  desc: 'Automatic material verification before running defect detection.' },
  { icon: Zap,      title: 'Live Camera Mode',     desc: 'Real-time inspection stream with instant defect overlay.' },
  { icon: BarChart3, title: 'Analytics & Reports', desc: 'Detailed inspection analytics and downloadable PDF reports.' },
]

export default function Home() {
  const navigate = useNavigate()
  const [pendingMaterial, setPendingMaterial] = useState(null)

  const goInspect = (key) => setPendingMaterial(key ?? '')
  const confirmInspection = () => {
    const material = pendingMaterial
    setPendingMaterial(null)
    navigate(material ? `/inspection?material=${material}` : '/inspection')
  }
  const pendingMaterialLabel = MATERIALS.find(m => m.key === pendingMaterial)?.label

  return (
    <>
      <div className="page-content page-content--home">
        <section className="home-hero" aria-labelledby="home-hero-title">
          <div className="home-hero__copy">
            <div className="hero__badge">
              <ScanLine size={13} />
              <span>COMPUTER VISION · INDUSTRIAL QUALITY</span>
            </div>
            <h1 className="home-hero__title" id="home-hero-title">
              A clearer view of <span className="grad-text">product quality.</span>
            </h1>
            <p className="home-hero__description">
              AI-powered visual inspection for manufacturing. Review supported materials, detect surface defects, and explore inspection results in one workspace.
            </p>
            <div className="home-hero__actions">
              <a className="btn btn--primary btn--lg" href="#materials">
                Explore materials <ArrowDown size={15} />
              </a>
              <a className="btn btn--ghost btn--lg" href="#capabilities">
                System capabilities <ArrowRight size={15} />
              </a>
            </div>
            <div className="home-hero__facts" aria-label="Inspection system features">
              <span><Layers size={15} /> {MATERIALS.length} supported materials</span>
              <span><ScanLine size={15} /> Upload and live camera modes</span>
            </div>
          </div>

          <div className="home-hero__media" aria-label="Industrial video background">
            <video
              className="home-hero__video"
              autoPlay
              loop
              muted
              playsInline
              preload="metadata"
              aria-hidden="true"
            >
              <source src="/app-bg-video.webm" type="video/webm" />
              <source src="/app-bg-video.mp4" type="video/mp4" />
            </video>
            <div className="home-hero__media-shade" />
            <div className="home-hero__frame" aria-hidden="true">
              <span className="home-hero__frame-corner home-hero__frame-corner--tl" />
              <span className="home-hero__frame-corner home-hero__frame-corner--tr" />
              <span className="home-hero__frame-corner home-hero__frame-corner--bl" />
              <span className="home-hero__frame-corner home-hero__frame-corner--br" />
              <span className="home-hero__frame-line" />
            </div>
            <div className="home-hero__media-caption">
              <span>INDUSTRIAL VISUAL INSPECTION</span>
              <span>AI QUALITY SYSTEM</span>
            </div>
          </div>
        </section>

        <section className="home-section home-section--capabilities" id="capabilities">
          <div className="home-section__heading">
            <div>
              <div className="section-label"><Layers size={13} /> WORKSPACE CAPABILITIES</div>
              <h2 className="section-title">Tools for inspection workflows</h2>
              <p className="section-sub">Move from material validation to results and reporting in one place.</p>
            </div>
          </div>
          <div className="features-grid">
            {FEATURES.map(f => (
              <article key={f.title} className="feature-card">
                <div className="feature-card__icon">
                  <f.icon size={18} />
                </div>
                <h3 className="feature-card__title">{f.title}</h3>
                <p className="feature-card__desc">{f.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="home-section home-section--materials" id="materials">
          <div className="section-label"><Cpu size={13} /> MATERIAL WORKSPACES</div>
          <h2 className="section-title">Choose a material to inspect</h2>
          <p className="section-sub">Explore the available material workflows and their supported defect classes.</p>
          <div className="products-grid">
            {MATERIALS.map(m => {
              const MaterialIcon = m.icon
              return (
                <article key={m.key} className="product-card" style={{ '--pc': m.color }}>
                  <div className="product-card__top">
                    <span className="product-card__icon">
                      <MaterialIcon size={21} />
                    </span>
                    <h3 className="product-card__name">{m.label}</h3>
                    <p className="product-card__desc">{m.desc}</p>
                  </div>
                  <div className="product-card__defects">
                    <span className="product-card__defects-label">Supported defect classes</span>
                    <div className="product-card__tags">
                      {m.defects.map(d => (
                        <span key={d} className="product-tag" style={{ borderColor: `${m.color}40`, color: m.color, background: `${m.color}10` }}>{d}</span>
                      ))}
                    </div>
                  </div>
                  <div className="product-card__actions">
                    <button className="btn btn--ghost btn--sm" onClick={() => navigate('/dashboard')}>
                      <BarChart3 size={13} /> Dashboard
                    </button>
                    <button className="btn btn--primary btn--sm" onClick={() => goInspect(m.key)} style={{ background: m.color, borderColor: m.color, color: '#050d14' }}>
                      Inspect <ArrowRight size={13} />
                    </button>
                  </div>
                </article>
              )
            })}
          </div>
        </section>
      </div>
      {pendingMaterial !== null && (
        <ActionConfirmModal
          title="Ready to start an inspection?"
          description={pendingMaterialLabel
            ? `Continue to the ${pendingMaterialLabel} inspection workspace.`
            : 'Continue to the inspection workspace to choose a material and inspection method.'}
          confirmLabel="Continue"
          onConfirm={confirmInspection}
          onClose={() => setPendingMaterial(null)}
        />
      )}
    </>
  )
}
