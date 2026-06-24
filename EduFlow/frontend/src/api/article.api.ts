import api from './axios'
import type { ArticleRequest, ArticleResponse, CategoryEntity, CommentRequest, CommentResponse } from '@/types/article.types'

// --- Статьи ---

export function getAllArticles(): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>('/article').then((r) => r.data)
}

export function getMyArticles(): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>('/user/article').then((r) => r.data)
}

export function getArticlesByUserId(userId: number): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>(`/user/article/user/${userId}`).then((r) => r.data)
}

export function getArticleById(articleId: number): Promise<ArticleResponse> {
  return api.get<ArticleResponse>(`/user/article/${articleId}`).then((r) => r.data)
}

export function getArticlesByCategory(categoryId: number): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>(`/user/article/category/${categoryId}`).then((r) => r.data)
}

export function getMyDrafts(): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>('/user/article/draft').then((r) => r.data)
}

export function getSubscriptionFeed(): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>('/user/subscribtion/article').then((r) => r.data)
}

export function searchArticles(query: string): Promise<ArticleResponse[]> {
  return api.get<ArticleResponse[]>('/article/search', { params: { line: query } }).then((r) => r.data)
}

export function createArticle(payload: ArticleRequest): Promise<ArticleResponse> {
  return api.post<ArticleResponse>('/user/article', payload).then((r) => r.data)
}

// Бэкенд принимает articleId через query param (особенность реализации)
export function updateArticle(articleId: number, payload: ArticleRequest): Promise<ArticleResponse> {
  return api.put<ArticleResponse>(`/user/article/${articleId}`, payload, { params: { articleId } }).then((r) => r.data)
}

export function deleteArticle(articleId: number): Promise<void> {
  return api.delete(`/user/article/${articleId}`).then(() => {})
}

// --- Категории ---

export function getCategories(): Promise<CategoryEntity[]> {
  return api.get<CategoryEntity[]>('/article/category').then((r) => r.data)
}

// --- Реакции ---

export function toggleReaction(articleId: number, reaction: boolean): Promise<ArticleResponse> {
  return api.post<ArticleResponse>(`/user/article/${articleId}/reaction`, null, { params: { reaction } }).then((r) => r.data)
}

export function getReactionCount(articleId: number): Promise<number> {
  return api.get<number>(`/user/article/reaction/count/${articleId}`).then((r) => r.data)
}

// --- Саммари ---

export function getArticleSummary(articleId: number): Promise<string> {
  return api.get<{ summary: string }>(`/user/article/${articleId}/summary`).then((r) => r.data.summary)
}

// --- Комментарии ---

export function createComment(articleId: number, payload: CommentRequest): Promise<CommentResponse> {
  return api.post<CommentResponse>(`/user/article/${articleId}/comment`, payload).then((r) => r.data)
}

export function getComments(articleId: number): Promise<CommentResponse[]> {
  return api.get<CommentResponse[]>(`/user/article/${articleId}/comment`).then((r) => r.data)
}
