import apiClient from './apiClient'

const BASE = import.meta.env.VITE_API_BASE_URL || ''

export const getCameraStatus = () => apiClient.get('/api/camera/status')
export const startCamera = (material = 'auto') =>
  apiClient.post('/api/camera/start', { material })
export const setCameraMode = (material = 'auto') =>
  apiClient.post('/api/camera/mode', { material })
export const stopCamera = () => apiClient.post('/api/camera/stop')
export const captureInspection = (inspector = 'AI Camera System') =>
  apiClient.post('/api/camera/capture', { inspector })

export const getStreamUrl = () => `${BASE}/api/camera/stream`
export const getImageUrl = (inspectionId, token) =>
  `${BASE}/api/images/${inspectionId}?token=${token}`
export const getThermalImageUrl = (inspectionId) =>
  `${BASE}/api/images/thermal/${inspectionId}`
