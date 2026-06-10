<script setup lang="ts">
import type { ArticleResponse } from '@/types/article.types'
import SaveButton from './SaveButton.vue'
import LikeButton from './LikeButton.vue'

const props = defineProps<{ article: ArticleResponse }>()
const emit = defineEmits<{ likeUpdate: [articleId: number, likes: number] }>()

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric'
  })
}
</script>

<template>
  <article class="py-8 border-b border-gray-100 last:border-b-0">

    <!-- 1. Author + date + category + save -->
    <div class="flex items-center gap-2 mb-4">
      <RouterLink
        :to="`/profile/${article.users?.userId}`"
        class="flex items-center gap-2 min-w-0"
        @click.stop
      >
        <img
          v-if="article.users?.avatar"
          :src="article.users.avatar"
          :alt="article.users.username"
          class="w-7 h-7 rounded-full object-cover flex-shrink-0"
        />
        <div
          v-else
          class="w-7 h-7 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0"
        >
          {{ article.users?.username?.charAt(0)?.toUpperCase() ?? '?' }}
        </div>
        <span class="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">
          {{ article.users?.username }}
        </span>
      </RouterLink>

      <span class="text-gray-300 flex-shrink-0">·</span>
      <span class="text-sm text-gray-400 flex-shrink-0">{{ formatDate(article.createdAt) }}</span>

      <span
        v-if="article.category"
        class="ml-auto flex-shrink-0 px-2.5 py-0.5 text-xs font-medium bg-blue-50 text-blue-600 rounded-full"
      >
        {{ article.category.name }}
      </span>

      <SaveButton :article-id="article.articleId" :saved="article.statusSave" />
    </div>

    <!-- 2. Title -->
    <RouterLink :to="`/article/${article.articleId}`" class="block group mb-4">
      <h2 class="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors leading-snug line-clamp-2">
        {{ article.title }}
      </h2>
    </RouterLink>

    <!-- 3. Cover image (full width) -->
    <RouterLink
      v-if="article.image"
      :to="`/article/${article.articleId}`"
      class="block mb-4"
    >
      <img
        :src="article.image"
        :alt="article.title"
        class="w-full h-auto rounded-xl"
      />
    </RouterLink>

    <!-- 4. Description -->
    <RouterLink
      v-if="article.description"
      :to="`/article/${article.articleId}`"
      class="block mb-4"
    >
      <p class="text-base text-gray-500 leading-relaxed line-clamp-3">
        {{ article.description }}
      </p>
    </RouterLink>

    <!-- 5. Likes -->
    <div class="flex items-center">
      <LikeButton
        :article-id="props.article.articleId"
        :liked="props.article.statusLike"
        :count="props.article.likes"
        @change="(likes) => emit('likeUpdate', props.article.articleId, likes)"
      />
    </div>

  </article>
</template>
