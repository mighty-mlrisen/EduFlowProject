import type { ProfileResponse } from './user.types'

export interface CategoryEntity {
  id: number
  name: string
}

export interface ArticleRequest {
  categoryName: string
  title: string
  description: string
  text: string
  image: string | null
  draft: boolean
}

export interface ArticleResponse {
  currentUserId: number
  articleId: number
  users: ProfileResponse
  category: CategoryEntity
  title: string
  text: string
  description: string
  image: string | null
  createdAt: string
  updatedAt: string | null
  draft: boolean
  statusSave: boolean
  likes: number
  statusLike: boolean
  commentsCount: number
}

export interface CommentRequest {
  comment: string
  parentCommentId?: number | null
}

export interface CommentResponse {
  commentId: number
  article: ArticleResponse
  author: ProfileResponse
  comment: string
  createdAt: string | null
  parentCommentId: number | null
}
