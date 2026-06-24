<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth.store'
import { useRouter, useRoute } from 'vue-router'
import { getCategories, searchArticles } from '@/api/article.api'
import { searchUsers } from '@/api/user.api'
import type { CategoryEntity, ArticleResponse } from '@/types/article.types'
import type { ProfileResponse } from '@/types/user.types'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// ── Categories ──────────────────────────────────────────────
const catOpen = ref(false)
const categories = ref<CategoryEntity[]>([])
const catLoaded = ref(false)
const catMenuRef = ref<HTMLElement | null>(null)

async function toggleCatMenu() {
  catOpen.value = !catOpen.value
  if (catOpen.value && !catLoaded.value) {
    try {
      categories.value = await getCategories()
      catLoaded.value = true
    } catch {}
  }
}
function closeCatMenu() { catOpen.value = false }
function onCatDocClick(e: MouseEvent) {
  if (!catMenuRef.value?.contains(e.target as Node)) closeCatMenu()
}
watch(catOpen, (val) => {
  if (val) document.addEventListener('click', onCatDocClick, true)
  else document.removeEventListener('click', onCatDocClick, true)
})

// ── Search ───────────────────────────────────────────────────
const searchQuery = ref('')
const searchOpen = ref(false)
const searchLoading = ref(false)
const foundArticles = ref<ArticleResponse[]>([])
const foundUsers = ref<ProfileResponse[]>([])
const searchRef = ref<HTMLElement | null>(null)
let searchTimer: ReturnType<typeof setTimeout> | null = null

const hasResults = computed(
  () => foundArticles.value.length > 0 || foundUsers.value.length > 0
)

watch(searchQuery, (q) => {
  if (searchTimer) clearTimeout(searchTimer)
  const trimmed = q.trim()
  if (trimmed.length < 2) {
    searchOpen.value = false
    foundArticles.value = []
    foundUsers.value = []
    searchLoading.value = false
    return
  }
  searchLoading.value = true
  searchOpen.value = true
  searchTimer = setTimeout(async () => {
    try {
      const [arts, users] = await Promise.all([
        searchArticles(trimmed),
        searchUsers(trimmed)
      ])
      foundArticles.value = arts.filter((a) => !a.draft).slice(0, 5)
      foundUsers.value = users.slice(0, 5)
    } catch {
      foundArticles.value = []
      foundUsers.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
})

function closeSearch() {
  searchOpen.value = false
  searchQuery.value = ''
  foundArticles.value = []
  foundUsers.value = []
}

function onSearchDocClick(e: MouseEvent) {
  if (!searchRef.value?.contains(e.target as Node)) searchOpen.value = false
}
watch(searchOpen, (val) => {
  if (val) document.addEventListener('click', onSearchDocClick, true)
  else document.removeEventListener('click', onSearchDocClick, true)
})

// ── Shared ───────────────────────────────────────────────────
watch(() => route.path, () => { closeCatMenu(); closeSearch() })

onUnmounted(() => {
  document.removeEventListener('click', onCatDocClick, true)
  document.removeEventListener('click', onSearchDocClick, true)
  if (searchTimer) clearTimeout(searchTimer)
})

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}

function goHome() {
  sessionStorage.removeItem('feed:scroll')
  sessionStorage.removeItem('feed:page')
}

function clearScrollFor(routeName: string) {
  const keyMap: Record<string, string[]> = {
    'subscription-feed': ['subfeed:scroll', 'subfeed:page'],
    'publish': ['publish:scroll'],
    'saved': ['saved:scroll', 'saved:page'],
    'my-profile': ['my-profile:scroll'],
  }
  ;(keyMap[routeName] ?? []).forEach(k => sessionStorage.removeItem(k))
}

function navToCategory(id: number) {
  sessionStorage.removeItem(`category-${id}:scroll`)
  sessionStorage.removeItem(`category-${id}:page`)
  closeCatMenu()
}
</script>

<template>
  <header class="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-sm">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center gap-4">

      <!-- Логотип -->
      <RouterLink
        to="/"
        class="text-2xl font-bold text-blue-600 hover:text-blue-700 transition-colors tracking-tight flex-shrink-0"
        @click="goHome"
      >
        EduFlow
      </RouterLink>

      <!-- Центральная навигация + поиск (авторизован) -->
      <template v-if="auth.isAuthenticated">

        <!-- Навигация -->
        <nav class="flex items-center gap-1 flex-shrink-0">

          <!-- Категории -->
          <div ref="catMenuRef" class="relative">
            <button
              @click="toggleCatMenu"
              class="px-3 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-1"
              :class="$route.name === 'category'
                ? 'bg-blue-50 text-blue-600'
                : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'"
            >
              Категории
              <svg
                class="w-3.5 h-3.5 transition-transform duration-200"
                :class="catOpen ? 'rotate-180' : ''"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>

            <Transition
              enter-active-class="transition duration-150 ease-out"
              enter-from-class="opacity-0 -translate-y-1 scale-95"
              enter-to-class="opacity-100 translate-y-0 scale-100"
              leave-active-class="transition duration-100 ease-in"
              leave-from-class="opacity-100 translate-y-0 scale-100"
              leave-to-class="opacity-0 -translate-y-1 scale-95"
            >
              <div
                v-if="catOpen"
                class="absolute left-0 top-full mt-2 bg-white rounded-xl border border-gray-100 shadow-xl py-3 px-3 z-40 origin-top-left"
                style="width: 580px"
              >
                <div v-if="!catLoaded" class="flex items-center gap-2 px-2 py-2 text-sm text-gray-400">
                  <div class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                  Загрузка...
                </div>
                <template v-else>
                  <p v-if="categories.length === 0" class="px-2 py-2 text-sm text-gray-400">Нет категорий</p>
                  <div v-else class="grid grid-cols-3 gap-0.5">
                    <RouterLink
                      v-for="cat in categories"
                      :key="cat.id"
                      :to="`/category/${cat.id}`"
                      class="px-3 py-2 text-sm text-gray-700 rounded-lg hover:bg-blue-50 hover:text-blue-600 transition-colors break-words leading-snug"
                      :class="Number($route.params.id) === cat.id ? 'bg-blue-50 text-blue-600 font-medium' : ''"
                      @click="navToCategory(cat.id)"
                    >
                      {{ cat.name }}
                    </RouterLink>
                  </div>
                </template>
              </div>
            </Transition>
          </div>

          <!-- Моя лента -->
          <RouterLink
            :to="{ name: 'subscription-feed' }"
            class="px-3 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'subscription-feed'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'"
            @click="clearScrollFor('subscription-feed')"
          >
            Моя лента
          </RouterLink>

          <!-- Публикации -->
          <RouterLink
            :to="{ name: 'publish' }"
            class="px-3 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'publish'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'"
            @click="clearScrollFor('publish')"
          >
            Публикации
          </RouterLink>

          <!-- Избранное -->
          <RouterLink
            :to="{ name: 'saved' }"
            class="px-3 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'saved'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'"
            @click="clearScrollFor('saved')"
          >
            Избранное
          </RouterLink>

          <!-- Статистика -->
          <RouterLink
            :to="{ name: 'stats' }"
            class="px-3 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'stats'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'"
          >
            Статистика
          </RouterLink>
        </nav>

        <!-- Поиск -->
        <div ref="searchRef" class="relative flex-1">
          <div class="flex items-center bg-gray-100 rounded-full px-3 py-1.5 gap-2 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-400 transition-all">
            <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Статьи, авторы..."
              class="bg-transparent text-base text-gray-800 placeholder-gray-400 outline-none w-full"
              @focus="searchOpen = searchQuery.trim().length >= 2"
            />
            <button
              v-if="searchQuery"
              @click="closeSearch"
              class="text-gray-400 hover:text-gray-600 flex-shrink-0"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Results dropdown -->
          <Transition
            enter-active-class="transition duration-150 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <div
              v-if="searchOpen"
              class="absolute right-0 top-full mt-2 bg-white rounded-xl border border-gray-100 shadow-xl z-40 overflow-hidden"
              style="width: 640px"
            >
              <!-- Loading -->
              <div v-if="searchLoading" class="flex items-center gap-2 px-5 py-4 text-base text-gray-400">
                <div class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                Поиск...
              </div>

              <!-- No results -->
              <div v-else-if="!hasResults" class="px-5 py-4 text-base text-gray-400">
                Ничего не найдено
              </div>

              <template v-else>
                <!-- Articles -->
                <div v-if="foundArticles.length > 0">
                  <p class="px-5 pt-4 pb-1.5 text-sm font-semibold text-gray-400 uppercase tracking-wide">Статьи</p>
                  <RouterLink
                    v-for="art in foundArticles"
                    :key="art.articleId"
                    :to="`/article/${art.articleId}`"
                    class="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 transition-colors"
                    @click="closeSearch"
                  >
                    <img
                      v-if="art.image"
                      :src="art.image"
                      class="w-11 h-11 rounded-lg object-cover flex-shrink-0"
                    />
                    <div v-else class="w-11 h-11 rounded-lg bg-blue-50 flex-shrink-0" />
                    <div class="min-w-0 flex-1">
                      <p class="text-base text-gray-800 truncate">{{ art.title }}</p>
                      <p v-if="art.category" class="text-sm text-gray-400 mt-0.5">{{ art.category.name }}</p>
                    </div>
                  </RouterLink>
                </div>

                <!-- Users -->
                <div v-if="foundUsers.length > 0">
                  <p class="px-5 pt-4 pb-1.5 text-sm font-semibold text-gray-400 uppercase tracking-wide">Авторы</p>
                  <RouterLink
                    v-for="user in foundUsers"
                    :key="user.userId"
                    :to="`/profile/${user.userId}`"
                    class="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 transition-colors"
                    @click="closeSearch"
                  >
                    <img
                      v-if="user.avatar"
                      :src="user.avatar"
                      :alt="user.username"
                      class="w-11 h-11 rounded-full object-cover flex-shrink-0"
                    />
                    <div
                      v-else
                      class="w-11 h-11 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0"
                    >
                      {{ user.username?.charAt(0)?.toUpperCase() ?? '?' }}
                    </div>
                    <div class="min-w-0">
                      <p class="text-base text-gray-800">{{ user.username }}</p>
                      <p class="text-sm text-gray-400 mt-0.5">{{ user.login }}</p>
                    </div>
                  </RouterLink>
                </div>

                <div class="h-3" />
              </template>
            </div>
          </Transition>
        </div>

      </template>

      <!-- Spacer (гость) -->
      <div v-else class="flex-1" />

      <!-- Правая часть -->
      <nav class="flex items-center gap-2 flex-shrink-0 ml-auto">

        <template v-if="!auth.isAuthenticated">
          <RouterLink
            to="/login"
            class="px-4 py-2 text-base font-medium text-gray-700 hover:text-blue-600 transition-colors"
          >
            Войти
          </RouterLink>
          <RouterLink
            to="/register"
            class="px-5 py-2 text-base font-medium bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
          >
            Регистрация
          </RouterLink>
        </template>

        <template v-else>
          <RouterLink
            to="/profile"
            class="flex items-center gap-2 px-3 py-2 text-base font-medium text-gray-700 hover:text-blue-600 rounded-lg hover:bg-gray-100 transition-colors"
            @click="clearScrollFor('my-profile')"
          >
            <span class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold uppercase">
              {{ auth.user?.username?.charAt(0) ?? auth.user?.login?.charAt(0) ?? '?' }}
            </span>
            <span>Профиль</span>
          </RouterLink>
          <button
            @click="logout"
            class="px-3 py-2 text-base text-gray-500 hover:text-red-500 transition-colors"
          >
            Выйти
          </button>
        </template>

      </nav>
    </div>
  </header>
</template>
