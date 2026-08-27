import apiClient from './apiClient'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const getCameraStatus = () => apiClient.get('/api/camera/status')
export const startCamera = (material = 'steel') =>
  apiClient.post('/api/camera/start', { material })
export const stopCamera = () => apiClient.post('/api/camera/stop')
export const captureInspection = () => apiClient.post('/api/camera/capture')

export const getStreamUrl = () => `${BASE}/api/camera/stream`
export const getImageUrl = (inspectionId, token) =>
  `${BASE}/api/images/${inspectionId}?token=${token}`
