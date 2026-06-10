<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { getArticleById } from '@/api/article.api'
import type { ArticleResponse } from '@/types/article.types'
import SaveButton from '@/components/article/SaveButton.vue'
import LikeButton from '@/components/article/LikeButton.vue'
import CommentSection from '@/components/article/CommentSection.vue'
import SubscribeButton from '@/components/user/SubscribeButton.vue'

const props = defineProps<{ articleId: number }>()

const article = ref<ArticleResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

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

const renderedContent = computed(() => {
  if (!article.value?.text) return ''
  const html = marked.parse(article.value.text) as string
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ['img', 'span'],
    ADD_ATTR: ['target', 'rel', 'src', 'alt', 'class', 'style', 'colspan', 'rowspan']
  })
})

// Own article — hide subscribe button
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
          <!-- Scroll to comments -->
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

      <!-- Description -->
      <p v-if="article.description" class="text-lg text-gray-500 mb-8 leading-relaxed">
        {{ article.description }}
      </p>

      <!-- Content -->
      <div class="article-content prose prose-lg prose-gray max-w-none" v-html="renderedContent" />

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
</style>
