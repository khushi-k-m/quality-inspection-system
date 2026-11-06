import { useState } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Home,
  LayoutDashboard,
  ScanLine,
  BarChart3,
  History,
  FileText,
  HelpCircle,
  Settings,
  LogOut,
  Cpu,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Radio
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/home',               icon: Home,            label: 'Home',        badge: null },
  { to: '/dashboard',          icon: LayoutDashboard, label: 'Dashboard',   badge: null },
  { to: '/inspection',         icon: ScanLine,        label: 'Inspection',  badge: 'Live' },
  { to: '/analysis',           icon: BarChart3,       label: 'Analysis',    badge: null },
  { to: '/inspection-history', icon: History,         label: 'History',     badge: null },
  { to: '/reports',            icon: FileText,        label: 'Reports',     badge: null },
  { to: '/help',               icon: HelpCircle,      label: 'Help',        badge: null },
  { to: '/settings',           icon: Settings,        label: 'Settings',    badge: null },
]

export default function Sidebar() {
  const { logout, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const initial = user?.username?.[0]?.toUpperCase() || 'O'

  const isNavActive = (to) => {
    if (to === '/home') return location.pathname === '/home' || location.pathname === '/'
    return location.pathname === to || location.pathname.startsWith(`${to}/`)
  }

  return (
    <>
      {/* Mobile trigger */}
      <button
        className="sb-hamburger"
        onClick={() => setMobileOpen(true)}
        aria-label="Open Navigation Menu"
      >
        <Menu size={20} />
      </button>

      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="sb-overlay"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`sidebar ${collapsed ? 'sidebar--col' : ''} ${mobileOpen ? 'sidebar--mob' : ''}`}
        aria-label="Main Navigation"
      >
        {/* Brand header */}
        <div className="sidebar__brand">
          <div className="sidebar__logo-wrap" title="AI Quality Inspection System">
            <Cpu size={19} className="sidebar__logo-icon" />
            <span className="sidebar__logo-pulse" />
          </div>

          {!collapsed && (
            <div className="sidebar__brand-text">
              <span className="sidebar__b1">AI QUALITY</span>
              <span className="sidebar__b2">INSPECTION OS</span>
            </div>
          )}

          <button
            className="sidebar__toggle"
            onClick={() => {
              if (mobileOpen) {
                setMobileOpen(false)
              } else {
                setCollapsed(c => !c)
              }
            }}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {mobileOpen ? (
              <X size={15} />
            ) : collapsed ? (
              <ChevronRight size={15} />
            ) : (
              <ChevronLeft size={15} />
            )}
          </button>
        </div>

        {/* Live system banner */}
        {!collapsed && (
          <div className="sidebar__status-bar">
            <div className="sidebar__status-indicator">
              <span className="sidebar__status-dot" />
              <span className="sidebar__status-text">SYSTEM OPERATIONAL</span>
            </div>
            <Radio size={12} className="sidebar__status-signal" />
          </div>
        )}

        {/* Navigation links */}
        <nav className="sidebar__nav">
          <div className="sidebar__nav-section-label">
            {!collapsed ? 'NAVIGATION' : '•'}
          </div>

          {NAV_ITEMS.map(({ to, icon: Icon, label, badge }) => {
            const active = isNavActive(to)
            return (
              <NavLink
                key={to}
                to={to}
                className={`sidebar__link ${active ? 'sidebar__link--active' : ''}`}
                onClick={() => setMobileOpen(false)}
                title={collapsed ? label : undefined}
              >
                <div className="sidebar__link-icon-wrap">
                  <Icon size={18} />
                </div>

                {!collapsed && (
                  <span className="sidebar__link-label">{label}</span>
                )}

                {!collapsed && badge && (
                  <span className="sidebar__link-badge">{badge}</span>
                )}

                {active && <span className="sidebar__link-active-bar" />}
              </NavLink>
            )
          })}
        </nav>

        {/* User profile & logout footer */}
        <div className="sidebar__footer">
          <div className="sidebar__user" title={user?.username || 'Operator'}>
            <div className="sidebar__avatar">
              <span>{initial}</span>
              <span className="sidebar__avatar-dot" />
            </div>

            {!collapsed && (
              <div className="sidebar__uinfo">
                <span className="sidebar__uname">{user?.username || 'Operator'}</span>
                <span className="sidebar__urole">{user?.role || 'Quality Inspector'}</span>
              </div>
            )}
          </div>

          <button
            className="sidebar__logout"
            onClick={handleLogout}
            title={collapsed ? 'Sign Out' : undefined}
          >
            <LogOut size={16} />
            {!collapsed && <span>Sign Out</span>}
          </button>
        </div>
      </aside>
    </>
  )
}
