import apiClient from './apiClient'

// ── Material-aware analytics (new) ────────────────────────────────────
export const getMaterialAnalytics = (material) =>
  apiClient.get(`/api/${material}/analytics`)

// ── Legacy steel-only endpoints (kept for backward compatibility) ─────
export const getSummary              = () => apiClient.get('/api/analytics/summary')
export const getStatusDistribution   = () => apiClient.get('/api/analytics/status-distribution')
export const getSeverityDistribution = () => apiClient.get('/api/analytics/severity-distribution')
export const getDefectDistribution   = () => apiClient.get('/api/analytics/defect-distribution')
export const getQualityTrend         = () => apiClient.get('/api/analytics/quality-trend')
export const getDefectTrend          = () => apiClient.get('/api/analytics/defect-trend')
export const getDailyVolume          = () => apiClient.get('/api/analytics/daily-volume')
