import api from './axios'
import type { AuthRequest, SignUpRequest, JwtResponse, TokenRefreshResponse } from '@/types/auth.types'

export function signIn(payload: AuthRequest): Promise<JwtResponse> {
  return api.post<JwtResponse>('/auth/signin', payload).then((r) => r.data)
}

export function signUp(payload: SignUpRequest): Promise<JwtResponse> {
  return api.post<JwtResponse>('/auth/signup', payload).then((r) => r.data)
}

export function refreshToken(token: string): Promise<TokenRefreshResponse> {
  return api.post<TokenRefreshResponse>('/auth/refreshtoken', { refreshToken: token }).then((r) => r.data)
}
