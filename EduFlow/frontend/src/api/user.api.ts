import api from './axios'
import type { ProfileResponse, ProfileUpdateRequest } from '@/types/user.types'
import type { ArticleResponse } from '@/types/article.types'

// --- Профиль ---

export function getMyProfile(): Promise<ProfileResponse> {
  return api.get<ProfileResponse>('/user/profile').then((r) => r.data)
}

export function getProfileById(userId: number): Promise<ProfileResponse> {
  return api.get<ProfileResponse>(`/user/profile/${userId}`).then((r) => r.data)
}

export function updateProfile(payload: ProfileUpdateRequest): Promise<ProfileResponse> {
  return api.put<ProfileResponse>('/user/profile', payload).then((r) => r.data)
}

// --- Подписки ---

export function subscribe(userId: number, status: boolean): Promise<ProfileResponse> {
  return api.post<ProfileResponse>(`/user/subscribtion/${userId}`, null, { params: { status } }).then((r) => r.data)
}

export function getMySubscriptions(): Promise<ProfileResponse[]> {
  return api.get<ProfileResponse[]>('/user/subscribtion').then((r) => r.data)
}

export function getUserSubscriptions(userId: number): Promise<ProfileResponse[]> {
  return api.get<ProfileResponse[]>(`/user/subscribtion/${userId}`).then((r) => r.data)
}

export function getMySubscribers(): Promise<ProfileResponse[]> {
  return api.get<ProfileResponse[]>('/user/subscribers').then((r) => r.data)
}

export function getUserSubscribers(userId: number): Promise<ProfileResponse[]> {
  return api.get<ProfileResponse[]>(`/user/subscribers/${userId}`).then((r) => r.data)
}

// --- Сохранённые статьи ---

export function toggleSaveArticle(articleId: number, status: boolean): Promise<ArticleResponse> {
  return api.post<ArticleResponse>(`/user/save/article/${articleId}`, null, { params: { status } }).then((r) => r.data)
}

export function getSavedArticles(): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>('/user/saved/articles').then((r) => r.data)
}

export function searchUsers(query: string): Promise<ProfileResponse[]> {
  return api.get<ProfileResponse[]>('/user/search', { params: { username: query } }).then((r) => r.data)
}
