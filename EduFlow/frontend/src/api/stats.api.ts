import api from './axios'
import type { GlobalStatsResponse, UserStatsResponse } from '@/types/stats.types'

export function getGlobalStats(): Promise<GlobalStatsResponse> {
  return api.get<GlobalStatsResponse>('/stats/global').then(r => r.data)
}

export function getUserStats(): Promise<UserStatsResponse> {
  return api.get<UserStatsResponse>('/user/stats').then(r => r.data)
}
