<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth.store'
import { getAllArticles } from '@/api/article.api'
import type { ArticleResponse } from '@/types/article.types'
import FeedArticleCard from '@/components/article/FeedArticleCard.vue'
import SortBar from '@/components/article/SortBar.vue'
import { useArticleSort } from '@/composables/useArticleSort'
import { onBeforeRouteLeave } from 'vue-router'

const auth = useAuthStore()

const articles = ref<ArticleResponse[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const ITEMS_PER_PAGE = 10
const currentPage = ref(1)

const { sortKey, sorted } = useArticleSort(articles)

watch(sortKey, () => { currentPage.value = 1 })

onBeforeRouteLeave(() => {
  sessionStorage.setItem('feed:scroll', String(window.scrollY))
  sessionStorage.setItem('feed:page', String(currentPage.value))
})

onMounted(async () => {
  const savedPage = sessionStorage.getItem('feed:page')
  if (savedPage) {
    currentPage.value = parseInt(savedPage)
    sessionStorage.removeItem('feed:page')
  }

  if (!auth.isAuthenticated) return

  const savedScroll = sessionStorage.getItem('feed:scroll')

  loading.value = true
  try {
    const all = await getAllArticles()
    articles.value = all.filter((a) => !a.draft)
  } catch {
    error.value = 'Не удалось загрузить статьи'
  } finally {
    loading.value = false
  }

  if (savedScroll) {
    sessionStorage.removeItem('feed:scroll')
    await nextTick()
    window.scrollTo({ top: parseInt(savedScroll), behavior: 'instant' })
  }
})

const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / ITEMS_PER_PAGE)))

const paginatedArticles = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return sorted.value.slice(start, start + ITEMS_PER_PAGE)
})

// Smart pagination: first, last, current±1, ellipsis between gaps
const visiblePages = computed<(number | '...')[]>(() => {
  const total = totalPages.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const cur = currentPage.value
  const pages: (number | '...')[] = [1]

  if (cur > 3) pages.push('...')

  const from = Math.max(2, cur - 1)
  const to = Math.min(total - 1, cur + 1)
  for (let i = from; i <= to; i++) pages.push(i)

  if (cur < total - 2) pages.push('...')
  pages.push(total)

  return pages
})

function goToPage(p: number) {
  currentPage.value = p
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onLikeUpdate(articleId: number, likes: number) {
  const art = articles.value.find((a) => a.articleId === articleId)
  if (art) art.likes = likes
}
</script>

<template>
  <div>

    <!-- ── Guest: hero ── -->
    <template v-if="!auth.isAuthenticated">
      <div class="max-w-6xl mx-auto px-6 py-12">
        <div class="flex flex-col items-center text-center py-16 gap-6">
          <h1 class="text-5xl font-bold text-gray-900 leading-tight">
            Добро пожаловать в <span class="text-blue-600">EduFlow</span>
          </h1>
          <p class="text-lg text-gray-500 max-w-xl">
            Платформа для IT-статей и обмена знаниями.
            Читайте, пишите, подписывайтесь на авторов.
          </p>
          <div class="flex gap-3 mt-2">
            <RouterLink
              to="/register"
              class="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-full hover:bg-blue-700 transition-colors"
            >
              Начать бесплатно
            </RouterLink>
            <RouterLink
              to="/login"
              class="px-6 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-full hover:border-blue-400 hover:text-blue-600 transition-colors"
            >
              Войти
            </RouterLink>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Authenticated: article feed ── -->
    <template v-else>
      <div class="max-w-3xl mx-auto px-6 py-8">

        <h1 class="text-2xl font-bold text-gray-900 mb-4">Все статьи</h1>

        <!-- Loading -->
        <div v-if="loading" class="flex justify-center py-20">
          <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>

        <!-- Error -->
        <p v-else-if="error" class="text-red-500 text-sm py-10 text-center">{{ error }}</p>

        <!-- Empty -->
        <div v-else-if="articles.length === 0" class="text-center py-20">
          <p class="text-gray-400">Пока нет опубликованных статей</p>
          <RouterLink to="/publish" class="mt-3 inline-block text-sm text-blue-600 hover:underline">
            Написать первую статью
          </RouterLink>
        </div>

        <!-- Feed -->
        <template v-else>
          <SortBar v-model="sortKey" class="mb-5" />
          <div>
            <FeedArticleCard
              v-for="article in paginatedArticles"
              :key="article.articleId"
              :article="article"
              @like-update="onLikeUpdate"
            />
          </div>

          <!-- ── Pagination ── -->
          <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 mt-10">

            <!-- Prev -->
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="w-9 h-9 flex items-center justify-center rounded-lg text-gray-500
                     hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>

            <!-- Page numbers -->
            <template v-for="(p, i) in visiblePages" :key="i">
              <span
                v-if="p === '...'"
                class="w-9 h-9 flex items-center justify-center text-sm text-gray-400"
              >…</span>
              <button
                v-else
                @click="goToPage(p as number)"
                class="w-9 h-9 rounded-lg text-sm font-medium transition-colors"
                :class="p === currentPage
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'"
              >
                {{ p }}
              </button>
            </template>

            <!-- Next -->
            <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="w-9 h-9 flex items-center justify-center rounded-lg text-gray-500
                     hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </button>

          </div>
        </template>

      </div>
    </template>

  </div>
</template>
