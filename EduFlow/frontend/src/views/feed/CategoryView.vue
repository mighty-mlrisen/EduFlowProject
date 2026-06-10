<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getArticlesByCategory, getCategories } from '@/api/article.api'
import type { ArticleResponse, CategoryEntity } from '@/types/article.types'
import FeedArticleCard from '@/components/article/FeedArticleCard.vue'
import SortBar from '@/components/article/SortBar.vue'
import { useArticleSort } from '@/composables/useArticleSort'

const props = defineProps<{ categoryId: number }>()

const articles = ref<ArticleResponse[]>([])
const categoryName = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)

const ITEMS_PER_PAGE = 10
const currentPage = ref(1)

const { sortKey, sorted } = useArticleSort(articles)

watch(sortKey, () => { currentPage.value = 1 })

async function load(id: number) {
  loading.value = true
  error.value = null
  currentPage.value = 1
  articles.value = []
  categoryName.value = ''
  try {
    const [data, cats] = await Promise.all([
      getArticlesByCategory(id),
      getCategories()
    ])
    const cat = cats.find((c: CategoryEntity) => c.id === id)
    categoryName.value = cat?.name ?? ''
    articles.value = data.filter((a) => !a.draft)
  } catch {
    error.value = 'Не удалось загрузить статьи'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(props.categoryId))
watch(() => props.categoryId, (id) => load(id))

const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / ITEMS_PER_PAGE)))

const paginatedArticles = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return sorted.value.slice(start, start + ITEMS_PER_PAGE)
})

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
  <div class="max-w-3xl mx-auto px-6 py-8">

    <!-- Heading -->
    <div class="mb-6">
      <p class="text-sm text-blue-600 font-medium uppercase tracking-wide mb-1">Категория</p>
      <h1 class="text-3xl font-bold text-gray-900">{{ categoryName || '...' }}</h1>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <p v-else-if="error" class="text-red-500 text-sm py-10 text-center">{{ error }}</p>

    <!-- Empty -->
    <div v-else-if="articles.length === 0" class="text-center py-20">
      <p class="text-gray-400">В этой категории пока нет статей</p>
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

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 mt-10">

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

        <template v-for="(p, i) in visiblePages" :key="i">
          <span
            v-if="p === '...'"
            class="w-9 h-9 flex items-center justify-center text-sm text-gray-400"
          >…</span>
          <button
            v-else
            @click="goToPage(p as number)"
            class="w-9 h-9 rounded-lg text-sm font-medium transition-colors"
            :class="p === currentPage ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'"
          >
            {{ p }}
          </button>
        </template>

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
