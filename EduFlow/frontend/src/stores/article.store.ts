import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as articleApi from '@/api/article.api'
import type { ArticleResponse, ArticleRequest, CategoryEntity, CommentResponse } from '@/types/article.types'

export const useArticleStore = defineStore('article', () => {
  const articles = ref<ArticleResponse[]>([])
  const currentArticle = ref<ArticleResponse | null>(null)
  const comments = ref<CommentResponse[]>([])
  const categories = ref<CategoryEntity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // --- Загрузка списков ---

  async function fetchAllArticles() {
    loading.value = true
    error.value = null
    try {
      articles.value = await articleApi.getAllArticles()
    } catch {
      error.value = 'Не удалось загрузить статьи'
    } finally {
      loading.value = false
    }
  }

  async function fetchMyArticles() {
    loading.value = true
    try {
      articles.value = await articleApi.getMyArticles()
    } finally {
      loading.value = false
    }
  }

  async function fetchArticlesByUser(userId: number) {
    loading.value = true
    try {
      articles.value = await articleApi.getArticlesByUserId(userId)
    } finally {
      loading.value = false
    }
  }

  async function fetchSubscriptionFeed() {
    loading.value = true
    try {
      articles.value = await articleApi.getSubscriptionFeed()
    } finally {
      loading.value = false
    }
  }

  async function fetchByCategory(categoryId: number) {
    loading.value = true
    try {
      articles.value = await articleApi.getArticlesByCategory(categoryId)
    } finally {
      loading.value = false
    }
  }

  async function fetchMyDrafts() {
    loading.value = true
    try {
      articles.value = await articleApi.getMyDrafts()
    } finally {
      loading.value = false
    }
  }

  async function search(query: string) {
    loading.value = true
    try {
      articles.value = await articleApi.searchArticles(query)
    } finally {
      loading.value = false
    }
  }

  // --- Одиночная статья ---

  async function fetchArticleById(articleId: number) {
    loading.value = true
    error.value = null
    try {
      currentArticle.value = await articleApi.getArticleById(articleId)
    } catch {
      error.value = 'Статья не найдена'
    } finally {
      loading.value = false
    }
  }

  // --- CRUD ---

  async function createArticle(payload: ArticleRequest): Promise<ArticleResponse> {
    const created = await articleApi.createArticle(payload)
    articles.value.unshift(created)
    return created
  }

  async function updateArticle(articleId: number, payload: ArticleRequest): Promise<ArticleResponse> {
    const updated = await articleApi.updateArticle(articleId, payload)
    const idx = articles.value.findIndex((a) => a.articleId === articleId)
    if (idx !== -1) articles.value[idx] = updated
    if (currentArticle.value?.articleId === articleId) currentArticle.value = updated
    return updated
  }

  // --- Реакции и сохранения ---

  async function toggleReaction(articleId: number, reaction: boolean) {
    const updated = await articleApi.toggleReaction(articleId, reaction)
    patchArticle(updated)
    return updated
  }

  async function toggleSave(articleId: number, status: boolean) {
    const { toggleSaveArticle } = await import('@/api/user.api')
    const updated = await toggleSaveArticle(articleId, status)
    patchArticle(updated)
    return updated
  }

  // --- Комментарии ---

  async function fetchComments(articleId: number) {
    comments.value = await articleApi.getComments(articleId)
  }

  async function postComment(articleId: number, text: string) {
    const comment = await articleApi.createComment(articleId, { comment: text })
    comments.value.push(comment)
    return comment
  }

  // --- Категории ---

  async function fetchCategories() {
    if (categories.value.length) return
    categories.value = await articleApi.getCategories()
  }

  // --- Helpers ---

  function patchArticle(updated: ArticleResponse) {
    const idx = articles.value.findIndex((a) => a.articleId === updated.articleId)
    if (idx !== -1) articles.value[idx] = updated
    if (currentArticle.value?.articleId === updated.articleId) currentArticle.value = updated
  }

  return {
    articles,
    currentArticle,
    comments,
    categories,
    loading,
    error,
    fetchAllArticles,
    fetchMyArticles,
    fetchArticlesByUser,
    fetchSubscriptionFeed,
    fetchByCategory,
    fetchMyDrafts,
    search,
    fetchArticleById,
    createArticle,
    updateArticle,
    toggleReaction,
    toggleSave,
    fetchComments,
    postComment,
    fetchCategories
  }
})
