import apiClient from './apiClient'

export const login = (username, password) =>
  apiClient.post('/api/auth/login', { username, password })

export const logout = () =>
  apiClient.post('/api/auth/logout')

export const register = (username, email, password, confirm_password) =>
  apiClient.post('/api/auth/register', { username, email, password, confirm_password })

export const forgotPassword = (email) =>
  apiClient.post('/api/auth/forgot-password', { email })

export const resetPassword = (token, new_password, confirm_password) =>
  apiClient.post('/api/auth/reset-password', { token, new_password, confirm_password })
