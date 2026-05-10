import { apiRequest } from '@/services/apiClient'
import type { AuthCredentials, AuthResponse } from '@/types/auth'

export async function registerApi(
  payload: AuthCredentials,
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function loginApi(payload: AuthCredentials): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function logoutApi(): Promise<{ message: string }> {
  return apiRequest<{ message: string }>('/auth/logout', {
    method: 'POST',
  })
}

export async function fetchCurrentUserApi(): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/auth/me')
}
