<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getGlobalStats, getUserStats } from '@/api/stats.api'
import type { GlobalStatsResponse, UserStatsResponse } from '@/types/stats.types'

type Tab = 'platform' | 'my'

const activeTab = ref<Tab>('platform')

const global = ref<GlobalStatsResponse | null>(null)
const user = ref<UserStatsResponse | null>(null)
const loadingGlobal = ref(true)
const loadingUser = ref(true)
const errorGlobal = ref<string | null>(null)
const errorUser = ref<string | null>(null)

onMounted(async () => {
  try {
    const [g, u] = await Promise.allSettled([getGlobalStats(), getUserStats()])
    loadingGlobal.value = false
    loadingUser.value = false
    if (g.status === 'fulfilled') global.value = g.value
    else {
      console.error('[StatsView] global stats failed:', (g as PromiseRejectedResult).reason)
      errorGlobal.value = 'Не удалось загрузить статистику платформы'
    }
    if (u.status === 'fulfilled') user.value = u.value
    else {
      console.error('[StatsView] user stats failed:', (u as PromiseRejectedResult).reason)
      errorUser.value = 'Не удалось загрузить личную статистику'
    }
  } catch (e) {
    console.error('[StatsView] unexpected error in onMounted:', e)
    loadingGlobal.value = false
    loadingUser.value = false
    errorGlobal.value = 'Ошибка загрузки'
    errorUser.value = 'Ошибка загрузки'
  }
})

const maxCategoryCount = computed(() =>
  Math.max(1, ...(global.value?.categoryStats?.map(c => c.articleCount) ?? [1]))
)

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' })
}

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">

    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Статистика</h1>
      <p class="text-sm text-gray-500 mt-1">Данные платформы и вашего профиля</p>
    </div>

    <!-- Tab switcher -->
    <div class="flex gap-1 bg-gray-100 rounded-xl p-1 mb-8 w-fit">
      <button
        @click="activeTab = 'platform'"
        class="px-5 py-2 text-sm font-medium rounded-lg transition-all"
        :class="activeTab === 'platform' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
      >
        Платформа
      </button>
      <button
        @click="activeTab = 'my'"
        class="px-5 py-2 text-sm font-medium rounded-lg transition-all"
        :class="activeTab === 'my' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
      >
        Моя статистика
      </button>
    </div>

    <!-- ══════════════ PLATFORM TAB ══════════════ -->
    <template v-if="activeTab === 'platform'">
      <div v-if="loadingGlobal" class="flex justify-center py-24">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
      <p v-else-if="errorGlobal" class="text-red-500 text-sm py-10 text-center">{{ errorGlobal }}</p>
      <template v-else-if="global">

        <!-- ── Counters grid ── -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Пользователи</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(global.totalUsers) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Опубликовано</p>
            <p class="text-3xl font-bold text-blue-600">{{ fmt(global.totalPublished) }}</p>
            <p class="text-xs text-gray-400 mt-1">черновиков: {{ fmt(global.totalDrafts) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Комментарии</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(global.totalComments) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Лайки</p>
            <p class="text-3xl font-bold text-pink-500">{{ fmt(global.totalLikes) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Подписки</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(global.totalSubscriptions) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Всего статей</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(global.totalArticles) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 col-span-2">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Новых пользователей за 7 дней</p>
            <p class="text-3xl font-bold text-green-600">+{{ fmt(global.newUsersLastWeek) }}</p>
          </div>
        </div>

        <!-- ── Top-10 articles by likes ── -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm mb-8">
          <div class="px-6 py-4 border-b border-gray-50">
            <h2 class="text-base font-semibold text-gray-800">Топ-10 статей по лайкам</h2>
          </div>
          <div v-if="!global.top10ArticlesByLikes?.length" class="px-6 py-8 text-sm text-gray-400 text-center">
            Нет данных
          </div>
          <div v-else>
            <div
              v-for="(item, i) in (global.top10ArticlesByLikes ?? [])"
              :key="item.articleId"
              class="flex items-center gap-4 px-6 py-3.5 hover:bg-gray-50 transition-colors"
              :class="i < (global.top10ArticlesByLikes?.length ?? 0) - 1 ? 'border-b border-gray-50' : ''"
            >
              <!-- Rank -->
              <span
                class="w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                :class="i === 0 ? 'bg-yellow-100 text-yellow-700'
                       : i === 1 ? 'bg-gray-100 text-gray-600'
                       : i === 2 ? 'bg-orange-100 text-orange-600'
                       : 'bg-gray-50 text-gray-400'"
              >{{ i + 1 }}</span>
              <!-- Title -->
              <RouterLink
                :to="`/article/${item.articleId}`"
                class="flex-1 min-w-0 text-sm font-medium text-gray-800 hover:text-blue-600 truncate transition-colors"
              >
                {{ item.title }}
              </RouterLink>
              <!-- Author -->
              <RouterLink
                v-if="item.authorUsername"
                :to="`/profile/${item.articleId}`"
                class="flex items-center gap-1.5 flex-shrink-0 mr-4"
              >
                <img
                  v-if="item.authorAvatar"
                  :src="item.authorAvatar"
                  class="w-5 h-5 rounded-full object-cover"
                />
                <div
                  v-else
                  class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold"
                >{{ item.authorUsername?.charAt(0)?.toUpperCase() }}</div>
                <span class="text-xs text-gray-500">{{ item.authorUsername }}</span>
              </RouterLink>
              <!-- Like count -->
              <div class="flex items-center gap-1 flex-shrink-0 min-w-[3.5rem] justify-end">
                <svg class="w-4 h-4 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
                <span class="text-sm font-semibold text-gray-700">{{ fmt(item.count) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Top-10 authors grid ── -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

          <!-- By likes -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
            <div class="px-6 py-4 border-b border-gray-50">
              <h2 class="text-base font-semibold text-gray-800">Топ-10 авторов по лайкам</h2>
            </div>
            <div v-if="!global.top10AuthorsByLikes?.length" class="px-6 py-8 text-sm text-gray-400 text-center">Нет данных</div>
            <div v-else>
              <div
                v-for="(author, i) in (global.top10AuthorsByLikes ?? [])"
                :key="author.userId"
                class="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 transition-colors"
                :class="i < (global.top10AuthorsByLikes?.length ?? 0) - 1 ? 'border-b border-gray-50' : ''"
              >
                <span class="w-5 text-xs text-gray-400 font-medium text-right flex-shrink-0">{{ i + 1 }}</span>
                <RouterLink :to="`/profile/${author.userId}`" class="flex items-center gap-2.5 flex-1 min-w-0">
                  <img v-if="author.avatar" :src="author.avatar" class="w-8 h-8 rounded-full object-cover flex-shrink-0" />
                  <div v-else class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {{ author.username?.charAt(0)?.toUpperCase() ?? '?' }}
                  </div>
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-800 truncate hover:text-blue-600 transition-colors">{{ author.username }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ author.login }}</p>
                  </div>
                </RouterLink>
                <div class="flex items-center gap-1 flex-shrink-0">
                  <svg class="w-3.5 h-3.5 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                  </svg>
                  <span class="text-sm font-semibold text-gray-700">{{ fmt(author.count) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- By subscribers -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
            <div class="px-6 py-4 border-b border-gray-50">
              <h2 class="text-base font-semibold text-gray-800">Топ-10 авторов по подписчикам</h2>
            </div>
            <div v-if="!global.top10AuthorsBySubscribers?.length" class="px-6 py-8 text-sm text-gray-400 text-center">Нет данных</div>
            <div v-else>
              <div
                v-for="(author, i) in (global.top10AuthorsBySubscribers ?? [])"
                :key="author.userId"
                class="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 transition-colors"
                :class="i < (global.top10AuthorsBySubscribers?.length ?? 0) - 1 ? 'border-b border-gray-50' : ''"
              >
                <span class="w-5 text-xs text-gray-400 font-medium text-right flex-shrink-0">{{ i + 1 }}</span>
                <RouterLink :to="`/profile/${author.userId}`" class="flex items-center gap-2.5 flex-1 min-w-0">
                  <img v-if="author.avatar" :src="author.avatar" class="w-8 h-8 rounded-full object-cover flex-shrink-0" />
                  <div v-else class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {{ author.username?.charAt(0)?.toUpperCase() ?? '?' }}
                  </div>
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-gray-800 truncate hover:text-blue-600 transition-colors">{{ author.username }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ author.login }}</p>
                  </div>
                </RouterLink>
                <div class="flex items-center gap-1 flex-shrink-0">
                  <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <span class="text-sm font-semibold text-gray-700">{{ fmt(author.count) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Category stats bar chart ── -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
          <div class="px-6 py-4 border-b border-gray-50">
            <h2 class="text-base font-semibold text-gray-800">Статьи по категориям</h2>
          </div>
          <div v-if="!global.categoryStats?.length" class="px-6 py-8 text-sm text-gray-400 text-center">Нет данных</div>
          <div v-else class="px-6 py-5 space-y-3">
            <div
              v-for="cat in (global.categoryStats ?? [])"
              :key="cat.categoryName"
              class="flex items-center gap-3"
            >
              <span class="text-sm text-gray-600 w-36 flex-shrink-0 truncate">{{ cat.categoryName }}</span>
              <div class="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                <div
                  class="h-2 rounded-full bg-blue-500 transition-all duration-500"
                  :style="{ width: (cat.articleCount / maxCategoryCount * 100) + '%' }"
                />
              </div>
              <span class="text-sm font-medium text-gray-700 w-10 text-right flex-shrink-0">{{ cat.articleCount }}</span>
            </div>
          </div>
        </div>

      </template>
    </template>

    <!-- ══════════════ MY STATS TAB ══════════════ -->
    <template v-else>
      <div v-if="loadingUser" class="flex justify-center py-24">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
      <p v-else-if="errorUser" class="text-red-500 text-sm py-10 text-center">{{ errorUser }}</p>
      <template v-else-if="user">

        <!-- ── Counters grid ── -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Опубликовано</p>
            <p class="text-3xl font-bold text-blue-600">{{ user.publishedArticles }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Черновики</p>
            <p class="text-3xl font-bold text-amber-500">{{ user.drafts }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Лайков получено</p>
            <p class="text-3xl font-bold text-pink-500">{{ fmt(user.totalLikesReceived) }}</p>
            <p class="text-xs text-gray-400 mt-1">
              среднее: {{ (user.avgLikesPerArticle ?? 0).toFixed(1) }} / статья
            </p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Комментариев написано</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(user.commentsGiven) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Подписчики</p>
            <p class="text-3xl font-bold text-indigo-600">{{ fmt(user.followersCount) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Подписки</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(user.subscriptionsCount) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Сохранено статей</p>
            <p class="text-3xl font-bold text-gray-900">{{ fmt(user.savedArticlesCount) }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Последняя публикация</p>
            <p class="text-sm font-semibold text-gray-800 mt-1 leading-tight">
              {{ formatDate(user.lastPublicationDate) }}
            </p>
          </div>
        </div>

        <!-- ── Activity last 30 days ── -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-5">
            <div class="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
              <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-400 font-medium uppercase tracking-wide">Статей за 30 дней</p>
              <p class="text-2xl font-bold text-gray-900 mt-0.5">{{ user.articlesLast30Days }}</p>
            </div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-5">
            <div class="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center flex-shrink-0">
              <svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-400 font-medium uppercase tracking-wide">Комментариев за 30 дней</p>
              <p class="text-2xl font-bold text-gray-900 mt-0.5">{{ user.commentsLast30Days }}</p>
            </div>
          </div>
        </div>

        <!-- ── Top-5 articles ── -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

          <!-- By likes -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
            <div class="px-6 py-4 border-b border-gray-50">
              <h2 class="text-base font-semibold text-gray-800">Мои топ-5 статей по лайкам</h2>
            </div>
            <div v-if="!user.top5ArticlesByLikes?.length" class="px-6 py-8 text-sm text-gray-400 text-center">
              Нет опубликованных статей
            </div>
            <div v-else>
              <div
                v-for="(item, i) in (user.top5ArticlesByLikes ?? [])"
                :key="item.articleId"
                class="flex items-center gap-3 px-5 py-3.5 hover:bg-gray-50 transition-colors"
                :class="i < (user.top5ArticlesByLikes?.length ?? 0) - 1 ? 'border-b border-gray-50' : ''"
              >
                <span
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  :class="i === 0 ? 'bg-yellow-100 text-yellow-700'
                         : i === 1 ? 'bg-gray-100 text-gray-500'
                         : i === 2 ? 'bg-orange-100 text-orange-600'
                         : 'bg-gray-50 text-gray-400'"
                >{{ i + 1 }}</span>
                <RouterLink
                  :to="`/article/${item.articleId}`"
                  class="flex-1 min-w-0 text-sm font-medium text-gray-800 hover:text-blue-600 truncate transition-colors"
                >{{ item.title }}</RouterLink>
                <div class="flex items-center gap-1 flex-shrink-0">
                  <svg class="w-3.5 h-3.5 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                  </svg>
                  <span class="text-sm font-semibold text-gray-700">{{ item.count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- By comments -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
            <div class="px-6 py-4 border-b border-gray-50">
              <h2 class="text-base font-semibold text-gray-800">Мои топ-5 статей по комментариям</h2>
            </div>
            <div v-if="!user.top5ArticlesByComments?.length" class="px-6 py-8 text-sm text-gray-400 text-center">
              Нет опубликованных статей
            </div>
            <div v-else>
              <div
                v-for="(item, i) in (user.top5ArticlesByComments ?? [])"
                :key="item.articleId"
                class="flex items-center gap-3 px-5 py-3.5 hover:bg-gray-50 transition-colors"
                :class="i < (user.top5ArticlesByComments?.length ?? 0) - 1 ? 'border-b border-gray-50' : ''"
              >
                <span
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  :class="i === 0 ? 'bg-yellow-100 text-yellow-700'
                         : i === 1 ? 'bg-gray-100 text-gray-500'
                         : i === 2 ? 'bg-orange-100 text-orange-600'
                         : 'bg-gray-50 text-gray-400'"
                >{{ i + 1 }}</span>
                <RouterLink
                  :to="`/article/${item.articleId}`"
                  class="flex-1 min-w-0 text-sm font-medium text-gray-800 hover:text-blue-600 truncate transition-colors"
                >{{ item.title }}</RouterLink>
                <div class="flex items-center gap-1 flex-shrink-0">
                  <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                  </svg>
                  <span class="text-sm font-semibold text-gray-700">{{ item.count }}</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </template>
    </template>

  </div>
</template>
