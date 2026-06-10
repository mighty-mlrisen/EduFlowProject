<script setup lang="ts">
import { ref } from 'vue'
import type { ArticleResponse } from '@/types/article.types'
import { deleteArticle } from '@/api/article.api'
import SaveButton from './SaveButton.vue'
import LikeButton from './LikeButton.vue'

const props = defineProps<{
  article: ArticleResponse
  isDraft?: boolean
  showEdit?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', id: number): void
  (e: 'save-change', saved: boolean): void
  (e: 'delete', id: number): void
}>()

const confirmingDelete = ref(false)
const deleting = ref(false)

function askDelete() { confirmingDelete.value = true }
function cancelDelete() { confirmingDelete.value = false }

async function confirmDelete() {
  deleting.value = true
  try {
    await deleteArticle(props.article.articleId)
    emit('delete', props.article.articleId)
  } catch {
    deleting.value = false
    confirmingDelete.value = false
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}

function onImgError(e: Event) {
  ;(e.target as HTMLImageElement).style.display = 'none'
}
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow flex flex-col">

    <!-- Cover image -->
    <RouterLink
      v-if="!isDraft && !showEdit"
      :to="`/article/${article.articleId}`"
      class="block flex-shrink-0"
    >
      <img
        v-if="article.image"
        :src="article.image"
        :alt="article.title"
        class="w-full h-72 object-cover"
        @error="onImgError"
      />
      <div v-else class="w-full h-40 bg-gradient-to-br from-blue-50 to-indigo-100" />
    </RouterLink>

    <div v-else class="flex-shrink-0">
      <img
        v-if="article.image"
        :src="article.image"
        :alt="article.title"
        class="w-full h-72 object-cover"
        @error="onImgError"
      />
      <div v-else class="w-full h-40 bg-gradient-to-br from-gray-50 to-gray-100" />
    </div>

    <!-- Body -->
    <div class="p-5 flex flex-col flex-1">

      <!-- Title -->
      <RouterLink
        v-if="!isDraft && !showEdit"
        :to="`/article/${article.articleId}`"
        class="block mb-2"
      >
        <h3 class="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors leading-snug line-clamp-2">
          {{ article.title || 'Без заголовка' }}
        </h3>
      </RouterLink>
      <h3 v-else class="text-lg font-semibold text-gray-900 leading-snug mb-2 line-clamp-2">
        {{ article.title || 'Без заголовка' }}
      </h3>

      <!-- Description -->
      <p v-if="article.description" class="text-sm text-gray-500 leading-relaxed line-clamp-2 mb-3">
        {{ article.description }}
      </p>

      <div class="flex-1" />

      <!-- Likes (not for drafts) -->
      <div v-if="!isDraft" class="mb-3">
        <LikeButton
          :article-id="article.articleId"
          :liked="article.statusLike"
          :count="article.likes"
        />
      </div>

      <!-- Author + date + save -->
      <div class="flex items-center justify-between pt-3 border-t border-gray-50">
        <RouterLink
          :to="`/profile/${article.users?.userId}`"
          class="flex items-center gap-2 min-w-0"
        >
          <img
            v-if="article.users?.avatar"
            :src="article.users.avatar"
            :alt="article.users.username"
            class="w-6 h-6 rounded-full object-cover flex-shrink-0"
          />
          <div
            v-else
            class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0"
          >
            {{ article.users?.username?.charAt(0)?.toUpperCase() ?? '?' }}
          </div>
          <span class="text-sm text-gray-600 hover:text-blue-600 truncate">
            {{ article.users?.username }}
          </span>
        </RouterLink>

        <div class="flex items-center gap-1 flex-shrink-0 ml-2">
          <span class="text-xs text-gray-400">{{ formatDate(article.createdAt) }}</span>
          <SaveButton
            v-if="!isDraft"
            :article-id="article.articleId"
            :saved="article.statusSave"
            @change="(s: boolean) => $emit('save-change', s)"
          />
        </div>
      </div>

      <!-- Edit / draft actions -->
      <div v-if="isDraft || showEdit" class="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
        <button
          @click="emit('edit', article.articleId)"
          class="flex-1 py-1.5 text-sm font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
        >
          Редактировать
        </button>
        <RouterLink
          v-if="!isDraft"
          :to="`/article/${article.articleId}`"
          class="px-3 py-1.5 text-sm font-medium text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Просмотр
        </RouterLink>
        <span v-if="isDraft" class="px-2.5 py-1 text-xs font-medium text-amber-600 bg-amber-50 rounded-lg">
          Черновик
        </span>
        <button
          @click="askDelete"
          class="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
          title="Удалить"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
          </svg>
        </button>
      </div>

      <!-- Confirm delete dialog -->
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="confirmingDelete"
          class="mt-3 p-3 bg-red-50 border border-red-100 rounded-xl"
        >
          <p class="text-sm text-red-700 font-medium mb-3">
            {{ isDraft ? 'Удалить черновик?' : 'Удалить статью?' }} Это действие необратимо.
          </p>
          <div class="flex gap-2">
            <button
              @click="cancelDelete"
              :disabled="deleting"
              class="flex-1 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white transition-colors disabled:opacity-50"
            >
              Отмена
            </button>
            <button
              @click="confirmDelete"
              :disabled="deleting"
              class="flex-1 py-1.5 text-sm font-medium text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50"
            >
              {{ deleting ? 'Удаление...' : 'Удалить' }}
            </button>
          </div>
        </div>
      </Transition>

    </div>
  </div>
</template>
