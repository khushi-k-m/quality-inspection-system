import { Shield, Cpu, Layers, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="app-footer__grid">
        {/* Column 1: About */}
        <div className="footer-col">
          <div className="footer-col__header">
            <div className="footer-col__icon-wrap">
              <Shield size={16} />
            </div>
            <h4 className="footer-col__title">About</h4>
          </div>
          <p className="footer-col__text">
            The AI Quality Inspection System is an automated vision platform engineered for defect identification, quality verification, and inspection workflows across manufacturing lines.
          </p>
        </div>

        {/* Column 2: Project Information */}
        <div className="footer-col">
          <div className="footer-col__header">
            <div className="footer-col__icon-wrap">
              <Layers size={16} />
            </div>
            <h4 className="footer-col__title">Project Information</h4>
          </div>
          <ul className="footer-list">
            <li>
              <span className="footer-list__key">Application:</span>
              <span className="footer-list__val">Quality Inspection System</span>
            </li>
            <li>
              <span className="footer-list__key">Supported Materials:</span>
              <span className="footer-list__val">Steel, Metal, Fabric, PCB, Welding</span>
            </li>
            <li>
              <span className="footer-list__key">Inspection Modes:</span>
              <span className="footer-list__val">Batch Image Upload & Live Camera</span>
            </li>
            <li>
              <span className="footer-list__key">Reporting:</span>
              <span className="footer-list__val">PDF Export & Inspection History</span>
            </li>
          </ul>
        </div>

        {/* Column 3: Technology */}
        <div className="footer-col">
          <div className="footer-col__header">
            <div className="footer-col__icon-wrap">
              <Cpu size={16} />
            </div>
            <h4 className="footer-col__title">Technology</h4>
          </div>
          <ul className="footer-list">
            <li>
              <span className="footer-list__key">Vision Engine:</span>
              <span className="footer-list__val">Ultralytics YOLOv8 & PyTorch</span>
            </li>
            <li>
              <span className="footer-list__key">Image Processing:</span>
              <span className="footer-list__val">OpenCV Analysis</span>
            </li>
            <li>
              <span className="footer-list__key">Backend API:</span>
              <span className="footer-list__val">Python FastAPI</span>
            </li>
            <li>
              <span className="footer-list__key">Frontend Client:</span>
              <span className="footer-list__val">React 19, Vite & Recharts</span>
            </li>
          </ul>
        </div>

        {/* Column 4: Contact */}
        <div className="footer-col">
          <div className="footer-col__header">
            <div className="footer-col__icon-wrap">
              <Mail size={16} />
            </div>
            <h4 className="footer-col__title">Contact</h4>
          </div>
          <div className="footer-contact-item">
            <span className="footer-contact-label">Email</span>
            <a
              className="footer-contact-link"
              href="https://mail.google.com/mail/?view=cm&fs=1&to=khushikm997%40gmail.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Email khushikm997@gmail.com"
            >
              khushikm997@gmail.com
            </a>
          </div>
          <p className="footer-col__text">
            Opens a new Gmail message addressed to this email.
          </p>
        </div>
      </div>

      <div className="app-footer__bottom">
        <div className="footer-copy">
          © {new Date().getFullYear()} AI Quality Inspection System
        </div>
      </div>
    </footer>
  )
}
