<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { getProfileById, getUserSubscriptions, getUserSubscribers } from '@/api/user.api'
import { getArticlesByUserId } from '@/api/article.api'
import { onBeforeRouteLeave } from 'vue-router'
import type { ProfileResponse } from '@/types/user.types'
import type { ArticleResponse } from '@/types/article.types'
import { useAuthStore } from '@/stores/auth.store'
import SubscribeButton from '@/components/user/SubscribeButton.vue'
import FeedArticleCard from '@/components/article/FeedArticleCard.vue'
import SortBar from '@/components/article/SortBar.vue'
import UserCard from '@/components/user/UserCard.vue'
import { useArticleSort } from '@/composables/useArticleSort'

const props = defineProps<{ userId: number }>()
const auth = useAuthStore()

const profile = ref<ProfileResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const subscriptions = ref<ProfileResponse[]>([])
const subscribers = ref<ProfileResponse[]>([])

const articles = ref<ArticleResponse[]>([])
const articlesLoaded = ref(false)
const articlesLoading = ref(false)

type Tab = 'articles' | 'subscriptions'
const activeTab = ref<Tab>('articles')

const searchQuery = ref('')

const { sortKey, sorted: sortedArticles } = useArticleSort(articles)

const filteredArticles = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return sortedArticles.value
  return sortedArticles.value.filter(
    (a) =>
      a.title.toLowerCase().includes(q) ||
      (a.description?.toLowerCase() ?? '').includes(q)
  )
})

const filteredSubscriptions = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return subscriptions.value
  return subscriptions.value.filter(
    (u) =>
      (u.username?.toLowerCase() ?? '').includes(q) ||
      u.login.toLowerCase().includes(q)
  )
})

// Pagination (articles only)
const ITEMS_PER_PAGE = 10
const currentPage = ref(1)

const totalPages = computed(() => Math.max(1, Math.ceil(filteredArticles.value.length / ITEMS_PER_PAGE)))

const paginatedArticles = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return filteredArticles.value.slice(start, start + ITEMS_PER_PAGE)
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

watch([sortKey, searchQuery], () => { currentPage.value = 1 })

function goToPage(p: number) {
  currentPage.value = p
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onBeforeRouteLeave(() => {
  sessionStorage.setItem(`profile-${props.userId}:scroll`, String(window.scrollY))
})

onMounted(async () => {
  const savedScroll = sessionStorage.getItem(`profile-${props.userId}:scroll`)

  try {
    const [p, subs, sbrs] = await Promise.all([
      getProfileById(props.userId),
      getUserSubscriptions(props.userId),
      getUserSubscribers(props.userId)
    ])
    profile.value = p
    subscriptions.value = subs
    subscribers.value = sbrs
    await loadArticles()
  } catch {
    error.value = 'Пользователь не найден'
  } finally {
    loading.value = false
  }

  if (savedScroll) {
    sessionStorage.removeItem(`profile-${props.userId}:scroll`)
    await nextTick()
    window.scrollTo({ top: parseInt(savedScroll), behavior: 'instant' })
  }
})

async function loadArticles() {
  if (articlesLoaded.value) return
  articlesLoading.value = true
  try {
    const all = await getArticlesByUserId(props.userId)
    articles.value = all.filter((a) => !a.draft)
    articlesLoaded.value = true
  } catch {}
  finally { articlesLoading.value = false }
}

function onLikeUpdate(articleId: number, likes: number) {
  const art = articles.value.find((a) => a.articleId === articleId)
  if (art) art.likes = likes
}

function setTab(tab: Tab) {
  activeTab.value = tab
  searchQuery.value = ''
  currentPage.value = 1
  if (tab === 'articles' && !articlesLoaded.value) loadArticles()
}

const initials = computed(() => {
  const name = profile.value?.username || profile.value?.login || '?'
  return name.charAt(0).toUpperCase()
})

const isOwnProfile = computed(() => auth.currentUserId === props.userId)

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}
</script>

<template>
  <div class="max-w-3xl mx-auto px-6 py-10">

    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="error" class="text-center py-20 text-red-500">{{ error }}</div>

    <div v-else-if="profile">

      <!-- Profile card -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
        <div class="flex items-start gap-5">

          <div class="flex-shrink-0">
            <img
              v-if="profile.avatar"
              :src="profile.avatar"
              :alt="profile.username"
              class="w-20 h-20 rounded-full object-cover border border-gray-200"
            />
            <div
              v-else
              class="w-20 h-20 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-3xl font-bold"
            >
              {{ initials }}
            </div>
          </div>

          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h1 class="text-xl font-bold text-gray-900 leading-tight">
                  {{ profile.username || 'Без имени' }}
                </h1>
                <p class="text-sm text-gray-400 mt-0.5">{{ profile.login }}</p>
              </div>
              <SubscribeButton
                v-if="!isOwnProfile"
                :user-id="profile.userId"
                :subscribed="profile.statusSubscribtion"
              />
            </div>

            <div class="flex items-center gap-5 mt-3">
              <div class="text-sm text-gray-500">
                <span class="font-semibold text-gray-800">{{ subscriptions.length }}</span> подписок
              </div>
              <div class="text-sm text-gray-500">
                <span class="font-semibold text-gray-800">{{ subscribers.length }}</span> подписчиков
              </div>
            </div>

            <div class="flex flex-wrap gap-2 mt-2">
              <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full">
                Пользователь
              </span>
              <span
                :class="profile.status ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'"
                class="px-2.5 py-0.5 text-xs font-medium rounded-full"
              >
                {{ profile.status ? 'Активен' : 'Неактивен' }}
              </span>
            </div>

            <p v-if="profile.createdAt" class="text-xs text-gray-400 mt-2">
              Зарегистрирован {{ formatDate(profile.createdAt) }}
            </p>
          </div>
        </div>

        <div v-if="profile.profile || profile.cardDetails" class="mt-4 pt-4 border-t border-gray-100">
          <p v-if="profile.profile" class="text-sm text-gray-600 leading-relaxed">
            {{ profile.profile }}
          </p>
          <p v-if="profile.cardDetails" class="text-xs text-gray-400 mt-2">
            {{ profile.cardDetails }}
          </p>
        </div>
      </div>

      <!-- Tab switcher -->
      <div class="flex border-b border-gray-200 mb-5">
        <button
          @click="setTab('articles')"
          class="px-5 py-3 text-base font-medium border-b-2 transition-colors -mb-px"
          :class="activeTab === 'articles'
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Статьи автора
        </button>
        <button
          @click="setTab('subscriptions')"
          class="px-5 py-3 text-base font-medium border-b-2 transition-colors -mb-px"
          :class="activeTab === 'subscriptions'
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Подписки
          <span class="ml-1 text-sm" :class="activeTab === 'subscriptions' ? 'text-blue-400' : 'text-gray-400'">
            {{ subscriptions.length }}
          </span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="relative mb-4">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="activeTab === 'articles' ? 'Поиск по статьям...' : 'Поиск по пользователям...'"
          class="w-full pl-9 pr-4 py-2.5 text-sm bg-gray-100 border border-transparent rounded-xl outline-none focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all"
        />
      </div>

      <!-- Articles tab -->
      <template v-if="activeTab === 'articles'">
        <SortBar v-model="sortKey" class="mb-5" />

        <div v-if="articlesLoading" class="flex justify-center py-10">
          <div class="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        </div>
        <p v-else-if="filteredArticles.length === 0 && !articlesLoading" class="text-gray-400 py-10 text-center">
          {{ articles.length === 0 ? 'Нет опубликованных статей' : 'Ничего не найдено' }}
        </p>
        <template v-else>
          <div>
            <FeedArticleCard
              v-for="article in paginatedArticles"
              :key="article.articleId"
              :article="article"
              @like-update="onLikeUpdate"
            />
          </div>

          <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 mt-10">
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="w-9 h-9 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            <template v-for="(p, i) in visiblePages" :key="i">
              <span v-if="p === '...'" class="w-9 h-9 flex items-center justify-center text-sm text-gray-400">…</span>
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
              class="w-9 h-9 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
        </template>
      </template>

      <!-- Subscriptions tab -->
      <template v-if="activeTab === 'subscriptions'">
        <p v-if="filteredSubscriptions.length === 0" class="text-gray-400 py-10 text-center">
          {{ subscriptions.length === 0 ? 'Нет подписок' : 'Ничего не найдено' }}
        </p>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <UserCard
            v-for="user in filteredSubscriptions"
            :key="user.userId"
            :profile="user"
          />
        </div>
      </template>

    </div>
  </div>
</template>
