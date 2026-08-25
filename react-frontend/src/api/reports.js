import apiClient from './apiClient'

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
