import { useState } from 'react'
import { ChevronDown, BookOpen, HelpCircle, AlertTriangle, CheckCircle, ScanLine, BarChart3 } from 'lucide-react'

const STEPS = [
  { n: '01', title: 'Login',              desc: 'Sign in with your username and password.' },
  { n: '02', title: 'Go to Inspection',   desc: 'Click "Inspection" in the sidebar.' },
  { n: '03', title: 'Select Product',     desc: 'Choose Steel, Metal, Fabric, PCB, or Welding from the dropdown.' },
  { n: '04', title: 'Upload or Capture',  desc: 'Upload an image file or use the live camera mode.' },
  { n: '05', title: 'Start Inspection',   desc: 'Click "Detect Defects" to run the AI model.' },
  { n: '06', title: 'View AI Result',     desc: 'See the annotated image, status, defects, and quality score.' },
  { n: '07', title: 'Analysis & Reports', desc: 'Use the Analysis page to explore historical data and download PDF reports.' },
]

const FAQS = [
  {
    q: 'What image formats are supported?',
    a: 'The system accepts JPG, JPEG, and PNG images up to 20 MB.',
  },
  {
    q: 'How does material validation work?',
    a: 'Before running defect detection, the system uses a classification model to verify the uploaded image matches the selected material. If the image is blank (INVALID_IMAGE), the wrong material (INVALID_MATERIAL), or uncertain (MATERIAL_UNVERIFIED), the inspection is stopped and you are shown the reason.',
  },
  {
    q: 'How does defect detection work?',
    a: 'Each material has a dedicated YOLOv8 model trained on domain-specific defect data. The model returns bounding boxes, defect classes, and confidence scores. The system then calculates a quality score and assigns a status of PASS, REWORK, or FAIL.',
  },
  {
    q: 'What do PASS, REWORK, and FAIL mean?',
    a: 'PASS means no significant defects were found. REWORK means minor defects were detected that may require attention. FAIL means critical defects were found and the product should be rejected.',
  },
  {
    q: 'Can I use a live camera for inspection?',
    a: 'Yes. Switch to "Live Camera" mode on the Inspection page. The system streams real-time YOLO detection. Click "Save Inspection" to record the current frame to the database.',
  },
  {
    q: 'How do I download a PDF report?',
    a: 'After a successful inspection, click "Download PDF". You can also download reports from the Inspection History page or the Reports section.',
  },
  {
    q: 'Why is my image showing INVALID_MATERIAL?',
    a: 'The material classifier detected a different material than what you selected. Make sure you are uploading an image of the correct product and that the image is clear and well-lit.',
  },
  {
    q: 'Where is my inspection data stored?',
    a: 'Each material has its own SQLite database on the server. Data is never mixed between materials.',
  },
]

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={`faq-item${open ? ' faq-item--open' : ''}`}>
      <button className="faq-item__q" onClick={() => setOpen(o => !o)}>
        <span>{q}</span>
        <ChevronDown size={16} className="faq-item__chevron" />
      </button>
      {open && <div className="faq-item__a">{a}</div>}
    </div>
  )
}

export default function Help() {
  return (
    <div className="page-content">
      {/* How to use */}
      <div className="help-section">
        <div className="help-section__hdr">
          <BookOpen size={16} />
          <h2 className="help-section__title">How to Use the System</h2>
        </div>
        <div className="steps-grid">
          {STEPS.map(s => (
            <div key={s.n} className="step-card">
              <span className="step-card__n">{s.n}</span>
              <div>
                <h3 className="step-card__title">{s.title}</h3>
                <p className="step-card__desc">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Status guide */}
      <div className="help-section">
        <div className="help-section__hdr">
          <ScanLine size={16} />
          <h2 className="help-section__title">Inspection Status Guide</h2>
        </div>
        <div className="status-guide">
          {[
            { status: 'PASS',               color: '#4ade80', icon: CheckCircle,  desc: 'No significant defects detected. Product meets quality standards.' },
            { status: 'REWORK',             color: '#fb923c', icon: AlertTriangle, desc: 'Minor defects detected. Product may require rework before use.' },
            { status: 'FAIL',               color: '#f87171', icon: AlertTriangle, desc: 'Critical defects detected. Product should be rejected.' },
            { status: 'INVALID_IMAGE',      color: '#fb923c', icon: HelpCircle,   desc: 'No valid product detected in the image. Try a clearer image.' },
            { status: 'INVALID_MATERIAL',   color: '#f87171', icon: HelpCircle,   desc: 'Image does not match the selected material type.' },
            { status: 'MATERIAL_UNVERIFIED',color: '#fb923c', icon: HelpCircle,   desc: 'Material could not be verified with sufficient confidence.' },
          ].map(({ status, color, icon: Icon, desc }) => (
            <div key={status} className="status-guide__item" style={{ borderColor: `${color}25` }}>
              <Icon size={16} style={{ color, flexShrink: 0 }} />
              <div>
                <span className="status-guide__badge" style={{ color, background: `${color}15`, border: `1px solid ${color}30` }}>{status}</span>
                <p className="status-guide__desc">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ */}
      <div className="help-section">
        <div className="help-section__hdr">
          <HelpCircle size={16} />
          <h2 className="help-section__title">Frequently Asked Questions</h2>
        </div>
        <div className="faq-list">
          {FAQS.map(f => <FaqItem key={f.q} q={f.q} a={f.a} />)}
        </div>
      </div>

      {/* Contact */}
      <div className="help-section">
        <div className="help-section__hdr">
          <BarChart3 size={16} />
          <h2 className="help-section__title">Troubleshooting</h2>
        </div>
        <div className="glass-card" style={{ padding: '20px 24px' }}>
          <ul className="trouble-list">
            <li><strong>Backend offline:</strong> Ensure the FastAPI server is running on port 8000.</li>
            <li><strong>Camera not starting:</strong> Check that a USB camera is connected and not in use by another application.</li>
            <li><strong>Model not ready:</strong> Verify that the trained model weights exist in the <code>trained_model/</code> directory.</li>
            <li><strong>Upload fails:</strong> Ensure the image is JPG or PNG and under 20 MB.</li>
            <li><strong>PDF not generating:</strong> The backend requires ReportLab. Run <code>pip install reportlab</code>.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
