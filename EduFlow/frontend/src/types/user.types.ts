export interface ProfileResponse {
  userId: number
  login: string
  username: string
  avatar: string | null
  profile: string | null
  cardDetails: string | null
  status: boolean
  userRole: string
  createdAt: string
  statusSubscribtion: boolean
}

export interface ProfileUpdateRequest {
  username: string
  avatar: string | null
  profile: string | null
  cardDetails: string | null
}
