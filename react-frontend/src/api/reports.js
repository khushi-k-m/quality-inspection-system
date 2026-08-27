import apiClient from './apiClient'

// ── Material-aware (new) ──────────────────────────────────────────────
export const getMaterialReports = (material) =>
  apiClient.get(`/api/${material}/reports`)

export const getMaterialReportDownload = async (material, inspectionId) => {
  const response = await apiClient.get(
    `/api/${material}/reports/${inspectionId}/download`,
    { responseType: 'blob', timeout: 30000 }
  )
  const url  = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href  = url
  link.setAttribute('download', `${inspectionId}_inspection_report.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// ── Legacy steel-only (kept for backward compatibility) ───────────────
export const getReports = () => apiClient.get('/api/reports')

export const downloadReport = async (inspectionId) => {
  const response = await apiClient.get(`/api/reports/${inspectionId}/download`, {
    responseType: 'blob',
  })
  const url  = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href  = url
  link.setAttribute('download', `${inspectionId}_inspection_report.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
