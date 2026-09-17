import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
})

// Attach token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('sv_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally — but NOT on auth endpoints (login returns 401 for bad credentials)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || ''
    const isAuthEndpoint = url.includes('/api/auth/')
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('sv_token')
      localStorage.removeItem('sv_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
