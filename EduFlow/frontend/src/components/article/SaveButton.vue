<script setup lang="ts">
import { ref, watch } from 'vue'
import { toggleSaveArticle } from '@/api/user.api'

const props = defineProps<{ articleId: number; saved: boolean; large?: boolean }>()
const emit = defineEmits<{ (e: 'change', saved: boolean): void }>()

const isSaved = ref(props.saved)
const loading = ref(false)

watch(() => props.saved, (v) => { isSaved.value = v })

async function toggle(e: MouseEvent) {
  e.preventDefault()
  e.stopPropagation()
  if (loading.value) return
  loading.value = true
  try {
    const result = await toggleSaveArticle(props.articleId, !isSaved.value)
    isSaved.value = result.statusSave
    emit('change', result.statusSave)
  } catch {
    // silently ignore
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button
    @click="toggle"
    class="flex items-center justify-center rounded-full transition-colors flex-shrink-0"
    :class="[
      large ? 'w-12 h-12' : 'w-8 h-8',
      isSaved ? 'text-blue-600 hover:bg-blue-50' : 'text-gray-400 hover:text-blue-500 hover:bg-gray-100'
    ]"
    :title="isSaved ? 'Убрать из избранного' : 'Добавить в избранное'"
  >
    <svg v-if="loading" :class="large ? 'w-7 h-7' : 'w-4 h-4'" class="animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
    <svg v-else-if="isSaved" :class="large ? 'w-7 h-7' : 'w-4 h-4'" viewBox="0 0 24 24" fill="currentColor">
      <path d="M5 4a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 20V4z"/>
    </svg>
    <svg v-else :class="large ? 'w-7 h-7' : 'w-4 h-4'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M5 4a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 20V4z"/>
    </svg>
  </button>
</template>
