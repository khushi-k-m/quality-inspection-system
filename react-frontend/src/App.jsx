import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AnimatedBackground from './components/AnimatedBackground'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Inspection from './pages/Inspection'
import InspectionHistory from './pages/InspectionHistory'
import InspectionDetails from './pages/InspectionDetails'
import Reports from './pages/Reports'
import Analysis from './pages/Analysis'
import Help from './pages/Help'
import Settings from './pages/Settings'
import Profile from './pages/Profile'

import Footer from './components/Footer'

function AppLayout() {
  const location = useLocation()

  return (
    <div className="app-shell">
      <AnimatedBackground showVideo={location.pathname !== '/home'} />
      <Sidebar />
      <div className="app-body">
        <Header />
        <main className="app-main">
          <Outlet />
          <Footer />
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login"          element={<Login />} />
          <Route path="/register"       element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/home"                          element={<Home />} />
            <Route path="/dashboard"                     element={<Dashboard />} />
            <Route path="/inspection"                    element={<Inspection />} />
            <Route path="/inspection-history"            element={<InspectionHistory />} />
            <Route path="/inspection-history/:id"        element={<InspectionDetails />} />
            <Route path="/reports"                       element={<Reports />} />
            <Route path="/analysis"                      element={<Analysis />} />
            <Route path="/analytics"                     element={<Navigate to="/analysis" replace />} />
            <Route path="/live-inspection"               element={<Navigate to="/inspection" replace />} />
            <Route path="/help"                          element={<Help />} />
            <Route path="/settings"                      element={<Settings />} />
            <Route path="/profile"                       element={<Profile />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
