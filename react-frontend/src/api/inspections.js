import apiClient from './apiClient'

// ── Material-aware (new) ──────────────────────────────────────────────
export const getMaterialInspections = (material, params) =>
  apiClient.get(`/api/${material}/inspections`, { params })

export const getMaterialInspection = (material, id) =>
  apiClient.get(`/api/${material}/inspections/${id}`)

export const uploadMaterialInspection = (material, file) => {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post(`/api/${material}/inspect`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

// ── Legacy steel endpoints (kept for backward compatibility) ──────────
export const getInspections = (params) =>
  apiClient.get('/api/inspections', { params })

export const getInspection = (id) =>
  apiClient.get(`/api/inspections/${id}`)

export const uploadInspection = (file) => {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post('/api/inspections/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}
