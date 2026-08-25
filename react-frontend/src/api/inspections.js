import apiClient from './apiClient'

export const getInspections = (params) =>
  apiClient.get('/api/inspections', { params })

export const getInspection = (id) =>
  apiClient.get(`/api/inspections/${id}`)

export const uploadInspection = (file) => {
  const form = new FormData()
  form.append('file', file)
  return apiClient.post('/api/inspections/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // YOLO can take a moment on first run
  })
}
