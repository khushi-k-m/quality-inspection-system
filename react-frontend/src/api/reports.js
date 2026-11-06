import apiClient from './apiClient'

// ── Material-aware reports ──────────────────────────────────────────
export const getMaterialReports = (material) =>
  apiClient.get(`/api/${material}/reports`)

export const getMaterialReportDownload = async (material, inspectionId, params = {}) => {
  const query = new URLSearchParams(params).toString()
  const path = material && material !== 'auto'
    ? `/api/${material}/reports/${inspectionId}/download${query ? `?${query}` : ''}`
    : `/api/reports/${inspectionId}/download${query ? `?${query}` : ''}`

  const response = await apiClient.get(path, {
    responseType: 'blob',
    timeout: 35000,
  })
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${inspectionId}_inspection_report.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// ── Download with client & company details ───────────────────────────
export const downloadReportWithDetails = async (inspectionId, params = {}) => {
  const query = new URLSearchParams(params).toString()
  const response = await apiClient.get(
    `/api/reports/${inspectionId}/download${query ? `?${query}` : ''}`,
    { responseType: 'blob', timeout: 35000 }
  )
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${inspectionId}_inspection_report.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// ── Legacy steel-only (backward compatibility) ───────────────────────
export const getReports = () => apiClient.get('/api/reports')

export const downloadReport = async (inspectionId) => {
  const response = await apiClient.get(`/api/reports/${inspectionId}/download`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${inspectionId}_inspection_report.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
