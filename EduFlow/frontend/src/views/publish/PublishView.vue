<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getArticleById, getMyDrafts, getMyArticles } from '@/api/article.api'
import type { ArticleResponse } from '@/types/article.types'
import ArticleEditor from '@/components/editor/ArticleEditor.vue'
import ArticleCard from '@/components/article/ArticleCard.vue'
import SortBar from '@/components/article/SortBar.vue'
import { useArticleSort } from '@/composables/useArticleSort'

const route = useRoute()
const router = useRouter()

type Tab = 'editor' | 'drafts' | 'articles'

const TABS: { id: Tab; label: string }[] = [
  { id: 'editor', label: 'Опубликовать статью' },
  { id: 'drafts', label: 'Черновики' },
  { id: 'articles', label: 'Мои статьи' }
]

const PER_PAGE = 10

const activeTab = computed<Tab>(() => (route.query.tab as Tab) || 'editor')
const editId = computed(() => route.query.id ? Number(route.query.id) : null)

const editingArticle = ref<ArticleResponse | null>(null)
const loadingEdit = ref(false)

const drafts = ref<ArticleResponse[]>([])
const myArticles = ref<ArticleResponse[]>([])
const loadingList = ref(false)
const listError = ref<string | null>(null)

const { sortKey: articlesSortKey, sorted: sortedMyArticles } = useArticleSort(myArticles)

// Pagination — drafts
const draftsPage = ref(1)
const draftsTotalPages = computed(() => Math.max(1, Math.ceil(drafts.value.length / PER_PAGE)))
const paginatedDrafts = computed(() => {
  const start = (draftsPage.value - 1) * PER_PAGE
  return drafts.value.slice(start, start + PER_PAGE)
})

// Pagination — my articles
const articlesPage = ref(1)
const articlesTotalPages = computed(() => Math.max(1, Math.ceil(sortedMyArticles.value.length / PER_PAGE)))
const paginatedMyArticles = computed(() => {
  const start = (articlesPage.value - 1) * PER_PAGE
  return sortedMyArticles.value.slice(start, start + PER_PAGE)
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

watch([articlesSortKey], () => { articlesPage.value = 1 })
watch(activeTab, () => { draftsPage.value = 1; articlesPage.value = 1 })
watch(draftsPage, () => { window.scrollTo({ top: 0, behavior: 'smooth' }) })
watch(articlesPage, () => { window.scrollTo({ top: 0, behavior: 'smooth' }) })

// Load article when editing
watch(editId, async (id) => {
  if (id) {
    loadingEdit.value = true
    editingArticle.value = null
    try {
      editingArticle.value = await getArticleById(id)
    } catch {
      editingArticle.value = null
    } finally {
      loadingEdit.value = false
    }
  } else {
    editingArticle.value = null
  }
}, { immediate: true })

// Load lists on tab change
watch(activeTab, (tab) => {
  if (tab === 'drafts') loadDrafts()
  else if (tab === 'articles') loadPublished()
}, { immediate: true })

async function loadDrafts() {
  loadingList.value = true
  listError.value = null
  try {
    drafts.value = await getMyDrafts()
  } catch {
    listError.value = 'Не удалось загрузить черновики'
  } finally {
    loadingList.value = false
  }
}

async function loadPublished() {
  loadingList.value = true
  listError.value = null
  try {
    const all = await getMyArticles()
    myArticles.value = all.filter((a) => !a.draft)
  } catch {
    listError.value = 'Не удалось загрузить статьи'
  } finally {
    loadingList.value = false
  }
}

function setTab(tab: Tab) {
  router.push({ name: 'publish', query: { tab } })
}

function editArticle(id: number) {
  router.push({ name: 'publish', query: { tab: 'editor', id: String(id) } })
}

function onDraftDeleted(id: number) {
  drafts.value = drafts.value.filter((a) => a.articleId !== id)
  if (draftsPage.value > draftsTotalPages.value) draftsPage.value = draftsTotalPages.value
}

function onArticleDeleted(id: number) {
  myArticles.value = myArticles.value.filter((a) => a.articleId !== id)
  if (articlesPage.value > articlesTotalPages.value) articlesPage.value = articlesTotalPages.value
}

const editorTabLabel = computed(() =>
  editId.value ? 'Редактировать' : 'Опубликовать статью'
)
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">

    <!-- Tab switcher -->
    <div class="flex gap-1 bg-gray-100 rounded-xl p-1 mb-8 w-fit">
      <button
        v-for="tab in TABS"
        :key="tab.id"
        @click="setTab(tab.id)"
        class="px-5 py-2 text-sm font-medium rounded-lg transition-all"
        :class="activeTab === tab.id
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-500 hover:text-gray-700'"
      >
        {{ tab.id === 'editor' ? editorTabLabel : tab.label }}
      </button>
    </div>

    <!-- ── Editor tab ── -->
    <template v-if="activeTab === 'editor'">
      <div v-if="loadingEdit" class="flex justify-center py-16">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
      <ArticleEditor
        v-else
        :initial-data="editingArticle"
        :article-id="editId"
      />
    </template>

    <!-- ── Drafts tab ── -->
    <template v-else-if="activeTab === 'drafts'">
      <div v-if="loadingList" class="flex justify-center py-16">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
      <p v-else-if="listError" class="text-red-500 text-sm">{{ listError }}</p>
      <div v-else-if="drafts.length === 0" class="text-center py-16">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <p class="text-sm font-medium text-gray-400">Черновиков пока нет</p>
        <button @click="setTab('editor')" class="mt-3 text-sm text-blue-600 hover:underline">
          Написать статью
        </button>
      </div>
      <div v-else>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          <ArticleCard
            v-for="article in paginatedDrafts"
            :key="article.articleId"
            :article="article"
            :is-draft="true"
            @edit="editArticle"
            @delete="onDraftDeleted"
          />
        </div>
        <!-- Drafts pagination -->
        <div v-if="draftsTotalPages > 1" class="flex items-center justify-center gap-1 mt-4">
          <button
            :disabled="draftsPage === 1"
            @click="draftsPage--"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >←</button>
          <template v-for="p in smartPages(draftsPage, draftsTotalPages)" :key="String(p)">
            <span v-if="p === '…'" class="px-2 text-gray-400 text-sm select-none">…</span>
            <button
              v-else
              @click="draftsPage = p as number"
              class="px-3 py-1.5 text-sm rounded-lg border transition-colors"
              :class="draftsPage === p
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
            >{{ p }}</button>
          </template>
          <button
            :disabled="draftsPage === draftsTotalPages"
            @click="draftsPage++"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >→</button>
        </div>
      </div>
    </template>

    <!-- ── My articles tab ── -->
    <template v-else>
      <div v-if="loadingList" class="flex justify-center py-16">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
      <p v-else-if="listError" class="text-red-500 text-sm">{{ listError }}</p>
      <div v-else-if="myArticles.length === 0" class="text-center py-16">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
        </svg>
        <p class="text-sm font-medium text-gray-400">Опубликованных статей пока нет</p>
        <button @click="setTab('editor')" class="mt-3 text-sm text-blue-600 hover:underline">
          Написать первую статью
        </button>
      </div>
      <div v-else>
        <SortBar v-model="articlesSortKey" class="mb-5" />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          <ArticleCard
            v-for="article in paginatedMyArticles"
            :key="article.articleId"
            :article="article"
            :show-edit="true"
            @edit="editArticle"
            @delete="onArticleDeleted"
          />
        </div>
        <!-- Articles pagination -->
        <div v-if="articlesTotalPages > 1" class="flex items-center justify-center gap-1 mt-4">
          <button
            :disabled="articlesPage === 1"
            @click="articlesPage--"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >←</button>
          <template v-for="p in smartPages(articlesPage, articlesTotalPages)" :key="String(p)">
            <span v-if="p === '…'" class="px-2 text-gray-400 text-sm select-none">…</span>
            <button
              v-else
              @click="articlesPage = p as number"
              class="px-3 py-1.5 text-sm rounded-lg border transition-colors"
              :class="articlesPage === p
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
            >{{ p }}</button>
          </template>
          <button
            :disabled="articlesPage === articlesTotalPages"
            @click="articlesPage++"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >→</button>
        </div>
      </div>
    </template>

  </div>
</template>
