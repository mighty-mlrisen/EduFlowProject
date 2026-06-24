<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import katex from 'katex'
import { getArticleById, getArticleSummary } from '@/api/article.api'
import type { ArticleResponse } from '@/types/article.types'
import SaveButton from '@/components/article/SaveButton.vue'
import LikeButton from '@/components/article/LikeButton.vue'
import CommentSection from '@/components/article/CommentSection.vue'
import SubscribeButton from '@/components/user/SubscribeButton.vue'

const props = defineProps<{ articleId: number }>()

const article = ref<ArticleResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const summaryOpen = ref(false)
const summaryText = ref<string | null>(null)
const summaryLoading = ref(false)
const summaryError = ref<string | null>(null)

const renderer = new marked.Renderer()
const _link = renderer.link.bind(renderer)
renderer.link = (token) => {
  const html = _link(token)
  return token.href?.startsWith('http')
    ? html.replace('<a ', '<a target="_blank" rel="noopener noreferrer" ')
    : html
}
marked.use({ renderer, breaks: true, gfm: true })

onMounted(async () => {
  try {
    article.value = await getArticleById(props.articleId)
  } catch {
    error.value = 'Статья не найдена'
  } finally {
    loading.value = false
  }
})

const contentRef = ref<HTMLElement | null>(null)

function preprocessMath(text: string): string {
  // Block math ($$...$$) first to avoid conflicts with inline
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
    try {
      return `<div class="math-block">${katex.renderToString(formula.trim(), { throwOnError: false, displayMode: true, output: 'html' })}</div>`
    } catch {
      return `<code>$$${formula}$$</code>`
    }
  })
  // Inline math ($...$)
  text = text.replace(/\$([^$\n]+?)\$/g, (_, formula) => {
    try {
      return `<span class="math-inline">${katex.renderToString(formula.trim(), { throwOnError: false, displayMode: false, output: 'html' })}</span>`
    } catch {
      return `<code>$${formula}$</code>`
    }
  })
  return text
}

const renderedContent = computed(() => {
  if (!article.value?.text) return ''
  const processed = preprocessMath(article.value.text)
  const html = marked.parse(processed) as string
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ['img', 'span'],
    ADD_ATTR: ['target', 'rel', 'src', 'alt', 'class', 'style', 'colspan', 'rowspan',
               'aria-hidden', 'data-type', 'data-formula'],
  })
})

// Fallback: render data-type math nodes from older articles saved before the $...$ serializer
function applyFallbackKatex() {
  if (!contentRef.value) return
  contentRef.value.querySelectorAll<HTMLElement>('[data-type="math-inline"]').forEach(el => {
    const formula = el.getAttribute('data-formula') || ''
    el.innerHTML = ''
    try { katex.render(formula, el, { throwOnError: false, displayMode: false, output: 'html' }) } catch {}
  })
  contentRef.value.querySelectorAll<HTMLElement>('[data-type="math-block"]').forEach(el => {
    const formula = el.getAttribute('data-formula') || ''
    el.innerHTML = ''
    try { katex.render(formula, el, { throwOnError: false, displayMode: true, output: 'html' }) } catch {}
  })
}

watch(renderedContent, async () => {
  await nextTick()
  applyFallbackKatex()
})

const isOwnArticle = computed(() =>
  article.value ? article.value.currentUserId === article.value.users?.userId : false
)

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}

function scrollToComments() {
  document.getElementById('comments')?.scrollIntoView({ behavior: 'smooth' })
}

async function toggleSummary() {
  summaryOpen.value = !summaryOpen.value

  if (summaryOpen.value && summaryText.value === null && !summaryLoading.value) {
    summaryLoading.value = true
    summaryError.value = null
    try {
      summaryText.value = await getArticleSummary(props.articleId)
    } catch {
      summaryError.value = 'Не удалось получить краткое содержание'
    } finally {
      summaryLoading.value = false
    }
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto px-6 py-10">

    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="error" class="text-center py-20 text-red-500">{{ error }}</div>

    <article v-else-if="article">

      <!-- Cover -->
      <img
        v-if="article.image"
        :src="article.image"
        :alt="article.title"
        class="w-full max-h-80 object-cover rounded-2xl mb-8"
      />

      <!-- Title + actions -->
      <div class="flex items-start gap-3 mb-5">
        <h1 class="text-4xl font-bold text-gray-900 leading-tight flex-1">
          {{ article.title }}
        </h1>
        <div class="flex items-center gap-1 flex-shrink-0 mt-2">
          <button
            @click="scrollToComments"
            class="flex items-center justify-center w-12 h-12 rounded-full text-gray-400 hover:text-blue-500 hover:bg-gray-100 transition-colors"
            title="Перейти к комментариям"
          >
            <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
          </button>
          <SaveButton :article-id="article.articleId" :saved="article.statusSave" :large="true" />
        </div>
      </div>

      <!-- Meta: author + date + category + subscribe -->
      <div class="flex flex-wrap items-center gap-3 mb-8 pb-8 border-b border-gray-100">
        <RouterLink :to="`/profile/${article.users?.userId}`" class="flex items-center gap-2">
          <img
            v-if="article.users?.avatar"
            :src="article.users.avatar"
            :alt="article.users.username"
            class="w-8 h-8 rounded-full object-cover"
          />
          <div
            v-else
            class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold"
          >
            {{ article.users?.username?.charAt(0)?.toUpperCase() ?? '?' }}
          </div>
          <span class="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">
            {{ article.users?.username }}
          </span>
        </RouterLink>

        <span class="text-gray-200">·</span>
        <span class="text-sm text-gray-400">{{ formatDate(article.createdAt) }}</span>

        <span
          v-if="article.category"
          class="px-2.5 py-0.5 text-xs font-medium bg-blue-50 text-blue-600 rounded-full"
        >
          {{ article.category.name }}
        </span>

        <SubscribeButton
          v-if="!isOwnArticle && article.users"
          :user-id="article.users.userId"
          :subscribed="article.users.statusSubscribtion"
          class="ml-auto"
        />
      </div>

      <!-- Summary toggle -->
      <div class="mb-8">
        <button
          @click="toggleSummary"
          class="w-full flex items-center justify-between px-5 py-3.5 rounded-xl border transition-all"
          :class="summaryOpen
            ? 'bg-violet-50 border-violet-200'
            : 'bg-gray-50 border-gray-200 hover:bg-violet-50 hover:border-violet-200'"
        >
          <div class="flex items-center gap-2.5">
            <svg class="w-4 h-4 text-violet-500 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l2.09 6.26L20 10l-5.91 1.74L12 18l-2.09-6.26L4 10l5.91-1.74L12 2z"/>
              <path d="M5 3l.9 2.7L8 6.5l-2.1.8L5 10l-.9-2.7L2 6.5l2.1-.8L5 3z" opacity=".6"/>
            </svg>
            <span class="text-sm font-medium text-violet-700">Краткое содержание</span>
          </div>
          <svg
            class="w-4 h-4 text-violet-400 transition-transform duration-300"
            :class="summaryOpen ? 'rotate-180' : ''"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
        </button>

        <Transition name="summary-slide">
          <div v-if="summaryOpen" class="mt-1 px-5 py-4 rounded-xl bg-violet-50/60 border border-violet-100">

              <div v-if="summaryLoading" class="flex items-center gap-3 text-violet-500 text-sm py-1">
                <div class="w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                Генерируем краткое содержание...
              </div>

              <p v-else-if="summaryError" class="text-sm text-red-500">{{ summaryError }}</p>

              <p v-else class="text-sm text-gray-700 leading-relaxed text-justify">{{ summaryText }}</p>

          </div>
        </Transition>
      </div>

      <!-- Description -->
      <p v-if="article.description" class="text-lg text-gray-500 mb-8 leading-relaxed">
        {{ article.description }}
      </p>

      <!-- Content -->
      <div ref="contentRef" class="article-content prose prose-lg prose-gray max-w-none" v-html="renderedContent" />

      <!-- Likes -->
      <div class="mt-10 pt-6 border-t border-gray-100">
        <LikeButton
          :article-id="article.articleId"
          :liked="article.statusLike"
          :count="article.likes"
          :large="true"
        />
      </div>

      <!-- Comments -->
      <CommentSection :article-id="article.articleId" />

    </article>
  </div>
</template>

<style scoped>
.summary-slide-enter-active,
.summary-slide-leave-active {
  transition: max-height 0.35s ease, opacity 0.3s ease;
  max-height: 600px;
  overflow: hidden;
}
.summary-slide-enter-from,
.summary-slide-leave-to {
  max-height: 0;
  opacity: 0;
}

:deep(.article-content pre) {
  background: #282c34 !important;
  color: #abb2bf !important;
  border-radius: 0.75rem;
  padding: 1.25rem 1.5rem;
  overflow-x: auto;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.875rem;
  line-height: 1.7;
}
:deep(.article-content pre code) {
  color: #abb2bf !important;
  background: transparent !important;
  padding: 0 !important;
  border-radius: 0 !important;
  font-size: inherit !important;
}
:deep(.article-content :not(pre) > code) {
  color: #e06c75 !important;
  background: #f3f4f6 !important;
  padding: 0.15em 0.4em !important;
  border-radius: 0.25rem !important;
  font-size: 0.875em !important;
}
:deep(.article-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1.5rem 0;
  font-size: 0.95rem;
}
:deep(.article-content th) {
  background: #f9fafb;
  font-weight: 600;
  border: 1px solid #e5e7eb;
  padding: 0.6rem 1rem;
  text-align: left;
}
:deep(.article-content td) {
  border: 1px solid #e5e7eb;
  padding: 0.6rem 1rem;
}
:deep(.article-content tr:nth-child(even) td) {
  background: #fafafa;
}
:deep(.article-content .math-block) {
  overflow-x: auto;
  text-align: center;
  margin: 1.5rem 0;
  padding: 0.5rem 0;
}
:deep(.article-content .math-inline) {
  display: inline;
}
:deep(.article-content .katex) {
  font-size: 1.1em;
}
</style>
