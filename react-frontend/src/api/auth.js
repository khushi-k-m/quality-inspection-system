import apiClient from './apiClient'

export const login = (username, password) =>
  apiClient.post('/api/auth/login', { username, password })

export const logout = () =>
  apiClient.post('/api/auth/logout')
