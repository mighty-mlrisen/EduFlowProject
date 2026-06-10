export interface AuthRequest {
  login: string
  password: string
}

export interface SignUpRequest {
  login: string
  password: string
  username: string
  userRole?: string
  cardDetails?: string | null
  profile?: string | null
}

export interface JwtResponse {
  id: number
  login: string
  username: string
  role: string
  accessToken: string
  type: string
  refreshToken: string
}

export interface TokenRefreshRequest {
  refreshToken: string
}

export interface TokenRefreshResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
}
