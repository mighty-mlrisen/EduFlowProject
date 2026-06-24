<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { getSavedArticles } from '@/api/user.api'
import type { ArticleResponse } from '@/types/article.types'
import ArticleCard from '@/components/article/ArticleCard.vue'
import SortBar from '@/components/article/SortBar.vue'
import { useArticleSort } from '@/composables/useArticleSort'
import { onBeforeRouteLeave } from 'vue-router'

const PER_PAGE = 10

const articles = ref<ArticleResponse[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const { sortKey, sorted } = useArticleSort(articles)

const currentPage = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / PER_PAGE)))
const paginatedArticles = computed(() => {
  const start = (currentPage.value - 1) * PER_PAGE
  return sorted.value.slice(start, start + PER_PAGE)
})

watch(sortKey, () => { currentPage.value = 1 })
watch(currentPage, () => { window.scrollTo({ top: 0, behavior: 'smooth' }) })

onBeforeRouteLeave(() => {
  sessionStorage.setItem('saved:scroll', String(window.scrollY))
  sessionStorage.setItem('saved:page', String(currentPage.value))
})

function smartPages(current: number, total: number): (number | '…')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | '…')[] = [1]
  if (current > 3) pages.push('…')
  for (let p = Math.max(2, current - 1); p <= Math.min(total - 1, current + 1); p++) pages.push(p)
  if (current < total - 2) pages.push('…')
  pages.push(total)
  return pages
}

onMounted(async () => {
  const savedPage = sessionStorage.getItem('saved:page')
  if (savedPage) {
    currentPage.value = parseInt(savedPage)
    sessionStorage.removeItem('saved:page')
  }

  const savedScroll = sessionStorage.getItem('saved:scroll')

  loading.value = true
  try {
    articles.value = await getSavedArticles()
  } catch {
    error.value = 'Не удалось загрузить избранное'
  } finally {
    loading.value = false
  }

  if (savedScroll) {
    sessionStorage.removeItem('saved:scroll')
    await nextTick()
    window.scrollTo({ top: parseInt(savedScroll), behavior: 'instant' })
  }
})

function onUnsaved(articleId: number) {
  articles.value = articles.value.filter((a) => a.articleId !== articleId)
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">

    <h1 class="text-2xl font-bold text-gray-900 mb-8">Избранное</h1>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <p v-else-if="error" class="text-red-500 text-sm py-10 text-center">{{ error }}</p>

    <!-- Empty -->
    <div v-else-if="articles.length === 0" class="text-center py-20">
      <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M5 4a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 20V4z"/>
      </svg>
      <p class="text-sm font-medium text-gray-400">Избранных статей пока нет</p>
      <RouterLink to="/" class="mt-3 inline-block text-sm text-blue-600 hover:underline">
        Перейти к ленте
      </RouterLink>
    </div>

    <!-- Grid + pagination -->
    <div v-else>
      <SortBar v-model="sortKey" class="mb-5" />
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
        <ArticleCard
          v-for="article in paginatedArticles"
          :key="article.articleId"
          :article="article"
          @save-change="(saved: boolean) => { if (!saved) onUnsaved(article.articleId) }"
        />
      </div>
      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 mt-4">
        <button
          :disabled="currentPage === 1"
          @click="currentPage--"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >←</button>
        <template v-for="p in smartPages(currentPage, totalPages)" :key="String(p)">
          <span v-if="p === '…'" class="px-2 text-gray-400 text-sm select-none">…</span>
          <button
            v-else
            @click="currentPage = p as number"
            class="px-3 py-1.5 text-sm rounded-lg border transition-colors"
            :class="currentPage === p
              ? 'bg-blue-600 text-white border-blue-600'
              : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
          >{{ p }}</button>
        </template>
        <button
          :disabled="currentPage === totalPages"
          @click="currentPage++"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >→</button>
      </div>
    </div>

  </div>
</template>
