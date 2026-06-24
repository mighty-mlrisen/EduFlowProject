<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useUserStore } from '@/stores/user.store'
import { getMySubscriptions, getMySubscribers } from '@/api/user.api'
import { getMyArticles } from '@/api/article.api'
import { onBeforeRouteLeave } from 'vue-router'
import type { ProfileResponse } from '@/types/user.types'
import type { ArticleResponse } from '@/types/article.types'
import FeedArticleCard from '@/components/article/FeedArticleCard.vue'
import SortBar from '@/components/article/SortBar.vue'
import UserCard from '@/components/user/UserCard.vue'
import { useArticleSort } from '@/composables/useArticleSort'
import { useThemeStore } from '@/stores/theme.store'

const userStore = useUserStore()
const themeStore = useThemeStore()

const isEditing = ref(false)
const saveLoading = ref(false)
const saveError = ref<string | null>(null)
const saveSuccess = ref(false)

const form = reactive({
  username: '',
  avatar: '',
  profile: '',
  cardDetails: ''
})

// Tabs
type Tab = 'articles' | 'subscriptions' | 'followers'
const activeTab = ref<Tab>('articles')

// Data
const subscriptions = ref<ProfileResponse[]>([])
const followers = ref<ProfileResponse[]>([])
const articles = ref<ArticleResponse[]>([])
const tabDataLoading = ref(false)

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

const filteredFollowers = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return followers.value
  return followers.value.filter(
    (u) =>
      (u.username?.toLowerCase() ?? '').includes(q) ||
      u.login.toLowerCase().includes(q)
  )
})

// Pagination
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
  sessionStorage.setItem('my-profile:scroll', String(window.scrollY))
})

onMounted(async () => {
  const savedScroll = sessionStorage.getItem('my-profile:scroll')

  tabDataLoading.value = true
  try {
    const [arts, subs, sbrs] = await Promise.all([
      getMyArticles(),
      getMySubscriptions(),
      getMySubscribers()
    ])
    articles.value = arts.filter((a) => !a.draft)
    subscriptions.value = subs
    followers.value = sbrs
  } catch {}
  finally { tabDataLoading.value = false }

  userStore.fetchMyProfile()

  if (savedScroll) {
    sessionStorage.removeItem('my-profile:scroll')
    await nextTick()
    window.scrollTo({ top: parseInt(savedScroll), behavior: 'instant' })
  }
})

const profile = computed(() => userStore.myProfile)

function startEditing() {
  if (!profile.value) return
  form.username = profile.value.username ?? ''
  form.avatar = profile.value.avatar ?? ''
  form.profile = profile.value.profile ?? ''
  form.cardDetails = profile.value.cardDetails ?? ''
  saveError.value = null
  saveSuccess.value = false
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
  saveError.value = null
}

async function handleSave() {
  if (!form.username.trim()) {
    saveError.value = 'Имя обязательно'
    return
  }
  saveLoading.value = true
  saveError.value = null
  saveSuccess.value = false
  try {
    await userStore.updateMyProfile({
      username: form.username.trim(),
      avatar: form.avatar.trim() || null,
      profile: form.profile.trim() || null,
      cardDetails: form.cardDetails.trim() || null
    })
    isEditing.value = false
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch {
    saveError.value = 'Не удалось сохранить изменения'
  } finally {
    saveLoading.value = false
  }
}

function setTab(tab: Tab) {
  activeTab.value = tab
  searchQuery.value = ''
  currentPage.value = 1
}

function onLikeUpdate(articleId: number, likes: number) {
  const art = articles.value.find((a) => a.articleId === articleId)
  if (art) art.likes = likes
}

const initials = computed(() => {
  const name = profile.value?.username || profile.value?.login || '?'
  return name.charAt(0).toUpperCase()
})

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}

function roleLabel(_role: string) {
  return 'Пользователь'
}
</script>

<template>
  <div class="max-w-3xl mx-auto px-6 py-10">

    <!-- Загрузка профиля -->
    <div v-if="userStore.loading && !profile" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Ошибка загрузки -->
    <div v-else-if="userStore.error" class="text-center py-20 text-red-500">
      {{ userStore.error }}
    </div>

    <!-- Профиль -->
    <div v-else-if="profile">

      <!-- Шапка профиля -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
        <div class="flex items-start gap-5">

          <!-- Аватар -->
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

          <!-- Основная инфо -->
          <div class="flex-1 min-w-0">
            <h1 class="text-xl font-bold text-gray-900 leading-tight">
              {{ profile.username || 'Без имени' }}
            </h1>
            <p class="text-sm text-gray-400 mt-0.5">{{ profile.login }}</p>

            <!-- Counts -->
            <div class="flex items-center gap-5 mt-3">
              <div class="text-sm text-gray-500">
                <span class="font-semibold text-gray-800">{{ subscriptions.length }}</span> подписок
              </div>
              <div class="text-sm text-gray-500">
                <span class="font-semibold text-gray-800">{{ followers.length }}</span> подписчиков
              </div>
            </div>

            <div class="flex flex-wrap gap-2 mt-2">
              <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full">
                {{ roleLabel(profile.userRole) }}
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

          <!-- Кнопка редактирования (вид) -->
          <button
            v-if="!isEditing"
            @click="startEditing"
            class="flex-shrink-0 px-4 py-1.5 text-sm font-medium border border-gray-300
                   rounded-lg text-gray-700 hover:border-blue-400 hover:text-blue-600 transition-colors"
          >
            Редактировать
          </button>
        </div>

        <!-- Описание профиля (вид) -->
        <div v-if="!isEditing && (profile.profile || profile.cardDetails)" class="mt-4 pt-4 border-t border-gray-100">
          <p v-if="profile.profile" class="text-sm text-gray-600 leading-relaxed">
            {{ profile.profile }}
          </p>
          <p v-if="profile.cardDetails" class="text-xs text-gray-400 mt-2">
            {{ profile.cardDetails }}
          </p>
        </div>

        <!-- Форма редактирования -->
        <form v-if="isEditing" @submit.prevent="handleSave" class="mt-4 pt-4 border-t border-gray-100 flex flex-col gap-4">

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">

            <!-- Имя -->
            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-gray-600">
                Имя <span class="text-red-400">*</span>
              </label>
              <input
                v-model="form.username"
                type="text"
                placeholder="Иван Иванов"
                :disabled="saveLoading"
                class="input-field"
              />
            </div>

            <!-- URL аватара -->
            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-gray-600">URL аватара</label>
              <input
                v-model="form.avatar"
                type="url"
                placeholder="https://example.com/avatar.jpg"
                :disabled="saveLoading"
                class="input-field"
              />
            </div>

          </div>

          <!-- Описание / bio -->
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-gray-600">О себе</label>
            <textarea
              v-model="form.profile"
              rows="3"
              placeholder="Расскажите о себе..."
              :disabled="saveLoading"
              class="input-field resize-none"
            />
          </div>

          <!-- Доп. данные -->
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-gray-600">Дополнительно</label>
            <input
              v-model="form.cardDetails"
              type="text"
              placeholder="Место работы, специализация..."
              :disabled="saveLoading"
              class="input-field"
            />
          </div>

          <!-- Ошибка сохранения -->
          <p v-if="saveError" class="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg">
            {{ saveError }}
          </p>

          <!-- Кнопки -->
          <div class="flex gap-2 justify-end">
            <button
              type="button"
              @click="cancelEditing"
              :disabled="saveLoading"
              class="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg
                     hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              :disabled="saveLoading"
              class="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg
                     hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              <span v-if="saveLoading">Сохранение...</span>
              <span v-else>Сохранить</span>
            </button>
          </div>

        </form>
      </div>

      <!-- Тема оформления -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-4 mb-6 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               :class="themeStore.isDark ? 'bg-slate-700' : 'bg-gray-100'">
            <svg v-if="!themeStore.isDark" class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V3a1 1 0 0 1 1-1zm0 15a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm7.071-2.929a1 1 0 0 1 0 1.414l-.707.707a1 1 0 1 1-1.414-1.414l.707-.707a1 1 0 0 1 1.414 0zM21 11h1a1 1 0 1 1 0 2h-1a1 1 0 1 1 0-2zm-2.929 7.071a1 1 0 0 1-1.414 0l-.707-.707a1 1 0 0 1 1.414-1.414l.707.707a1 1 0 0 1 0 1.414zM13 20v1a1 1 0 1 1-2 0v-1a1 1 0 1 1 2 0zm-7.071-2.929a1 1 0 0 1 0-1.414l.707-.707A1 1 0 0 1 8.05 16.364l-.707.707a1 1 0 0 1-1.414 0zM3 11h1a1 1 0 1 1 0 2H3a1 1 0 1 1 0-2zm3.636-4.95a1 1 0 0 1 1.414 0l.707.707A1 1 0 0 1 7.343 8.17l-.707-.707a1 1 0 0 1 0-1.414z"/>
            </svg>
            <svg v-else class="w-5 h-5 text-blue-300" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-800">Тема оформления</p>
            <p class="text-xs text-gray-400 mt-0.5">{{ themeStore.isDark ? 'Тёмная' : 'Светлая' }}</p>
          </div>
        </div>

        <!-- Toggle switch -->
        <button
          @click="themeStore.toggle()"
          class="relative inline-flex w-12 h-6 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none"
          :class="themeStore.isDark ? 'bg-blue-600' : 'bg-gray-200'"
          :aria-label="themeStore.isDark ? 'Переключить на светлую тему' : 'Переключить на тёмную тему'"
        >
          <span
            class="pointer-events-none inline-block w-5 h-5 rounded-full bg-white shadow transform transition-transform duration-200"
            :class="themeStore.isDark ? 'translate-x-6' : 'translate-x-0'"
          />
        </button>
      </div>

      <!-- Tab switcher -->
      <div class="flex border-b border-gray-200 mb-6">
        <button
          @click="setTab('articles')"
          class="px-5 py-3 text-base font-medium border-b-2 transition-colors -mb-px"
          :class="activeTab === 'articles'
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Мои статьи
          <span class="ml-1 text-sm" :class="activeTab === 'articles' ? 'text-blue-400' : 'text-gray-400'">
            {{ articles.length }}
          </span>
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
        <button
          @click="setTab('followers')"
          class="px-5 py-3 text-base font-medium border-b-2 transition-colors -mb-px"
          :class="activeTab === 'followers'
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Фолловеры
          <span class="ml-1 text-sm" :class="activeTab === 'followers' ? 'text-blue-400' : 'text-gray-400'">
            {{ followers.length }}
          </span>
        </button>
      </div>

      <!-- Search bar (always shown once profile loaded) -->
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

      <!-- Loading tab data -->
      <div v-if="tabDataLoading" class="flex justify-center py-10">
        <div class="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
      </div>

      <template v-else>

        <!-- Мои статьи -->
        <template v-if="activeTab === 'articles'">
          <SortBar v-model="sortKey" class="mb-5" />
          <p v-if="filteredArticles.length === 0" class="text-gray-400 py-10 text-center">
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

            <!-- Pagination -->
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

        <!-- Подписки -->
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

        <!-- Фолловеры -->
        <template v-if="activeTab === 'followers'">
          <p v-if="filteredFollowers.length === 0" class="text-gray-400 py-10 text-center">
            {{ followers.length === 0 ? 'Нет подписчиков' : 'Ничего не найдено' }}
          </p>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <UserCard
              v-for="user in filteredFollowers"
              :key="user.userId"
              :profile="user"
            />
          </div>
        </template>

      </template>
    </div>

    <!-- Уведомление об успехе -->
    <Transition name="fade">
      <div
        v-if="saveSuccess"
        class="fixed bottom-6 right-6 bg-green-600 text-white text-sm px-4 py-2 rounded-lg shadow-lg"
      >
        Профиль обновлён
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.input-field {
  @apply w-full px-3 py-2 rounded-lg border border-gray-300 text-sm outline-none
         focus:border-blue-500 focus:ring-2 focus:ring-blue-100
         disabled:bg-gray-50 disabled:text-gray-400 transition bg-white;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
