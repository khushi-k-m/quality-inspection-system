import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, logout as apiLogout } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('sv_token')
    const stored = localStorage.getItem('sv_user')
    if (token && stored) {
      try {
        setUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('sv_token')
        localStorage.removeItem('sv_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const res = await apiLogin(username, password)
    const { access_token, username: uname, role } = res.data
    const userData = { username: uname, role }
    localStorage.setItem('sv_token', access_token)
    localStorage.setItem('sv_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const logout = async () => {
    try { await apiLogout() } catch {}
    localStorage.removeItem('sv_token')
    localStorage.removeItem('sv_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
