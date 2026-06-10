<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getComments, createComment } from '@/api/article.api'
import type { CommentResponse } from '@/types/article.types'

const props = defineProps<{ articleId: number }>()

const comments = ref<CommentResponse[]>([])
const loading = ref(false)

// New top-level comment
const newText = ref('')
const newSubmitting = ref(false)
const newError = ref<string | null>(null)

// Reply state
const replyingToId = ref<number | null>(null)
const replyingToUsername = ref('')
const replyText = ref('')
const replySubmitting = ref(false)
const replyError = ref<string | null>(null)

// Collapsed threads (set of root commentIds) — populated after load
const collapsed = ref(new Set<number>())

onMounted(async () => {
  loading.value = true
  try {
    comments.value = await getComments(props.articleId)
    // collapse all reply threads by default
    comments.value.forEach((c) => {
      if (!c.parentCommentId) collapsed.value.add(c.commentId)
    })
  } catch { /* ignore */ }
  finally { loading.value = false }
})

// ── Pagination ────────────────────────────────────────────────
const PER_PAGE = 5
const currentPage = ref(1)

const topLevel = computed(() => comments.value.filter((c) => !c.parentCommentId))

const totalPages = computed(() => Math.max(1, Math.ceil(topLevel.value.length / PER_PAGE)))

const paginatedTopLevel = computed(() => {
  const start = (currentPage.value - 1) * PER_PAGE
  return topLevel.value.slice(start, start + PER_PAGE)
})

function smartPages(current: number, total: number): (number | '...')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | '...')[] = [1]
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i)
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
}

function goToPage(p: number) {
  currentPage.value = p
  cancelReply()
  document.getElementById('comments')?.scrollIntoView({ behavior: 'smooth' })
}

watch(totalPages, (newTotal) => {
  if (currentPage.value > newTotal) currentPage.value = newTotal
})

// ── Helpers ───────────────────────────────────────────────────

function getRootId(commentId: number): number {
  const c = comments.value.find((x) => x.commentId === commentId)
  if (!c || !c.parentCommentId) return commentId
  return getRootId(c.parentCommentId)
}

function getReplies(rootId: number) {
  return comments.value.filter(
    (c) => c.parentCommentId !== null && getRootId(c.commentId) === rootId
  )
}

// Which root thread owns the current reply form
const replyFormRoot = computed(() =>
  replyingToId.value !== null ? getRootId(replyingToId.value) : null
)

function toggleCollapse(rootId: number) {
  if (collapsed.value.has(rootId)) collapsed.value.delete(rootId)
  else collapsed.value.add(rootId)
}

function startReply(commentId: number, username: string) {
  if (replyingToId.value === commentId) {
    replyingToId.value = null
    replyingToUsername.value = ''
    replyText.value = ''
  } else {
    replyingToId.value = commentId
    replyingToUsername.value = username
    replyText.value = ''
    replyError.value = null
  }
}

function cancelReply() {
  replyingToId.value = null
  replyingToUsername.value = ''
  replyText.value = ''
  replyError.value = null
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

// ── Submit ────────────────────────────────────────────────────
async function submitNew() {
  const text = newText.value.trim()
  if (!text || newSubmitting.value) return
  newSubmitting.value = true
  newError.value = null
  try {
    comments.value.push(await createComment(props.articleId, { comment: text }))
    newText.value = ''
    currentPage.value = totalPages.value
  } catch {
    newError.value = 'Не удалось отправить комментарий'
  } finally {
    newSubmitting.value = false
  }
}

async function submitReply() {
  const text = replyText.value.trim()
  if (!text || replySubmitting.value || replyingToId.value === null) return
  replySubmitting.value = true
  replyError.value = null
  try {
    comments.value.push(
      await createComment(props.articleId, {
        comment: text,
        parentCommentId: replyingToId.value
      })
    )
    cancelReply()
  } catch {
    replyError.value = 'Не удалось отправить ответ'
  } finally {
    replySubmitting.value = false
  }
}
</script>

<template>
  <section id="comments" class="mt-14 pt-10 border-t border-gray-100">

    <h2 class="text-2xl font-bold text-gray-900 mb-8">
      Комментарии
      <span v-if="comments.length" class="text-lg font-normal text-gray-400 ml-1">({{ comments.length }})</span>
    </h2>

    <!-- New comment form -->
    <div class="mb-10">
      <textarea
        v-model="newText"
        placeholder="Напишите комментарий..."
        rows="4"
        class="w-full px-5 py-4 text-base text-gray-800 bg-gray-50 border border-gray-200 rounded-xl resize-none outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all placeholder-gray-400"
        @keydown.ctrl.enter="submitNew"
      />
      <div class="flex items-center justify-between mt-3">
        <p v-if="newError" class="text-sm text-red-500">{{ newError }}</p>
        <span v-else class="text-sm text-gray-400">Ctrl+Enter для отправки</span>
        <button
          @click="submitNew"
          :disabled="!newText.trim() || newSubmitting"
          class="px-6 py-2.5 text-base font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {{ newSubmitting ? 'Отправка...' : 'Отправить' }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-10">
      <div class="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <p v-else-if="!loading && comments.length === 0" class="text-base text-gray-400 py-4">
      Пока нет комментариев. Будьте первым!
    </p>

    <!-- Comment threads -->
    <div v-else class="space-y-8">
      <div v-for="c in paginatedTopLevel" :key="c.commentId">

        <!-- Top-level comment -->
        <div class="flex gap-4">
          <RouterLink :to="`/profile/${c.author?.userId}`" class="flex-shrink-0">
            <img v-if="c.author?.avatar" :src="c.author.avatar" :alt="c.author.username"
                 class="w-11 h-11 rounded-full object-cover" />
            <div v-else class="w-11 h-11 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-base font-bold">
              {{ c.author?.username?.charAt(0)?.toUpperCase() ?? '?' }}
            </div>
          </RouterLink>

          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-3 flex-wrap mb-1">
              <RouterLink :to="`/profile/${c.author?.userId}`"
                          class="text-base font-semibold text-gray-900 hover:text-blue-600 transition-colors">
                {{ c.author?.username }}
              </RouterLink>
              <span v-if="c.createdAt" class="text-sm text-gray-400">{{ formatDate(c.createdAt) }}</span>
            </div>
            <p class="text-base text-gray-700 leading-relaxed whitespace-pre-wrap">{{ c.comment }}</p>

            <!-- Reply button for top-level -->
            <button
              @click="startReply(c.commentId, c.author?.username ?? '')"
              class="mt-2 text-sm font-medium text-gray-400 hover:text-blue-500 transition-colors"
            >
              {{ replyingToId === c.commentId ? 'Отмена' : 'Ответить' }}
            </button>

            <!-- Reply form — shown when replying to this thread -->
            <div v-if="replyFormRoot === c.commentId" class="mt-4">
              <p class="text-sm text-gray-400 mb-2">
                Ответ для <span class="font-medium text-gray-700">{{ replyingToUsername }}</span>
              </p>
              <textarea
                v-model="replyText"
                :placeholder="`Ответить ${replyingToUsername}...`"
                rows="3"
                class="w-full px-4 py-3 text-base text-gray-800 bg-gray-50 border border-gray-200 rounded-xl resize-none outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all placeholder-gray-400"
                @keydown.ctrl.enter="submitReply"
              />
              <div class="flex items-center justify-between mt-2">
                <p v-if="replyError" class="text-sm text-red-500">{{ replyError }}</p>
                <span v-else class="text-sm text-gray-400">Ctrl+Enter</span>
                <div class="flex gap-2">
                  <button @click="cancelReply"
                          class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
                    Отмена
                  </button>
                  <button
                    @click="submitReply"
                    :disabled="!replyText.trim() || replySubmitting"
                    class="px-5 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {{ replySubmitting ? 'Отправка...' : 'Ответить' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Replies section -->
            <template v-if="getReplies(c.commentId).length">
              <!-- Toggle collapse -->
              <button
                @click="toggleCollapse(c.commentId)"
                class="mt-4 flex items-center gap-1.5 text-sm font-medium text-gray-400 hover:text-blue-500 transition-colors"
              >
                <svg
                  class="w-3.5 h-3.5 transition-transform duration-200"
                  :class="collapsed.has(c.commentId) ? '' : 'rotate-90'"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
                {{ collapsed.has(c.commentId)
                  ? `Показать ответы (${getReplies(c.commentId).length})`
                  : `Свернуть ответы (${getReplies(c.commentId).length})` }}
              </button>

              <!-- Replies list -->
              <div v-if="!collapsed.has(c.commentId)" class="mt-4 space-y-5 pl-4 border-l-2 border-gray-100">
                <div v-for="reply in getReplies(c.commentId)" :key="reply.commentId" class="flex gap-3">
                  <RouterLink :to="`/profile/${reply.author?.userId}`" class="flex-shrink-0">
                    <img v-if="reply.author?.avatar" :src="reply.author.avatar" :alt="reply.author.username"
                         class="w-9 h-9 rounded-full object-cover" />
                    <div v-else class="w-9 h-9 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold">
                      {{ reply.author?.username?.charAt(0)?.toUpperCase() ?? '?' }}
                    </div>
                  </RouterLink>

                  <div class="flex-1 min-w-0">
                    <div class="flex items-baseline gap-3 flex-wrap mb-1">
                      <RouterLink :to="`/profile/${reply.author?.userId}`"
                                  class="text-base font-semibold text-gray-900 hover:text-blue-600 transition-colors">
                        {{ reply.author?.username }}
                      </RouterLink>
                      <span v-if="reply.createdAt" class="text-sm text-gray-400">{{ formatDate(reply.createdAt) }}</span>
                    </div>
                    <p class="text-base text-gray-700 leading-relaxed whitespace-pre-wrap">{{ reply.comment }}</p>
                    <!-- Reply to a reply -->
                    <button
                      @click="startReply(reply.commentId, reply.author?.username ?? '')"
                      class="mt-1.5 text-sm font-medium text-gray-400 hover:text-blue-500 transition-colors"
                    >
                      {{ replyingToId === reply.commentId ? 'Отмена' : 'Ответить' }}
                    </button>
                  </div>
                </div>
              </div>
            </template>

          </div>
        </div>

      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-1.5 mt-10">
      <!-- Prev -->
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="w-9 h-9 flex items-center justify-center rounded-lg text-sm text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>

      <!-- Page numbers -->
      <template v-for="p in smartPages(currentPage, totalPages)" :key="p">
        <span v-if="p === '...'" class="w-9 h-9 flex items-center justify-center text-sm text-gray-400">…</span>
        <button
          v-else
          @click="goToPage(p as number)"
          class="w-9 h-9 flex items-center justify-center rounded-lg text-sm font-medium transition-colors"
          :class="currentPage === p
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
        class="w-9 h-9 flex items-center justify-center rounded-lg text-sm text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

  </section>
</template>
