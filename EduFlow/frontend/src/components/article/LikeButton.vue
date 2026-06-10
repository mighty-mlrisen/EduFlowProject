<script setup lang="ts">
import { ref, watch } from 'vue'
import { toggleReaction } from '@/api/article.api'

const props = defineProps<{ articleId: number; liked: boolean; count: number; large?: boolean }>()
const emit = defineEmits<{ change: [likes: number] }>()

const isLiked = ref(props.liked)
const likeCount = ref(props.count)
const loading = ref(false)

watch(() => props.liked, (v) => { isLiked.value = v })
watch(() => props.count, (v) => { likeCount.value = v })

async function toggle(e: MouseEvent) {
  e.preventDefault()
  e.stopPropagation()
  if (loading.value) return
  loading.value = true
  try {
    const result = await toggleReaction(props.articleId, !isLiked.value)
    isLiked.value = result.statusLike
    likeCount.value = result.likes
    emit('change', result.likes)
  } catch {
    // 400 — already liked/unliked, ignore
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button
    @click="toggle"
    class="flex items-center gap-1.5 rounded-full font-medium transition-colors"
    :class="[
      large ? 'px-4 py-2 text-base' : 'px-3 py-1.5 text-sm',
      isLiked
        ? 'text-rose-500 bg-rose-50 hover:bg-rose-100'
        : 'text-gray-400 hover:text-rose-500 hover:bg-rose-50'
    ]"
  >
    <svg v-if="loading" :class="large ? 'w-6 h-6' : 'w-4 h-4'" class="animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
    <svg v-else-if="isLiked" :class="large ? 'w-6 h-6' : 'w-4 h-4'" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
    </svg>
    <svg v-else :class="large ? 'w-6 h-6' : 'w-4 h-4'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
    </svg>
    <span>{{ likeCount }}</span>
  </button>
</template>
